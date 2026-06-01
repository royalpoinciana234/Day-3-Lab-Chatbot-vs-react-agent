"""
Streamlit chat UI for the Doctor-Finder lab.

Run:  streamlit run app.py

Multi-turn conversation that reuses the same ReActAgent across reruns via
st.session_state, so the agent keeps its tool observations (real doctor_id /
slot) and can book an appointment after the patient confirms. Renders the
Thought/Action/Observation trace per turn and per-session telemetry.
"""
import streamlit as st

from src.core.provider_factory import get_provider
from src.core.chatbot import run_chatbot
from src.agent.agent import ReActAgent
from src.tools import TOOLS
from src.telemetry.metrics import tracker

st.set_page_config(page_title="Chatbot vs ReAct Agent", page_icon="🩺", layout="wide")
st.title("🩺 Doctor-Finder: Chatbot vs ReAct Agent")


def render_trace(trace, expanded=False):
    if not trace:
        return
    with st.expander(f"🔎 Trace ReAct ({len(trace)} bước)", expanded=expanded):
        for i, step in enumerate(trace, 1):
            st.markdown(f"**Bước {i} — Action:** `{step['action']}`")
            if step["thought"]:
                st.caption(f"Thought: {step['thought']}")
            st.code(str(step["observation"]), language="json")


with st.sidebar:
    st.header("Cấu hình")
    mode = st.radio("Chế độ", ["agent", "chatbot"], format_func=str.capitalize)
    provider = st.selectbox("Provider", ["(theo .env)", "openai", "google", "local"])
    if st.button("🔄 Cuộc trò chuyện mới"):
        for key in ("agent", "llm", "messages", "first", "config_key"):
            st.session_state.pop(key, None)
        tracker.reset()
        st.rerun()

provider_arg = None if provider.startswith("(") else provider
config_key = f"{mode}|{provider}"

# (Re)initialise the session when first loaded or when mode/provider changes.
if st.session_state.get("config_key") != config_key:
    try:
        llm = get_provider(provider_arg)
        st.session_state.llm = llm
        st.session_state.agent = ReActAgent(llm, TOOLS)
    except ValueError as e:
        st.error(str(e))
        st.stop()
    st.session_state.messages = []
    st.session_state.first = True
    st.session_state.config_key = config_key
    tracker.reset()

# Replay conversation history.
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        render_trace(m.get("trace"))

# Handle a new turn.
if prompt := st.chat_input("Nhập triệu chứng, hoặc xác nhận đặt lịch (vd 'đồng ý')..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Đang xử lý..."):
            if mode == "chatbot":
                answer = run_chatbot(st.session_state.llm, prompt)
                trace = []
            else:
                agent = st.session_state.agent
                before = len(agent.history)
                answer = agent.run(prompt, reset=st.session_state.first)
                st.session_state.first = False
                trace = list(agent.history[before:])  # only this turn's steps
        st.markdown(answer)
        render_trace(trace, expanded=True)

    st.session_state.messages.append({"role": "assistant", "content": answer, "trace": trace})

# Per-session telemetry.
with st.sidebar:
    st.subheader("Telemetry (phiên)")
    summary = tracker.session_summary()
    st.metric("Requests", summary["requests"])
    st.metric("Total tokens", summary["total_tokens"])
    st.metric("Latency (ms)", summary["total_latency_ms"])
    st.metric("Cost (USD)", f"${summary['total_cost_usd']:.6f}")
