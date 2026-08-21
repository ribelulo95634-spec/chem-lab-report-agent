"""Public Streamlit app for guide-first chemistry report generation."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import streamlit as st

from web_app_utils import (
    CATALOG,
    COMMON_EXPERIMENTS,
    analyze_guide_text,
    build_data_template_csv,
    build_project_package,
    build_formal_report,
    build_prelab_report,
    build_standard_report_template,
    extract_uploaded_document,
    extract_structured_data_file,
    inspect_report_readiness,
    load_entry,
    load_project_package,
    markdown_to_docx_bytes,
    normalize_data_rows,
)


ROOT = Path(__file__).resolve().parent


st.set_page_config(
    page_title="ChemReport",
    page_icon="CR",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
:root {
  --ink: #14221c;
  --muted: #607068;
  --accent: #0f766e;
  --accent-strong: #0b5c56;
  --accent-soft: #e0f0eb;
  --line: #cfdbd5;
  --paper: #f4f7f5;
  --surface: #ffffff;
  --surface-raised: #f9fbfa;
  --radius: 14px;
  --focus: #0f766e;
}
.stApp {
  background:
    linear-gradient(rgb(20 34 28 / .035) 1px, transparent 1px),
    linear-gradient(90deg, rgb(20 34 28 / .035) 1px, transparent 1px),
    radial-gradient(circle at 85% 8%, rgb(15 118 110 / .12), transparent 28rem),
    var(--paper);
  background-size: 32px 32px, 32px 32px, auto, auto;
  color: var(--ink);
}
[data-testid="stHeader"] { background: transparent; }
[data-testid="stSidebar"] { background: #e8f0ec; border-right: 1px solid var(--line); }
.block-container { max-width: 1180px; padding-top: 1rem; padding-bottom: 4rem; }
.precision-head { display: grid; grid-template-columns: 1.08fr .92fr; gap: clamp(2rem, 5vw, 5rem); align-items: center; padding: 2.5rem 0 2rem; }
.precision-copy { min-width: 0; }
.precision-badge {
  display: inline-flex;
  align-items: center;
  min-height: 1.8rem;
  padding: .28rem .7rem;
  margin-bottom: 1.25rem;
  color: var(--accent-strong);
  background: var(--accent-soft);
  border: 1px solid rgb(15 118 110 / .22);
  border-radius: 999px;
  font-size: .72rem;
  font-weight: 800;
  letter-spacing: .09em;
}
.precision-title { max-width: 12ch; margin: 0; color: var(--ink); font-size: clamp(2.65rem, 5vw, 4.6rem); line-height: .98; letter-spacing: -.055em; font-weight: 820; }
.precision-title span { display: block; color: var(--accent); }
.precision-subtitle { max-width: 570px; margin: 1.25rem 0 0; color: var(--muted); font-size: 1.06rem; line-height: 1.7; }
.trust-line { display: flex; flex-wrap: wrap; gap: .55rem 1.1rem; margin-top: 1.35rem; color: var(--muted); font-size: .82rem; font-weight: 650; }
.trust-line span::before { content: "✓"; margin-right: .38rem; color: var(--accent); font-weight: 900; }
.workflow-console { position: relative; overflow: hidden; padding: 1.15rem; background: rgb(255 255 255 / .9); border: 1px solid var(--line); border-radius: 18px; box-shadow: 0 24px 65px rgb(38 65 53 / .12); }
.workflow-console::before { content: ""; position: absolute; inset: 0; background: linear-gradient(135deg, rgb(15 118 110 / .07), transparent 42%); pointer-events: none; }
.console-top { position: relative; display: flex; justify-content: space-between; align-items: center; padding: .25rem .2rem .9rem; border-bottom: 1px solid var(--line); }
.console-top strong { font-size: .9rem; letter-spacing: -.01em; }
.console-top span { color: var(--accent); font-size: .72rem; font-weight: 800; letter-spacing: .08em; }
.precision-desktop { position: relative; display: grid; gap: .55rem; padding-top: .8rem; }
.precision-pillar { display: grid; grid-template-columns: 2.25rem 1fr auto; gap: .75rem; align-items: center; padding: .72rem .78rem; background: var(--surface-raised); border: 1px solid transparent; border-radius: 10px; }
.precision-pillar:first-child { background: var(--accent-soft); border-color: rgb(15 118 110 / .18); }
.pillar-step { display: grid; place-items: center; width: 2.25rem; height: 2.25rem; color: #fff; background: var(--accent); border-radius: 8px; font-size: .72rem; font-weight: 850; }
.pillar-head strong { display: block; color: var(--ink); font-size: .92rem; }
.pillar-head span { display: block; margin-top: .15rem; color: var(--muted); font-size: .76rem; line-height: 1.4; }
.pillar-state { color: var(--accent); font-size: .72rem; font-weight: 800; }
.search-heading { max-width: 700px; margin: 1.2rem 0 .75rem; text-align: left; }
.search-heading h2 { margin: 0 0 .45rem; color: var(--ink); font-size: clamp(1.45rem, 2.5vw, 2rem); }
.search-heading p { margin: 0; color: var(--muted); line-height: 1.55; }
.privacy-line { margin: .7rem 0 1.1rem; color: var(--muted); font-size: .9rem; }
.source-band { display: grid; grid-template-columns: 1.4fr .8fr .8fr; gap: .8rem; margin: 1rem 0 1.4rem; }
.source-panel { padding: .95rem 1rem; background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius); }
.source-panel strong { display: block; color: var(--accent); font-size: .82rem; margin-bottom: .25rem; }
.source-panel span { color: var(--ink); overflow-wrap: anywhere; }
.boundary { margin: 1rem 0; padding: .9rem 1rem; background: var(--accent-soft); border-left: 3px solid var(--accent); border-radius: 0 var(--radius) var(--radius) 0; color: var(--ink); }
.quiet { color: var(--muted); font-size: .9rem; line-height: 1.6; }
.stButton > button, .stDownloadButton > button { min-height: 2.8rem; border-radius: 10px; font-weight: 750; border: 1px solid var(--accent); box-shadow: none; transition: transform .16s ease, box-shadow .16s ease, background .16s ease; }
.stButton > button[kind="primary"], .stDownloadButton > button { background: var(--accent-strong); color: #f8fbf9; }
.stButton > button:hover, .stDownloadButton > button:hover { box-shadow: 0 8px 20px rgb(15 118 110 / .14); }
.stButton > button:active, .stDownloadButton > button:active { transform: translateY(1px) scale(.99); }
div[data-testid="stFileUploader"] { padding: 1rem; background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius); box-shadow: 0 10px 34px rgb(38 65 53 / .06); }
div[data-testid="stFileUploaderDropzone"] { background: #eef5f1; border: 1px dashed #6f9484; border-radius: 10px; }
div[data-testid="stTextInput"] label, div[data-testid="stTextArea"] label { color: var(--ink); font-weight: 650; }
div[data-testid="stTextInput"] input, div[data-testid="stTextArea"] textarea { background: var(--surface); color: var(--ink); border-color: #849b91; border-radius: 10px; }
div[data-testid="stForm"] { background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius); padding: 1rem; }
div[data-testid="stExpander"] { background: var(--surface); border-color: var(--line); border-radius: var(--radius); }
div[data-testid="stAlert"] { border-radius: var(--radius); }
[data-baseweb="tab-list"] { gap: .5rem; }
[data-baseweb="tab"] { border-radius: 10px 10px 0 0; }
div[data-testid="stSelectbox"] label { color: var(--ink); font-weight: 650; }
div[data-baseweb="select"] > div { background: var(--surface); border-color: #849b91; border-radius: 10px; min-height: 2.8rem; }
div[data-testid="stTextInput"] input:focus, div[data-testid="stTextArea"] textarea:focus { border-color: var(--focus); box-shadow: 0 0 0 2px rgb(15 118 110 / .18); }
@media (max-width: 767px) {
  .block-container { padding-left: 1rem; padding-right: 1rem; padding-top: .8rem; }
  .precision-head { grid-template-columns: 1fr; gap: 1.5rem; padding-top: 1.35rem; }
  .precision-title { font-size: clamp(2.2rem, 11vw, 3.15rem); }
  .precision-subtitle { font-size: .98rem; }
  .workflow-console { padding: .85rem; }
  .precision-pillar { grid-template-columns: 2.1rem 1fr; }
  .pillar-state { display: none; }
  .source-band { grid-template-columns: 1fr; }
}
@media (prefers-color-scheme: dark) {
  :root { --ink: #eef7f2; --muted: #aabdb4; --accent: #53c5b8; --accent-strong: #167f75; --accent-soft: #173b36; --line: #345047; --paper: #101915; --surface: #18241f; --surface-raised: #1d2c26; --focus: #53c5b8; }
  [data-testid="stSidebar"] { background: #14211c; }
  .workflow-console { background: rgb(24 36 31 / .94); box-shadow: 0 24px 65px rgb(0 0 0 / .26); }
  div[data-testid="stFileUploaderDropzone"] { background: #1d2c26; border-color: #5d7b6e; }
}
@media (prefers-reduced-motion: reduce) {
  *, *:before, *:after { scroll-behavior: auto !important; transition: none !important; }
}
</style>
""",
    unsafe_allow_html=True,
)


