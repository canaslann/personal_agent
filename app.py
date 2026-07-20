"""
Kişisel Asistan — Streamlit Glass UI
Çalıştırma: streamlit run app.py
"""
import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from agent import build_graph
from memory.store import AgentMemory
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Asistan",
    page_icon="✦",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Glass / fluid dark theme ──────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

/* Root & background */
html, body, [data-testid="stAppViewContainer"] {
    background: #07070f !important;
    font-family: 'Inter', sans-serif !important;
}

[data-testid="stAppViewContainer"]::before {
    content: '';
    position: fixed;
    inset: 0;
    background:
        radial-gradient(ellipse 60% 40% at 20% 10%, rgba(120, 80, 255, 0.18) 0%, transparent 70%),
        radial-gradient(ellipse 50% 35% at 80% 85%, rgba(80, 120, 255, 0.12) 0%, transparent 65%);
    pointer-events: none;
    z-index: 0;
}

.st-emotion-cache-hzygls,
[data-testid="stChatInputContainer"],
[data-testid="stBottomBlockContainer"] {
    background: transparent !important;
}


/* Hide default Streamlit chrome */
#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"] { display: none !important; }

/* Main container */
.main .block-container {
    max-width: 760px;
    padding: 2rem 1.5rem 7rem;
    position: relative;
    z-index: 1;
}

/* ── Typography ── */
h1 {
    font-size: 1.1rem !important;
    font-weight: 500 !important;
    color: rgba(255,255,255,0.9) !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    margin-bottom: 0.2rem !important;
}

/* ── Message bubbles ── */
.msg-user {
    display: flex;
    justify-content: flex-end;
    margin: 0.6rem 0;
}
.msg-user-inner {
    background: rgba(124, 106, 255, 0.18);
    border: 1px solid rgba(124, 106, 255, 0.35);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-radius: 18px 18px 4px 18px;
    padding: 0.65rem 1rem;
    max-width: 75%;
    color: rgba(255,255,255,0.92);
    font-size: 0.92rem;
    line-height: 1.55;
}

.msg-assistant {
    display: flex;
    justify-content: flex-start;
    margin: 0.6rem 0;
}
.msg-assistant-inner {
    background: rgba(255, 255, 255, 0.055);
    border: 1px solid rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border-radius: 18px 18px 18px 4px;
    padding: 0.75rem 1.1rem;
    max-width: 85%;
    color: rgba(255,255,255,0.88);
    font-size: 0.92rem;
    line-height: 1.65;
}

/* Avatar dot */
.avatar {
    width: 26px;
    height: 26px;
    border-radius: 50%;
    background: linear-gradient(135deg, #7c6aff, #a78bfa);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.65rem;
    color: white;
    font-weight: 600;
    margin-right: 0.5rem;
    flex-shrink: 0;
    margin-top: 2px;
}

/* ── Input area ── */

.st-emotion-cache-jchovf:focus-within {
    border-color: rgba(124, 106, 255, 0.6) !important;
}            

[data-testid="stChatInput"] {
    position: fixed !important;
    bottom: 0 !important;
    left: 50% !important;
    transform: translateX(-50%) !important;
    width: min(760px, 100vw) !important;
    padding: 1rem 1.5rem 1.4rem !important;
    background: rgba(7, 7, 15, 0.85) !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    border-top: 1px solid rgba(255,255,255,0.07) !important;
    z-index: 999 !important;
}

[data-testid="stChatInput"] textarea {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 14px !important;
    color: rgba(255,255,255,0.9) !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.92rem !important;
    caret-color: #a78bfa !important;
    padding: 0.75rem 1rem !important;
    transition: border-color 0.2s ease !important;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: rgba(124, 106, 255, 0.6) !important;
    outline: none !important;
    box-shadow: 0 0 0 2px rgba(124, 106, 255, 0.2) !important;
}
[data-testid="stChatInput"] textarea::placeholder {
    color: rgba(255,255,255,0.25) !important;
}

/* Send button */
[data-testid="stChatInput"] button {
    background: rgba(124,106,255,0.25) !important;
    border: 1px solid rgba(124,106,255,0.4) !important;
    border-radius: 10px !important;
    color: #a78bfa !important;
    transition: all 0.2s ease !important;
}
[data-testid="stChatInput"] button:hover {
    background: rgba(124,106,255,0.4) !important;
}

/* ── Divider / header line ── */
.header-line {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid rgba(255,255,255,0.07);
}
.header-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #7c6aff;
    box-shadow: 0 0 10px rgba(124,106,255,0.8);
}
.header-title {
    font-size: 0.8rem;
    font-weight: 500;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: rgba(255,255,255,0.4);
}

/* ── Spinner / thinking state ── */
.thinking {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 0.6rem 1rem;
    color: rgba(255,255,255,0.35);
    font-size: 0.82rem;
}
.dot-pulse {
    display: inline-block;
    width: 5px; height: 5px;
    border-radius: 50%;
    background: #7c6aff;
    animation: pulse 1.4s ease-in-out infinite;
}
.dot-pulse:nth-child(2) { animation-delay: 0.2s; }
.dot-pulse:nth-child(3) { animation-delay: 0.4s; }
@keyframes pulse {
    0%, 80%, 100% { opacity: 0.2; transform: scale(0.8); }
    40% { opacity: 1; transform: scale(1); }
}

/* Scrollbar */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(124,106,255,0.3); border-radius: 4px; }
</style>
""", unsafe_allow_html=True)


# ── State init ────────────────────────────────────────────────────────────────
if "agent" not in st.session_state:
    st.session_state.agent = build_graph(memory=AgentMemory())

if "graph_state" not in st.session_state:
    st.session_state.graph_state = {"messages": []}

if "display_messages" not in st.session_state:
    st.session_state.display_messages = []


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="header-line">
    <div class="header-dot"></div>
    <span class="header-title">Kişisel Asistan</span>
</div>
""", unsafe_allow_html=True)


# ── Render conversation ───────────────────────────────────────────────────────
def render_message(role: str, content: str):
    if role == "user":
        st.markdown(f"""
        <div class="msg-user">
            <div class="msg-user-inner">{content}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Escape HTML in content but preserve newlines as <br>
        safe = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
        st.markdown(f"""
        <div class="msg-assistant">
            <div class="avatar">✦</div>
            <div class="msg-assistant-inner">{safe}</div>
        </div>
        """, unsafe_allow_html=True)


for msg in st.session_state.display_messages:
    render_message(msg["role"], msg["content"])


# ── Chat input ────────────────────────────────────────────────────────────────
if prompt := st.chat_input("Bir şey sor veya görev ver…"):
    # Show user message immediately
    st.session_state.display_messages.append({"role": "user", "content": prompt})
    render_message("user", prompt)

    # Thinking indicator
    thinking_placeholder = st.empty()
    thinking_placeholder.markdown("""
    <div class="thinking">
        <span class="dot-pulse"></span>
        <span class="dot-pulse"></span>
        <span class="dot-pulse"></span>
    </div>
    """, unsafe_allow_html=True)

    # Run agent
    st.session_state.graph_state["messages"].append(HumanMessage(content=prompt))
    result = st.session_state.agent.invoke(st.session_state.graph_state)
    st.session_state.graph_state = result

    # Extract last AI response
    ai_message = next(
        (m for m in reversed(result["messages"]) if isinstance(m, AIMessage) and m.content),
        None,
    )

    thinking_placeholder.empty()

    if ai_message:
        st.session_state.display_messages.append({"role": "assistant", "content": ai_message.content})
        render_message("assistant", ai_message.content)