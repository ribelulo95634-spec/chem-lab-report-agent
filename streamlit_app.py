"""Public Streamlit app for guide-first chemistry report generation."""

from __future__ import annotations

import re
from pathlib import Path

import streamlit as st

from web_app_utils import (
    CATALOG,
    COMMON_EXPERIMENTS,
    analyze_guide_text,
    build_formal_report,
    build_prelab_report,
    build_standard_report_template,
    extract_uploaded_document,
    load_entry,
    markdown_to_docx_bytes,
)


ROOT = Path(__file__).resolve().parent


st.set_page_config(
    page_title="ChemReport Agent",
    page_icon="CR",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
:root {
  --ink: #170f3f;
  --muted: #6f6988;
  --accent: #4931a8;
  --accent-strong: #2e1c72;
  --accent-soft: #eeeafe;
  --line: #ded9ef;
  --paper: #f8f7fc;
  --surface: #ffffff;
  --radius: 16px;
  --focus: #6b4fe8;
}
.stApp {
  background:
    radial-gradient(circle at 12% 4%, rgb(144 119 255 / .10), transparent 27rem),
    radial-gradient(circle at 88% 18%, rgb(255 174 102 / .09), transparent 24rem),
    var(--paper);
  color: var(--ink);
}
[data-testid="stHeader"] { background: transparent; }
[data-testid="stSidebar"] { background: #edf2ef; border-right: 1px solid var(--line); }
.block-container { max-width: 1120px; padding-top: 1.3rem; padding-bottom: 4rem; }
.precision-head { max-width: 900px; margin: 0 auto; padding: 2.4rem 0 .7rem; text-align: center; }
.precision-badge {
  display: inline-flex;
  align-items: center;
  min-height: 2rem;
  padding: .35rem .8rem;
  margin-bottom: 1rem;
  color: var(--accent-strong);
  background: rgb(255 255 255 / .72);
  border: 1px solid var(--line);
  border-radius: 999px;
  font-size: .78rem;
  font-weight: 760;
  letter-spacing: .05em;
}
.precision-title { margin: 0; color: var(--ink); font-size: clamp(2.35rem, 5vw, 4.45rem); line-height: 1.04; letter-spacing: -.045em; font-weight: 800; }
.precision-title span { display: block; color: var(--accent); background: linear-gradient(92deg, #38228f 12%, #7b4dd7 55%, #d36f3f 100%); background-clip: text; -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.precision-subtitle { max-width: 650px; margin: 1rem auto 0; color: var(--muted); font-size: 1.02rem; line-height: 1.65; }
.precision-desktop { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: clamp(.9rem, 2vw, 1.5rem); min-height: 385px; margin: 2.1rem 0 .4rem; align-items: start; }
.precision-pillar { position: relative; display: flex; flex-direction: column; min-width: 0; }
.precision-pillar:nth-child(1) { padding-top: 6.6rem; }
.precision-pillar:nth-child(2) { padding-top: 4.4rem; }
.precision-pillar:nth-child(3) { padding-top: 2.2rem; }
.precision-pillar:nth-child(4) { padding-top: 0; }
.pillar-head { min-height: 9.2rem; padding: 1.05rem; background: rgb(255 255 255 / .82); border: 1px solid var(--line); border-radius: var(--radius); box-shadow: 0 14px 40px rgb(40 25 92 / .07); }
.pillar-step { color: var(--accent); font-size: .73rem; font-weight: 800; letter-spacing: .07em; }
.pillar-head strong { display: block; margin-top: 1.8rem; color: var(--ink); font-size: clamp(1.04rem, 1.55vw, 1.3rem); line-height: 1.2; }
.pillar-head span { display: block; margin-top: .45rem; color: var(--muted); font-size: .84rem; line-height: 1.48; }
.pillar-detail { position: relative; min-height: 7.6rem; padding: 1rem .55rem .35rem 1.15rem; color: var(--muted); font-size: .81rem; line-height: 1.55; }
.pillar-detail::before { content: ""; position: absolute; left: .2rem; top: 0; bottom: .15rem; width: 2px; border-radius: 2px; background: linear-gradient(to bottom, #6846d6, #d97952 60%, transparent); }
.pillar-detail b { display: block; margin-bottom: .28rem; color: var(--ink); font-size: .85rem; }
.precision-mobile { display: none; }
.search-heading { max-width: 700px; margin: 1.5rem auto .75rem; text-align: center; }
.search-heading h2 { margin: 0 0 .45rem; color: var(--ink); font-size: clamp(1.45rem, 2.5vw, 2rem); }
.search-heading p { margin: 0; color: var(--muted); line-height: 1.55; }
.privacy-line { margin: .7rem 0 1.1rem; color: var(--muted); font-size: .9rem; }
.source-band { display: grid; grid-template-columns: 1.4fr .8fr .8fr; gap: .8rem; margin: 1rem 0 1.4rem; }
.source-panel { padding: .95rem 1rem; background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius); }
.source-panel strong { display: block; color: var(--accent); font-size: .82rem; margin-bottom: .25rem; }
.source-panel span { color: var(--ink); overflow-wrap: anywhere; }
.boundary { margin: 1rem 0; padding: .9rem 1rem; background: var(--accent-soft); border-left: 3px solid var(--accent); border-radius: 0 var(--radius) var(--radius) 0; color: var(--ink); }
.quiet { color: var(--muted); font-size: .9rem; line-height: 1.6; }
.stButton > button, .stDownloadButton > button { min-height: 2.8rem; border-radius: 10px; font-weight: 700; border: 1px solid var(--accent); box-shadow: none; }
.stButton > button[kind="primary"], .stDownloadButton > button { background: var(--accent-strong); color: #f8fbf9; }
.stButton > button:active, .stDownloadButton > button:active { transform: translateY(1px); }
div[data-testid="stFileUploader"] { padding: 1rem; background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius); }
div[data-testid="stFileUploaderDropzone"] { background: #f1f5f3; border: 1px dashed #83948b; border-radius: 10px; }
div[data-testid="stTextInput"] label, div[data-testid="stTextArea"] label { color: var(--ink); font-weight: 650; }
div[data-testid="stTextInput"] input, div[data-testid="stTextArea"] textarea { background: var(--surface); color: var(--ink); border-color: #9189ad; border-radius: 10px; }
div[data-testid="stForm"] { background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius); padding: 1rem; }
div[data-testid="stExpander"] { background: var(--surface); border-color: var(--line); border-radius: var(--radius); }
div[data-testid="stAlert"] { border-radius: var(--radius); }
[data-baseweb="tab-list"] { gap: .5rem; }
[data-baseweb="tab"] { border-radius: 10px 10px 0 0; }
div[data-testid="stSelectbox"] label { color: var(--ink); font-weight: 650; }
div[data-baseweb="select"] > div { background: var(--surface); border-color: #9189ad; border-radius: 10px; min-height: 2.8rem; }
div[data-testid="stTextInput"] input:focus, div[data-testid="stTextArea"] textarea:focus { border-color: var(--focus); box-shadow: 0 0 0 2px rgb(107 79 232 / .2); }
@media (max-width: 767px) {
  .block-container { padding-left: 1rem; padding-right: 1rem; padding-top: .8rem; }
  .precision-head { padding-top: 1.35rem; }
  .precision-title { font-size: clamp(2.2rem, 11vw, 3.15rem); }
  .precision-desktop { display: none; }
  .precision-mobile { display: flex; flex-direction: column; gap: .7rem; margin: 1.7rem 0 1.1rem; }
  .precision-mobile .precision-pillar { width: 86%; padding-top: 0; }
  .precision-mobile .precision-pillar:nth-child(even) { align-self: flex-end; }
  .precision-mobile .precision-pillar:nth-child(odd) { align-self: flex-start; }
  .precision-mobile .pillar-head { min-height: 0; padding: 1rem; }
  .precision-mobile .pillar-head strong { margin-top: .75rem; }
  .precision-mobile .pillar-detail { min-height: 0; padding-bottom: .65rem; }
  .source-band { grid-template-columns: 1fr; }
}
@media (prefers-color-scheme: dark) {
  :root { --ink: #f2efff; --muted: #bdb5d5; --accent: #ae96ff; --accent-strong: #6548c9; --accent-soft: #28213e; --line: #42385d; --paper: #151222; --surface: #211c31; --focus: #b4a0ff; }
  [data-testid="stSidebar"] { background: #1b1728; }
  .precision-badge, .pillar-head { background: rgb(33 28 49 / .88); }
  div[data-testid="stFileUploaderDropzone"] { background: #28223a; border-color: #766c91; }
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
  <div class="precision-badge">CHEMREPORT AGENT</div>
  <h1 class="precision-title">从实验指导书开始<span>生成可追溯的完整报告</span></h1>
  <p class="precision-subtitle">上传导师文件，提取实验结构，生成预习报告，并用真实记录完成正式报告。</p>
</header>
<div class="precision-desktop">
  <div class="precision-pillar"><div class="pillar-head"><div class="pillar-step">01 GUIDE</div><strong>上传指导书</strong><span>读取 DOCX、文本型 PDF、Markdown 和 TXT</span></div><div class="pillar-detail"><b>保留原始依据</b>记录文件名称、提取方式与哈希，关键参数由你核对。</div></div>
  <div class="precision-pillar"><div class="pillar-head"><div class="pillar-step">02 PARSE</div><strong>提取实验结构</strong><span>识别目的、原理、步骤、安全和数据要求</span></div><div class="pillar-detail"><b>缺失不补造</b>无法确认的章节明确标记，并允许逐项修正。</div></div>
  <div class="precision-pillar"><div class="pillar-head"><div class="pillar-step">03 PRELAB</div><strong>生成预习报告</strong><span>整理用品、安全、计划步骤、空表和作图计划</span></div><div class="pillar-detail"><b>先计划再实验</b>复杂拟合只给出专业软件操作与导出清单。</div></div>
  <div class="precision-pillar"><div class="pillar-head"><div class="pillar-step">04 REPORT</div><strong>生成正式报告</strong><span>整合真实操作、现象、数据和软件产物</span></div><div class="pillar-detail"><b>可追溯输出</b>完成误差、讨论与结论，并导出 Markdown 和 Word。</div></div>
</div>
<div class="precision-mobile">
  <div class="precision-pillar"><div class="pillar-head"><div class="pillar-step">01 GUIDE</div><strong>上传指导书</strong><span>DOCX、文本型 PDF、Markdown、TXT</span></div><div class="pillar-detail"><b>保留原始依据</b>记录来源与哈希。</div></div>
  <div class="precision-pillar"><div class="pillar-head"><div class="pillar-step">02 PARSE</div><strong>提取实验结构</strong><span>目的、原理、步骤、安全与数据</span></div><div class="pillar-detail"><b>缺失不补造</b>所有缺失项明确标记。</div></div>
  <div class="precision-pillar"><div class="pillar-head"><div class="pillar-step">03 PRELAB</div><strong>生成预习报告</strong><span>用品、安全、空表与作图计划</span></div><div class="pillar-detail"><b>先计划再实验</b>专业分析交给对应软件。</div></div>
  <div class="precision-pillar"><div class="pillar-head"><div class="pillar-step">04 REPORT</div><strong>生成正式报告</strong><span>真实记录、数据与软件产物</span></div><div class="pillar-detail"><b>可追溯输出</b>导出 Markdown 和 Word。</div></div>
</div>
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


def render_report_workspace(source: dict, analysis: dict) -> None:
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
        with st.form(f"formal_report_{source['sha256']}"):
            actual_procedure = st.text_area("本次实际操作与计划偏差", height=140, placeholder="记录实际步骤、条件和与指导书不同之处")
            observations = st.text_area("真实实验现象", height=120, placeholder="只填写本次观察到的现象")
            raw_data = st.text_area("原始数据", height=170, placeholder="粘贴数据并保留样品编号、单位和有效数字")
            software_results = st.text_area("计算结果或专业软件产物", height=150, placeholder="填写计算结果，或说明 Origin 图表、参数表和拟合模型")
            error_analysis = st.text_area("误差分析", height=120, placeholder="结合本次操作、数据和仪器证据分析")
            conclusion = st.text_area("实验结论", height=100, placeholder="结论必须由本次真实数据支持")
            generated = st.form_submit_button("生成正式报告草稿", type="primary", use_container_width=True)
        report_key = f"formal_markdown_{source['sha256']}"
        if generated:
            st.session_state[report_key] = build_formal_report(
                analysis,
                source,
                actual_procedure=actual_procedure,
                observations=observations,
                raw_data=raw_data,
                software_results=software_results,
                error_analysis=error_analysis,
                conclusion=conclusion,
            )
        if report_key in st.session_state:
            report = st.session_state[report_key]
            st.warning("当前仍是待审核草稿。缺失内容会保留占位，不会被模型虚构。")
            with st.expander("正式报告预览", expanded=True):
                st.markdown(clean_visible_text(report))
            file_downloads(report, "正式实验报告草稿")


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
    st.title("ChemReport Agent")
    st.markdown("**隐私原则**")
    st.caption("不要求姓名、学号或班级。上传文件只在当前会话中临时处理，网页不主动建立个人档案。")
    st.markdown("**报告边界**")
    st.caption("不编造实验数据，不用预期现象替代真实结果，不替代教师审核和专业软件分析。")

st.markdown("## 上传导师提供的实验文件")
uploaded = st.file_uploader(
    "实验指导书或实验要求",
    type=["docx", "pdf", "md", "txt", "doc"],
    help="支持 DOCX、文本型 PDF、Markdown 和 TXT，最大 10 MB。旧版 DOC 请先另存为 DOCX 或 PDF。",
)
st.markdown('<p class="privacy-line">无需填写姓名、学号或班级。文件仅用于当前页面解析和报告生成。</p>', unsafe_allow_html=True)

if uploaded is None:
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
    '<p class="quiet">公开版采用可追溯的本地结构提取，不需要 API Key。复杂公式、图片内容和专业软件结果必须由使用者核对或补充。</p>',
    unsafe_allow_html=True,
)