def clean_visible_text(value: str) -> str:
    return value.replace("\u2014", "-").replace("\u2013", "-")


def render_header() -> None:
    st.markdown(
        """
<header class="precision-head">
  <div class="precision-copy">
    <div class="precision-badge">CHEMREPORT · LAB WORKSPACE</div>
    <h1 class="precision-title">指导书进来<span>实验报告出去</span></h1>
    <p class="precision-subtitle">提取实验结构，记录真实数据，生成可追溯的预习与正式报告。缺失内容保持缺失，不替你编造实验结果。</p>
    <div class="trust-line"><span>无需 API Key</span><span>数据留在当前会话</span><span>支持 Word 导出</span></div>
  </div>
  <div class="workflow-console">
    <div class="console-top"><strong>报告工作台</strong><span>TRACEABLE</span></div>
    <div class="precision-desktop">
      <div class="precision-pillar"><div class="pillar-step">01</div><div class="pillar-head"><strong>上传指导书</strong><span>DOCX、PDF、Markdown、TXT</span></div><div class="pillar-state">读取来源</div></div>
      <div class="precision-pillar"><div class="pillar-step">02</div><div class="pillar-head"><strong>核对实验结构</strong><span>目的、原理、步骤、安全要求</span></div><div class="pillar-state">人工确认</div></div>
      <div class="precision-pillar"><div class="pillar-step">03</div><div class="pillar-head"><strong>补充真实记录</strong><span>现象、原始数据、软件结果</span></div><div class="pillar-state">保留原值</div></div>
      <div class="precision-pillar"><div class="pillar-step">04</div><div class="pillar-head"><strong>导出完整报告</strong><span>Markdown、Word、项目进度</span></div><div class="pillar-state">待人工审核</div></div>
    </div>
  </div>
</header>
""",
        unsafe_allow_html=True,
    )


