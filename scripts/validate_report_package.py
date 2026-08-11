"""Validate report-first schemas and cross-file provenance constraints."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from validate_experiment_spec import load_json, validate_node


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = PROJECT_ROOT / "schemas"
REQUIRED_SECTIONS = {
    "preview", "materials_and_conditions", "design", "preflight", "procedure",
    "observations_and_raw_data", "preprocessing", "results", "quality_assessment",
    "error_analysis", "discussion", "conclusion", "cleanup_and_archive",
}
ALLOWED_ARTIFACT_EXTENSIONS = {".csv", ".xlsx", ".json", ".png", ".jpg", ".jpeg", ".svg", ".pdf", ".opju"}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def issue(code: str, severity: str, message: str, path: str = "") -> dict[str, str]:
    return {"code": code, "severity": severity, "message": message, "path": path}


def duplicates(values: list[str]) -> set[str]:
    seen: set[str] = set()
    repeated: set[str] = set()
    for value in values:
        if value in seen:
            repeated.add(value)
        seen.add(value)
    return repeated


def validate_structure(payload: Any, schema_name: str, label: str) -> list[dict[str, str]]:
    schema = load_json(SCHEMA_DIR / schema_name)
    return [issue("schema_error", "blocking", error, label) for error in validate_node(payload, schema, schema)]


def validate_package(
    spec: dict[str, Any],
    run: dict[str, Any],
    artifacts: list[dict[str, Any]],
    base_dir: Path,
) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    issues.extend(validate_structure(spec, "experiment-spec-v0.2.schema.json", "spec"))
    issues.extend(validate_structure(run, "experiment-run.schema.json", "run"))
    for index, artifact in enumerate(artifacts):
        issues.extend(validate_structure(artifact, "analysis-artifact.schema.json", f"artifacts[{index}]"))
    if any(item["severity"] == "blocking" for item in issues):
        return summarize(issues)

    source_ids = [item["source_id"] for item in spec["sources"]]
    data_field_ids = [item["field_id"] for item in spec["data_fields"]]
    step_ids = [item["step_id"] for item in spec["planned_steps"]]
    analysis_ids = [item["analysis_id"] for item in spec["analysis_plan"]]

    for label, values in (("source_id", source_ids), ("data_field_id", data_field_ids), ("step_id", step_ids), ("analysis_id", analysis_ids)):
        for value in sorted(duplicates(values)):
            issues.append(issue("duplicate_id", "blocking", f"重复的 {label}: {value}", f"spec.{label}"))

    source_set = set(source_ids)
    for group_name in ("objectives", "principles", "materials", "instruments", "planned_steps", "analysis_plan", "quality_rules"):
        for index, item in enumerate(spec.get(group_name, [])):
            for ref in item.get("evidence_refs", []):
                if ref not in source_set:
                    issues.append(issue("unknown_evidence", "blocking", f"来源 {ref} 不存在", f"spec.{group_name}[{index}]"))
    for ref in spec["safety"].get("evidence_refs", []):
        if ref not in source_set:
            issues.append(issue("unknown_evidence", "blocking", f"安全来源 {ref} 不存在", "spec.safety"))

    field_set = set(data_field_ids)
    derived_field_set = {
        output
        for analysis in spec["analysis_plan"]
        for output in analysis["required_outputs"]
        if not output.startswith("图表:")
    }
    for index, analysis in enumerate(spec["analysis_plan"]):
        for field_id in analysis["input_field_ids"]:
            if field_id not in field_set | derived_field_set:
                issues.append(issue("unknown_analysis_input", "blocking", f"分析输入字段 {field_id} 不存在", f"spec.analysis_plan[{index}]"))

    if set(spec["report_sections"]) != REQUIRED_SECTIONS:
        missing = sorted(REQUIRED_SECTIONS - set(spec["report_sections"]))
        extra = sorted(set(spec["report_sections"]) - REQUIRED_SECTIONS)
        issues.append(issue("report_sections", "blocking", f"报告章节不完整，缺少={missing}，额外={extra}", "spec.report_sections"))

    spec_review = spec["review"]
    if not all(spec_review[key] for key in ("guide_confirmed", "formulas_confirmed", "quality_rules_confirmed", "safety_confirmed")):
        issues.append(issue("spec_review_required", "warning", "实验定义中的指导书、公式、质量规则或安全信息尚未全部人工确认", "spec.review"))

    if run["experiment_id"] != spec["experiment_id"]:
        issues.append(issue("experiment_mismatch", "blocking", "ExperimentRun 与 ExperimentSpec 的实验 ID 不一致", "run.experiment_id"))
    for index, actual in enumerate(run["actual_steps"]):
        if actual["planned_step_id"] not in set(step_ids):
            issues.append(issue("unknown_planned_step", "blocking", f"实际步骤引用不存在的计划步骤 {actual['planned_step_id']}", f"run.actual_steps[{index}]"))
    for index, observation in enumerate(run["observations"]):
        if observation["step_id"] not in set(step_ids):
            issues.append(issue("unknown_observation_step", "blocking", f"现象引用不存在的步骤 {observation['step_id']}", f"run.observations[{index}]"))
    for index, record in enumerate(run["raw_records"]):
        unknown = sorted(set(record["values"]) - field_set)
        if unknown:
            issues.append(issue("unknown_raw_field", "blocking", f"原始记录含未定义字段 {unknown}", f"run.raw_records[{index}]"))

    artifact_by_id = {item["artifact_id"]: item for item in artifacts}
    for artifact_id in run["analysis_artifact_ids"]:
        if artifact_id not in artifact_by_id:
            issues.append(issue("missing_artifact", "blocking", f"运行记录引用的分析产物不存在: {artifact_id}", "run.analysis_artifact_ids"))
    for index, artifact in enumerate(artifacts):
        if artifact["run_id"] != run["run_id"]:
            issues.append(issue("artifact_run_mismatch", "blocking", "分析产物 run_id 与运行记录不一致", f"artifacts[{index}].run_id"))
        if artifact["analysis_id"] not in set(analysis_ids):
            issues.append(issue("artifact_analysis_mismatch", "blocking", f"分析产物引用不存在的分析任务 {artifact['analysis_id']}", f"artifacts[{index}].analysis_id"))
        if artifact["status"] == "missing":
            issues.append(issue("external_output_missing", "warning", f"分析产物 {artifact['artifact_id']} 尚未导入，仅可生成草稿", f"artifacts[{index}]"))
        for ref in artifact["source_files"] + artifact["plots"]:
            path = Path(ref["path"])
            resolved = path if path.is_absolute() else base_dir / path
            if resolved.suffix.lower() not in ALLOWED_ARTIFACT_EXTENSIONS:
                issues.append(issue("unsupported_artifact_type", "blocking", f"不支持的分析文件类型: {resolved.suffix}", str(resolved)))
            if artifact["tier"] in {"guided", "external"} and resolved.suffix.lower() == ".json":
                issues.append(issue("unsupported_external_json", "blocking", "专业软件产物请导出 CSV/XLSX/PDF/图像；JSON 只允许内部自动计算使用", str(resolved)))
            if artifact["status"] == "complete" and not resolved.exists():
                issues.append(issue("artifact_file_missing", "blocking", f"完整分析产物的文件不存在: {resolved}", str(resolved)))
            if resolved.exists() and ref.get("sha256") and file_sha256(resolved) != ref["sha256"]:
                issues.append(issue("artifact_hash_mismatch", "blocking", f"文件哈希不一致: {resolved}", str(resolved)))
        review = artifact["review"]
        if artifact["status"] == "complete" and not all(
            review[key] for key in ("input_matches_run", "units_confirmed", "model_confirmed", "plot_matches_parameters")
        ):
            issues.append(issue("artifact_review_incomplete", "warning", f"分析产物 {artifact['artifact_id']} 尚未完成一致性确认", f"artifacts[{index}].review"))

    missing_observations = [item for item in run["observations"] if item["content_status"] == "missing" or not item["text"]]
    if missing_observations:
        issues.append(issue("observations_missing", "warning", f"有 {len(missing_observations)} 条实验现象等待填写", "run.observations"))
    if run["conclusion"]["content_status"] in {"missing", "model_draft", "needs_review"}:
        issues.append(issue("conclusion_unconfirmed", "warning", "结论尚未由真实数据和人工审核确认", "run.conclusion"))
    final_review = run["final_review"]
    review_flags = ("raw_data_confirmed", "actual_steps_confirmed", "analysis_confirmed", "report_confirmed")
    if run["run_status"] == "human_confirmed" and not all(final_review[key] for key in review_flags):
        issues.append(issue("invalid_final_status", "blocking", "运行状态为 human_confirmed，但最终审核未全部完成", "run.final_review"))
    if not all(final_review[key] for key in review_flags):
        issues.append(issue("human_review_required", "warning", "正式报告仍需用户或教师人工确认", "run.final_review"))

    if any(source["source_type"] == "standard" for source in spec["sources"]) and any(
        source["source_type"] == "research_paper" for source in spec["sources"]
    ):
        issues.append(issue("mixed_source_scope", "info", "配置同时引用标准和研究论文，报告必须分别说明适用对象，不能合并质量判据", "spec.sources"))
    return summarize(issues)


def summarize(issues: list[dict[str, str]]) -> dict[str, Any]:
    counts = {severity: sum(item["severity"] == severity for item in issues) for severity in ("blocking", "warning", "info")}
    if counts["blocking"]:
        status = "BLOCKED"
    elif counts["warning"]:
        status = "NEEDS_HUMAN_REVIEW"
    else:
        status = "READY"
    return {"status": status, "counts": counts, "issues": issues}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--artifact", type=Path, action="append", default=[])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = validate_package(
        load_json(args.spec),
        load_json(args.run),
        [load_json(path) for path in args.artifact],
        PROJECT_ROOT,
    )
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 1 if result["status"] == "BLOCKED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
