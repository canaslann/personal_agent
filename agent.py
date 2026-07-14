"""
Kişisel asistan - çalışma zamanı agent grafiği.

ÖNEMLİ: Bu, kullanıcının KULLANACAĞI agent (tek bir tool-calling agent).
PM/Dev/Tester ayrımı GELİŞTİRME sürecinde (bu kodu yazarken) kullanıldı,
runtime'da öyle bir ayrım YOK - kullanıcı tek bir asistanla konuşuyor.

Mimari: basit ReAct-style loop.
  user mesajı -> LLM (tool seçer) -> tool çalışır -> LLM (cevap üretir) -> son
"""
import os
from datetime import datetime, timezone, timedelta
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from tools.agent_tools import ALL_TOOLS
from memory.store import AgentMemory

_SYSTEM_PROMPT_TEMPLATE = """Sen kullanıcının kişisel asistanısın. Takvim, email ve görev
yönetimi konularında yardımcı oluyorsun. Elindeki tool'ları kullanarak gerçek
işlemler yap. Email'i ASLA doğrudan gönderme, her zaman taslak oluştur.
Bir etkinliği veya taslağı silmeden/güncellemeden önce hangisini kastettiğini
söyle, kullanıcı onaylarsa işlemi yap. Kısa, net cevap ver.

KRİTİK KURALLAR:
1. Kullanıcı sadece selamlama veya genel sohbet yapıyorsa ("merhaba", "nasılsın" vb.)
   HİÇBİR tool çağırma, sadece sohbet et.
2. Bir tool liste döndürdüğünde (email, etkinlik, görev vb.) o listeyi
   TAMAMEN ve AYNEN cevabına yaz. "Yukarıdadır", "listelenmiştir" gibi
   ifadeler KULLANMA - listeyi direkt yaz.
3. Tool'u sadece kullanıcı açıkça bir işlem istediğinde çağır.

TARİH/SAAT ÇÖZÜMLEME: Kullanıcı göreli ifadeler kullandığında
(yarın, gelecek pazartesi, 2 saat sonra vb.) bunları YYYY-MM-DD ve
HH:MM formatına çevir.
Şu anki zaman (Europe/Istanbul, UTC+3): {now_istanbul}
Bugün: {today} ({weekday})"""

DAYS_TR = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
ISTANBUL = timezone(timedelta(hours=3))


def _get_system_prompt() -> str:
    """Her çağrıda güncel tarih/saat bilgisini sisteme enjekte eder."""
    now = datetime.now(ISTANBUL)
    return _SYSTEM_PROMPT_TEMPLATE.format(
        now_istanbul=now.strftime("%Y-%m-%d %H:%M"),
        today=now.strftime("%Y-%m-%d"),
        weekday=DAYS_TR[now.weekday()],
    )


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


def build_graph(groq_api_key: str | None = None, memory: AgentMemory | None = None):
    api_key = groq_api_key or os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY bulunamadı. https://console.groq.com adresinden "
            "ücretsiz key al ve ortam değişkeni olarak ayarla."
        )

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=api_key,
        temperature=0,
    )
    llm_with_tools = llm.bind_tools(ALL_TOOLS)

    def agent_node(state: AgentState):
        messages = state["messages"]
        system_content = _get_system_prompt()

        if memory is not None and messages and isinstance(messages[-1], HumanMessage):
            recalled = memory.recall(messages[-1].content, n_results=3)
            if recalled:
                context = "\n".join(f"- {r}" for r in recalled)
                system_content += f"\n\nGeçmiş konuşmalardan ilgili bilgiler:\n{context}"

        messages = [SystemMessage(content=system_content)] + [
            m for m in messages if not isinstance(m, SystemMessage)
        ]

        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def should_continue(state: AgentState):
        last_message = state["messages"][-1]
        if getattr(last_message, "tool_calls", None):
            return "tools"
        return END

    tool_node = ToolNode(ALL_TOOLS)

    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    return graph.compile()