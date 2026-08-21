import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class StreamlitPresentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "streamlit_app.py").read_text(encoding="utf-8")

    def test_upload_is_the_primary_workflow(self):
        for marker in ("st.file_uploader", "上传实验指导书", "解析依据", "预习报告", "正式报告"):
            self.assertIn(marker, self.source)

    def test_four_precision_pillars_and_search_exist(self):
        self.assertIn('class="precision-desktop"', self.source)
        self.assertEqual(self.source.count('class="precision-pillar"'), 4)
        self.assertIn('class="workflow-console"', self.source)
        self.assertIn("grid-template-columns: 1.08fr .92fr", self.source)
        self.assertIn("指导书进来", self.source)
        self.assertIn("linear-gradient", self.source)
        self.assertIn("搜索实验名称", self.source)
        self.assertIn("生成标准报告", self.source)
        self.assertIn("accept_new_options=True", self.source)

    def test_personal_identity_fields_are_removed(self):
        for field in ('st.text_input("姓名"', 'st.text_input("学号"', 'st.text_input("班级"'):
            self.assertNotIn(field, self.source)
        self.assertIn("不要求姓名、学号或班级", self.source)

    def test_examples_are_clearly_secondary(self):
        self.assertIn("查看两个已验证示例", self.source)
        self.assertIn("示例只用于展示质量标准", self.source)

    def test_formal_report_has_a_readiness_check(self):
        self.assertIn("提交前完整性检查", self.source)
        self.assertIn("正式报告就绪度", self.source)
        self.assertIn("不会被自动补写", self.source)

    def test_project_progress_can_be_saved_and_restored(self):
        self.assertIn("保存项目文件，稍后继续", self.source)
        self.assertIn("恢复 ChemReport 项目", self.source)
        self.assertIn("load_project_package", self.source)

    def test_structured_raw_data_can_be_edited_and_imported(self):
        self.assertIn("结构化原始数据", self.source)
        self.assertIn("st.data_editor", self.source)
        self.assertIn('type=["csv", "xlsx"]', self.source)
        self.assertIn("下载 CSV 模板", self.source)

    def test_mobile_dark_and_reduced_motion_styles_exist(self):
        self.assertIn("@media (max-width: 767px)", self.source)
        self.assertIn("@media (prefers-color-scheme: dark)", self.source)
        self.assertIn("@media (prefers-reduced-motion: reduce)", self.source)

    def test_no_visible_long_dash_literals(self):
        source_without_sanitizer = self.source.replace('"\\u2014"', "").replace('"\\u2013"', "")
        self.assertNotIn("\u2014", source_without_sanitizer)
        self.assertNotIn("\u2013", source_without_sanitizer)


if __name__ == "__main__":
    unittest.main()
