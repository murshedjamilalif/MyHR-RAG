"""18 · app.py — Streamlit chat UI for the HR policy assistant.

Run from the repo root:  streamlit run app.py
"""

import uuid

import streamlit as st

from myhr_rag import config
from myhr_rag.logging_config import configure_logging
from myhr_rag.pipeline import ask, build_hr_assistant
from myhr_rag.tracing import check_langsmith_tracing

configure_logging()
check_langsmith_tracing()

st.set_page_config(
    page_title="MyHR Policy Assistant",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded",
)

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=Fraunces:opsz,wght@9..144,600&display=swap');

html, body, [class*="css"] {
    font-family: "DM Sans", sans-serif;
}

.stApp {
    background:
        radial-gradient(1200px 500px at 10% -10%, #d8eee9 0%, transparent 55%),
        radial-gradient(900px 400px at 110% 0%, #e8e4d8 0%, transparent 50%),
        #f3f5f8;
}

#MainMenu, footer, .stAppDeployButton { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }

[data-testid="stSidebar"] {
    background: #0f2f33;
    border-right: none;
}
[data-testid="stSidebar"] * { color: #e8eef0 !important; }
[data-testid="stSidebar"] .stMarkdown p { color: #b7c5c8 !important; }
[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.12);
    margin: 1.1rem 0;
}

.brand-mark {
    font-family: Fraunces, Georgia, serif;
    font-size: 1.55rem;
    font-weight: 600;
    letter-spacing: -0.02em;
    color: #f4f7f6 !important;
    margin-bottom: 0.15rem;
}
.brand-sub {
    font-size: 0.82rem;
    line-height: 1.45;
    color: #9db0b4 !important;
}

.hero {
    background: linear-gradient(135deg, #0f2f33 0%, #16575c 58%, #1a7a72 100%);
    border-radius: 22px;
    padding: 1.65rem 1.75rem 1.45rem;
    color: #f4f7f6;
    margin-bottom: 1.25rem;
    box-shadow: 0 18px 40px rgba(15, 47, 51, 0.18);
}
.hero h1 {
    font-family: Fraunces, Georgia, serif;
    font-size: 1.85rem;
    font-weight: 600;
    margin: 0 0 0.4rem 0;
    letter-spacing: -0.03em;
}
.hero p {
    margin: 0;
    opacity: 0.88;
    font-size: 0.98rem;
    line-height: 1.5;
}

.empty-card {
    background: #fff;
    border: 1px solid #e4e8ee;
    border-radius: 16px;
    padding: 1.15rem 1.2rem 0.85rem;
    margin-bottom: 0.75rem;
}
.empty-card h3 {
    font-family: Fraunces, Georgia, serif;
    font-size: 1.05rem;
    margin: 0 0 0.35rem 0;
    color: #1c2430;
}
.empty-card p {
    margin: 0 0 0.85rem 0;
    color: #5a6673;
    font-size: 0.9rem;
}

.chip-label {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #7a8794;
    margin-bottom: 0.35rem;
}

[data-testid="stChatMessage"] {
    background: transparent;
}
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p {
    line-height: 1.55;
}

.stChatFloatingInputContainer {
    background: transparent;
}
</style>
"""

st.markdown(_CSS, unsafe_allow_html=True)

EXAMPLES = [
    "How many paid annual leave days do I get?",
    "What is the notice period during probation?",
    "Can I work from home every day?",
    "How many weeks of maternity leave am I entitled to?",
]


@st.cache_resource(show_spinner="Warming up the policy assistant…")
def get_agent():
    return build_hr_assistant()


def _tracing_on() -> bool:
    return config.LANGSMITH_TRACING.lower() == "true" and bool(config.LANGSMITH_API_KEY)


def _new_thread() -> None:
    st.session_state.thread_id = str(uuid.uuid4())
    st.session_state.messages = []
    st.session_state.pop("pending_question", None)


agent = get_agent()

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.markdown('<div class="brand-mark">MyHR</div>', unsafe_allow_html=True)
    st.markdown(
        '<p class="brand-sub">Answers come from indexed HR policies — '
        "not from guesswork. Citations name the source file.</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    if st.button("New conversation", use_container_width=True, type="primary"):
        _new_thread()
        st.rerun()

    st.caption("Topics this assistant covers")
    for topic in (
        "Leave & holidays",
        "Work from home",
        "Probation & notice",
        "Maternity / paternity",
        "Reimbursement & travel",
        "Code of conduct & exit",
    ):
        st.markdown(f"- {topic}")

    st.divider()
    st.caption("Status")
    st.markdown("**Retrieval** · Qdrant hybrid + Jina rerank")
    st.markdown(f"**Model** · `{config.LLM_MODEL_NAME}`")
    if _tracing_on():
        st.markdown(f"**LangSmith** · on (`{config.LANGSMITH_PROJECT}`)")
    else:
        st.markdown("**LangSmith** · off")

st.markdown(
    """
    <div class="hero">
      <h1>Policy assistant</h1>
      <p>Ask about leave, notice, WFH, and the rest of the handbook.
      I’ll search the corpus, keep the top passages, and answer from those only.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

for message in st.session_state.messages:
    avatar = "🤖" if message["role"] == "assistant" else "👤"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

if not st.session_state.messages and not st.session_state.get("pending_question"):
    st.markdown(
        """
        <div class="empty-card">
          <h3>Try a question</h3>
          <p>Pick a starter, or type your own below. Follow-ups stay in this thread.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    cols = st.columns(2)
    for i, example in enumerate(EXAMPLES):
        with cols[i % 2]:
            if st.button(example, key=f"ex_{i}", use_container_width=True):
                st.session_state.pending_question = example
                st.rerun()

typed = st.chat_input("Ask about HR policy…")
question = st.session_state.pop("pending_question", None) or typed

if question:
    with st.chat_message("user", avatar="👤"):
        st.markdown(question)

    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Looking up policy…"):
            answer = ask(agent, question, thread_id=st.session_state.thread_id)
        st.markdown(answer)

    st.session_state.messages.append({"role": "user", "content": question})
    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.rerun()
