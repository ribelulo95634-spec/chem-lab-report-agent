"""Validate ExperimentSpec JSON files without mandatory third-party packages."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = PROJECT_ROOT / "schemas" / "experiment-spec.schema.json"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def join_path(base: str, part: object) -> str:
    return f"{base}.{part}" if base else str(part)


def resolve_ref(root_schema: dict[str, Any], ref: str) -> dict[str, Any]:
    if not ref.startswith("#/"):
        raise ValueError(f"Only local schema references are supported: {ref}")
    node: Any = root_schema
    for token in ref[2:].split("/"):
        node = node[token.replace("~1", "/").replace("~0", "~")]
    return node


def matches_type(value: Any, expected: str) -> bool:
    checks = {
        "object": lambda item: isinstance(item, dict),
        "array": lambda item: isinstance(item, list),
        "string": lambda item: isinstance(item, str),
        "number": lambda item: isinstance(item, (int, float)) and not isinstance(item, bool),
        "integer": lambda item: isinstance(item, int) and not isinstance(item, bool),
        "boolean": lambda item: isinstance(item, bool),
        "null": lambda item: item is None,
    }
    return checks[expected](value)


def validate_node(
    value: Any,
    schema: dict[str, Any],
    root_schema: dict[str, Any],
    path: str = "",
) -> list[str]:
    if "$ref" in schema:
        schema = resolve_ref(root_schema, schema["$ref"])

    errors: list[str] = []
    expected_types = schema.get("type")
    if expected_types is not None:
        if isinstance(expected_types, str):
            expected_types = [expected_types]
        if not any(matches_type(value, item) for item in expected_types):
            return [f"{path or '<root>'}: expected type {expected_types}, got {type(value).__name__}"]

    if "const" in schema and value != schema["const"]:
        errors.append(f"{path or '<root>'}: expected constant {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path or '<root>'}: {value!r} is not an allowed value")

    if isinstance(value, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in value:
                errors.append(f"{join_path(path, key)}: required property is missing")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for key in value:
                if key not in properties:
                    errors.append(f"{join_path(path, key)}: additional property is not allowed")
        for key, child_schema in properties.items():
            if key in value:
                errors.extend(validate_node(value[key], child_schema, root_schema, join_path(path, key)))

    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errors.append(f"{path or '<root>'}: requires at least {schema['minItems']} items")
        if schema.get("uniqueItems"):
            encoded = [json.dumps(item, ensure_ascii=False, sort_keys=True) for item in value]
            if len(encoded) != len(set(encoded)):
                errors.append(f"{path or '<root>'}: items must be unique")
        item_schema = schema.get("items")
        if item_schema:
            for index, item in enumerate(value):
                errors.extend(validate_node(item, item_schema, root_schema, join_path(path, index)))

    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            errors.append(f"{path or '<root>'}: string is too short")
        if "pattern" in schema and re.fullmatch(schema["pattern"], value) is None:
            errors.append(f"{path or '<root>'}: does not match pattern {schema['pattern']}")
        if schema.get("format") == "date-time":
            try:
                datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                errors.append(f"{path or '<root>'}: is not a valid date-time")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path or '<root>'}: must be >= {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path or '<root>'}: must be <= {schema['maximum']}")
    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("specs", nargs="+", type=Path)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        schema = load_json(args.schema)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Schema cannot be read: {exc}", file=sys.stderr)
        return 2

    all_errors: list[str] = []
    for spec_path in args.specs:
        try:
            payload = load_json(spec_path)
        except (OSError, json.JSONDecodeError) as exc:
            all_errors.append(f"{spec_path}: cannot read JSON: {exc}")
            continue
        errors = validate_node(payload, schema, schema)
        if errors:
            all_errors.extend(f"{spec_path}:{message}" for message in errors)
        else:
            print(f"PASS {spec_path}")

    if all_errors:
        for message in all_errors:
            print(f"FAIL {message}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
