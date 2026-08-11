import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class StreamlitPresentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "streamlit_app.py").read_text(encoding="utf-8")

    def test_upload_is_the_primary_workflow(self):
        for marker in ("st.file_uploader", "上传导师提供的实验文件", "解析依据", "预习报告", "正式报告"):
            self.assertIn(marker, self.source)

    def test_four_precision_pillars_and_search_exist(self):
        self.assertIn('class="precision-desktop"', self.source)
        self.assertIn('class="precision-mobile"', self.source)
        self.assertEqual(self.source.count('class="precision-pillar"'), 8)
        self.assertIn("repeat(4, minmax(0, 1fr))", self.source)
        self.assertIn("padding-top: 6.6rem", self.source)
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
