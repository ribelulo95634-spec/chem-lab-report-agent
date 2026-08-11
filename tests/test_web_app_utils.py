import io
import unittest

from docx import Document

from web_app_utils import (
    CATALOG,
    analyze_guide_text,
    build_formal_report,
    build_prelab_report,
    build_standard_report_template,
    extract_uploaded_document,
    load_entry,
    markdown_to_docx_bytes,
)


class WebAppUtilsTests(unittest.TestCase):
    def test_catalog_is_examples_not_the_general_input_limit(self):
        for key, entry in CATALOG.items():
            self.assertTrue(entry.spec_path.exists(), key)
            _, spec, report, audit = load_entry(key)
            self.assertIn("experiment_name", spec)
            self.assertIn("预习报告", report)
            self.assertIn("status", audit)

    def test_docx_upload_is_extracted_in_memory(self):
        document = Document()
        document.add_heading("酸碱滴定", 1)
        document.add_heading("实验目的", 2)
        document.add_paragraph("掌握滴定操作")
        document.add_heading("实验步骤", 2)
        document.add_paragraph("记录滴定管初读数和终读数")
        payload = io.BytesIO()
        document.save(payload)

        source = extract_uploaded_document("guide.docx", payload.getvalue())
        self.assertEqual(source["method"], "python_docx")
        self.assertIn("掌握滴定操作", source["text"])
        self.assertEqual(len(source["sha256"]), 64)

    def test_general_analysis_and_prelab_keep_missing_visible(self):
        source = extract_uploaded_document(
            "guide.md",
            "# 酸碱滴定\n\n## 实验目的\n掌握滴定\n\n## 实验步骤\n记录读数".encode("utf-8"),
        )
        analysis = analyze_guide_text(source["text"], "酸碱滴定")
        report = build_prelab_report(analysis, source)
        self.assertEqual(analysis["experiment_name"], "酸碱滴定")
        self.assertIn("掌握滴定", report)
        self.assertIn("【指导书中未识别到", report)
        self.assertNotIn("姓名", report)
        self.assertNotIn("学号", report)

    def test_formal_report_never_invents_missing_results(self):
        source = extract_uploaded_document("guide.txt", "实验目的\n观察反应\n实验步骤\n完成操作".encode("utf-8"))
        analysis = analyze_guide_text(source["text"], "示例实验")
        report = build_formal_report(
            analysis,
            source,
            actual_procedure="",
            observations="",
            raw_data="",
            software_results="",
            error_analysis="",
            conclusion="",
        )
        self.assertIn("【缺失：请填写本次真实观察", report)
        self.assertIn("【缺失：请粘贴原始数据", report)
        self.assertIn("NEEDS_HUMAN_REVIEW", report)

    def test_legacy_doc_has_actionable_error(self):
        with self.assertRaisesRegex(ValueError, "另存为 .docx"):
            extract_uploaded_document("guide.doc", b"legacy")

    def test_search_known_experiment_builds_reference_template(self):
        report, reference = build_standard_report_template("酸碱标准溶液标定")
        self.assertIsNotNone(reference)
        self.assertEqual(reference["name"], "酸碱标准溶液标定与未知酸测定")
        self.assertIn("标准实验报告模板", report)
        self.assertIn("原始数据", report)
        self.assertIn("本校实验参数", report)

    def test_search_unknown_experiment_stays_generic(self):
        report, reference = build_standard_report_template("自定义催化实验")
        self.assertIsNone(reference)
        self.assertIn("未在项目实验目录中找到匹配项", report)
        self.assertIn("不根据实验名称猜测", report)

    def test_docx_download_is_created_in_memory(self):
        payload = markdown_to_docx_bytes("# 示例实验 - 预习报告\n\n## 目的\n\n核对流程")
        self.assertGreater(len(payload), 10000)
        self.assertEqual(payload[:2], b"PK")


if __name__ == "__main__":
    unittest.main()