def render_experiment_search() -> None:
    st.markdown(
        """
<div class="search-heading">
  <h2>搜索实验名称</h2>
  <p>常见实验可生成带参考流程的标准模板，其他名称会生成不含虚构参数的通用模板。</p>
</div>
""",
        unsafe_allow_html=True,
    )
    with st.form("experiment_search_form"):
        left, right = st.columns([4.5, 1.5])
        with left:
            query = st.selectbox(
                "实验名称",
                COMMON_EXPERIMENTS,
                index=None,
                placeholder="输入或选择实验，例如：酸碱滴定",
                accept_new_options=True,
                label_visibility="collapsed",
            )
        with right:
            submitted = st.form_submit_button("生成标准报告", type="primary", use_container_width=True)
    if submitted:
        if not query or not str(query).strip():
            st.error("请输入实验名称。")
        else:
            report, reference = build_standard_report_template(str(query))
            st.session_state["searched_report"] = report
            st.session_state["searched_reference"] = reference
            st.session_state["searched_name"] = reference["name"] if reference else str(query).strip()
    if "searched_report" in st.session_state:
        report = st.session_state["searched_report"]
        reference = st.session_state.get("searched_reference")
        if reference:
            st.success(f"已匹配实验目录：{reference['name']}")
        else:
            st.warning("实验目录中没有匹配项，已生成标准报告结构。上传指导书后可补充准确内容。")
        with st.expander("标准实验报告预览", expanded=True):
            st.markdown(clean_visible_text(report))
        file_downloads(report, f"{st.session_state['searched_name']}_标准实验报告")


def file_downloads(markdown: str, base_name: str) -> None:
    safe_name = re.sub(r'[\\/:*?"<>|]+', "_", base_name).strip(" .")[:80] or "实验报告"
    left, right = st.columns(2)
    with left:
        st.download_button(
            "下载 Markdown",
            markdown.encode("utf-8"),
            file_name=f"{safe_name}.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with right:
        st.download_button(
            "下载 Word",
            markdown_to_docx_bytes(markdown),
            file_name=f"{safe_name}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )


def render_analysis_editor(analysis: dict, source_hash: str) -> dict:
    state_key = f"analysis_{source_hash}"
    if state_key not in st.session_state:
        st.session_state[state_key] = analysis
    current = st.session_state[state_key]
    with st.expander("检查并修正提取结果"):
        st.caption("自动提取只整理可访问文字。标题层级不规范或公式是图片时，请在这里修正。")
        with st.form(f"analysis_editor_{source_hash}"):
            experiment_name = st.text_input("实验名称", value=current["experiment_name"])
            labels = {
                "objectives": "实验目的",
                "principle": "实验原理",
                "materials": "仪器与试剂",
                "safety": "安全与废物",
                "procedure": "计划步骤",
                "data": "数据处理与作图",
                "questions": "思考题",
            }
            edited = {
                key: st.text_area(label, value=current["sections"].get(key, ""), height=130)
                for key, label in labels.items()
            }
            applied = st.form_submit_button("应用修订", type="primary", use_container_width=True)
        if applied:
            current = {
                **current,
                "experiment_name": experiment_name.strip() or "未命名实验",
                "sections": edited,
                "missing_sections": [key for key, value in edited.items() if not value.strip()],
            }
            st.session_state[state_key] = current
            st.success("修订已应用到本次预习报告和正式报告。")
    return current


def render_report_workspace(
    source: dict,
    analysis: dict,
    restored_formal_inputs: dict | None = None,
    restored_data_rows: list[dict] | None = None,
) -> None:
    st.markdown(
        f"""
<div class="source-band">
  <div class="source-panel"><strong>指导书</strong><span>{clean_visible_text(source['file_name'])}</span></div>
  <div class="source-panel"><strong>提取方式</strong><span>{source['method']}</span></div>
  <div class="source-panel"><strong>待补章节</strong><span>{len(analysis['missing_sections'])}</span></div>
</div>
""",
        unsafe_allow_html=True,
    )

    analysis = render_analysis_editor(analysis, source["sha256"])
    formal_inputs_key = f"formal_inputs_{source['sha256']}"
    if formal_inputs_key not in st.session_state:
        st.session_state[formal_inputs_key] = restored_formal_inputs or {
            "actual_procedure": "",
            "observations": "",
            "raw_data": "",
            "software_results": "",
            "error_analysis": "",
            "conclusion": "",
        }
    formal_inputs = st.session_state[formal_inputs_key]
    data_rows_key = f"data_rows_{source['sha256']}"
    if data_rows_key not in st.session_state:
        st.session_state[data_rows_key] = normalize_data_rows(restored_data_rows)
    data_rows = st.session_state[data_rows_key]
    data_editor_revision_key = f"data_editor_revision_{source['sha256']}"
    if data_editor_revision_key not in st.session_state:
        st.session_state[data_editor_revision_key] = 0
    preview_tab, prelab_tab, formal_tab = st.tabs(["解析依据", "预习报告", "正式报告"])

    with preview_tab:
        st.markdown("### 从文件中识别到的内容")
        if analysis["missing_sections"]:
            st.warning("部分章节未识别。请展开上方编辑区核对，不会自动补写缺失内容。")
        with st.expander("查看提取文本", expanded=True):
            st.text(clean_visible_text(source["text"][:16000]))
        st.caption(f"SHA-256: {source['sha256']}")

    with prelab_tab:
        prelab = build_prelab_report(analysis, source)
        st.markdown('<div class="boundary">预习报告可以直接生成，但关键参数仍需与原指导书逐项核对。</div>', unsafe_allow_html=True)
        with st.expander("预习报告预览", expanded=True):
            st.markdown(clean_visible_text(prelab))
        file_downloads(prelab, "实验预习报告")

    with formal_tab:
        st.markdown('<div class="boundary">指导书只能提供计划。正式报告必须补充本次真实操作、现象、原始数据和软件结果。</div>', unsafe_allow_html=True)
        st.markdown("### 结构化原始数据")
        st.caption("可直接增删行，或导入包含“数据项、单位、原始值、备注”列的 CSV/Excel。")
        import_col, action_col, template_col = st.columns([2.4, 1, 1])
        with import_col:
            data_file = st.file_uploader(
                "CSV 或 Excel 数据文件",
                type=["csv", "xlsx"],
                key=f"structured_data_upload_{source['sha256']}",
                label_visibility="collapsed",
            )
        with action_col:
            import_clicked = st.button(
                "导入并替换",
                key=f"structured_data_import_{source['sha256']}",
                use_container_width=True,
                disabled=data_file is None,
            )
        with template_col:
            st.download_button(
                "下载 CSV 模板",
                build_data_template_csv(),
                file_name="ChemReport_原始数据模板.csv",
                mime="text/csv",
                use_container_width=True,
            )
        if import_clicked and data_file is not None:
            try:
                imported = extract_structured_data_file(data_file.name, data_file.getvalue())
                data_rows = imported["rows"]
                st.session_state[data_rows_key] = data_rows
                st.session_state[data_editor_revision_key] += 1
                st.success(f"已从 {imported['file_name']} 导入 {len(data_rows)} 行数据。")
            except Exception as exc:
                st.error(clean_visible_text(str(exc)))

        editor_value = data_rows or [{"数据项": "", "单位": "", "原始值": "", "备注": ""}]
        edited_rows = st.data_editor(
            editor_value,
            num_rows="dynamic",
            hide_index=True,
            use_container_width=True,
            key=(
                f"structured_data_editor_{source['sha256']}_"
                f"{st.session_state[data_editor_revision_key]}"
            ),
            column_order=["数据项", "单位", "原始值", "备注"],
        )
        data_rows = normalize_data_rows(edited_rows)
        st.session_state[data_rows_key] = data_rows
        st.caption(f"当前已记录 {len(data_rows)} 行有效数据。数值按原样保存，不自动修改单位或有效数字。")

        with st.form(f"formal_report_{source['sha256']}"):
            actual_procedure = st.text_area("本次实际操作与计划偏差", value=formal_inputs["actual_procedure"], height=140, placeholder="记录实际步骤、条件和与指导书不同之处")
            observations = st.text_area("真实实验现象", value=formal_inputs["observations"], height=120, placeholder="只填写本次观察到的现象")
            raw_data = st.text_area("原始数据补充说明（可选）", value=formal_inputs["raw_data"], height=120, placeholder="补充仪器读数规则、数据来源或表格无法表达的信息")
            software_results = st.text_area("计算结果或专业软件产物", value=formal_inputs["software_results"], height=150, placeholder="填写计算结果，或说明 Origin 图表、参数表和拟合模型")
            error_analysis = st.text_area("误差分析", value=formal_inputs["error_analysis"], height=120, placeholder="结合本次操作、数据和仪器证据分析")
            conclusion = st.text_area("实验结论", value=formal_inputs["conclusion"], height=100, placeholder="结论必须由本次真实数据支持")
            generated = st.form_submit_button("保存输入并生成正式报告草稿", type="primary", use_container_width=True)
        report_key = f"formal_markdown_{source['sha256']}"
        if generated:
            formal_inputs = {
                "actual_procedure": actual_procedure,
                "observations": observations,
                "raw_data": raw_data,
                "software_results": software_results,
                "error_analysis": error_analysis,
                "conclusion": conclusion,
            }
            st.session_state[formal_inputs_key] = formal_inputs
            readiness = inspect_report_readiness(
                actual_procedure=actual_procedure,
                observations=observations,
                raw_data=raw_data,
                software_results=software_results,
                error_analysis=error_analysis,
                conclusion=conclusion,
                data_rows=data_rows,
            )
            st.session_state[report_key] = build_formal_report(
                analysis,
                source,
                actual_procedure=actual_procedure,
                observations=observations,
                raw_data=raw_data,
                software_results=software_results,
                error_analysis=error_analysis,
                conclusion=conclusion,
                data_rows=data_rows,
            )
            st.session_state[f"formal_readiness_{source['sha256']}"] = readiness
        if report_key in st.session_state:
            report = st.session_state[report_key]
            readiness = st.session_state[f"formal_readiness_{source['sha256']}"]
            st.markdown("### 提交前完整性检查")
            st.caption(
                f"正式报告就绪度：{readiness['completed_count']}/{readiness['total_count']} 项真实内容已补充。"
            )
            if readiness["is_ready"]:
                st.success("关键内容已补齐。导出前仍需核对原始数据、单位、有效数字和图表来源。")
            else:
                st.warning("尚缺：" + "、".join(readiness["missing"]) + "。可先导出草稿，但不应直接提交。")
            st.warning("当前仍是待审核草稿。缺失内容会保留占位，不会被自动补写。")
            with st.expander("正式报告预览", expanded=True):
                st.markdown(clean_visible_text(report))
            file_downloads(report, "正式实验报告草稿")

    project_name = re.sub(r'[\\/:*?"<>|]+', "_", analysis["experiment_name"]).strip(" .")[:60] or "实验项目"
    st.divider()
    st.markdown("### 保存当前进度")
    st.download_button(
        "保存项目文件，稍后继续",
        build_project_package(source, analysis, formal_inputs, data_rows),
        file_name=f"{project_name}_ChemReport项目.json",
        mime="application/json",
        use_container_width=True,
        help="项目文件包含指导书来源、人工修订和已保存的正式报告输入。",
    )


def render_examples() -> None:
    with st.expander("查看两个已验证示例"):
        st.caption("示例只用于展示质量标准，不限制你上传其他化学实验。")
        labels = {key: entry.label for key, entry in CATALOG.items()}
        selected = st.selectbox("示例实验", list(labels), format_func=labels.get)
        entry, spec, _, audit = load_entry(selected)
        st.markdown(f"**{clean_visible_text(spec['experiment_name'])}**")
        st.write(entry.short_description)
        st.caption(f"审查状态：{audit.get('status', 'NEEDS_HUMAN_REVIEW')}")


render_header()
render_experiment_search()
st.divider()

with st.sidebar:
    st.title("ChemReport")
    st.markdown("**隐私原则**")
    st.caption("不要求姓名、学号或班级。上传文件只在当前会话中临时处理，网页不主动建立个人档案。")
    st.markdown("**报告边界**")
    st.caption("不编造实验数据，不用预期现象替代真实结果，不替代教师审核和专业软件分析。")

st.markdown("## 开始新的报告，或继续之前的项目")
upload_tab, restore_tab = st.tabs(["上传实验指导书", "恢复 ChemReport 项目"])
with upload_tab:
    uploaded = st.file_uploader(
        "实验指导书或实验要求",
        type=["docx", "pdf", "md", "txt", "doc"],
        help="支持 DOCX、文本型 PDF、Markdown 和 TXT，最大 10 MB。旧版 DOC 请先另存为 DOCX 或 PDF。",
        key="guide_upload",
    )
with restore_tab:
    restored = st.file_uploader(
        "ChemReport 项目文件",
        type=["json"],
        help="上传此前由本工具导出的 ChemReport 项目 JSON。",
        key="project_restore",
    )
st.markdown('<p class="privacy-line">无需填写姓名、学号或班级。文件仅用于当前页面解析和报告生成。</p>', unsafe_allow_html=True)

if restored is None:
    st.session_state.pop("active_restore_marker", None)

if restored is not None:
    try:
        project_bytes = restored.getvalue()
        project = load_project_package(project_bytes)
        project_hash = project["source"]["sha256"]
        restore_marker = hashlib.sha256(project_bytes).hexdigest()
        if st.session_state.get("active_restore_marker") != restore_marker:
            st.session_state[f"analysis_{project_hash}"] = project["analysis"]
            st.session_state[f"formal_inputs_{project_hash}"] = project["formal_inputs"]
            st.session_state[f"data_rows_{project_hash}"] = project["data_rows"]
            st.session_state[f"data_editor_revision_{project_hash}"] = 0
            st.session_state["active_restore_marker"] = restore_marker
        st.success(f"已恢复项目：{project['analysis']['experiment_name']}")
        render_report_workspace(
            project["source"],
            project["analysis"],
            project["formal_inputs"],
            project["data_rows"],
        )
    except Exception as exc:
        st.error(clean_visible_text(str(exc)))
        st.caption("请选择由 ChemReport 导出的有效项目 JSON 文件。")
elif uploaded is None:
    st.info("上传文件后，页面会自动进入解析、预习报告和正式报告工作区。")
    render_examples()
else:
    try:
        source = extract_uploaded_document(uploaded.name, uploaded.getvalue())
        analysis = analyze_guide_text(source["text"], fallback_name=Path(uploaded.name).stem)
        render_report_workspace(source, analysis)
    except Exception as exc:
        st.error(clean_visible_text(str(exc)))
        st.caption("如果是扫描版 PDF，请先进行 OCR；如果是旧版 DOC，请另存为 DOCX 或 PDF。")

st.divider()
st.markdown(
    '<p class="quiet">公开版采用可追溯的本地结构提取，不需要 API Key。可下载项目 JSON 保存进度；复杂公式、图片内容和专业软件结果必须由使用者核对或补充。</p>',
    unsafe_allow_html=True,
)
