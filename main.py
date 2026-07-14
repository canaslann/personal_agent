"""
Kişisel asistanı terminalden çalıştırmak için basit CLI.

Kullanım:
    export GROQ_API_KEY="your_key_here"
    python main.py
"""
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from agent import build_graph
from memory.store import AgentMemory

def main():
    print("Kişisel Asistan başlatıldı. Çıkmak için 'exit' yaz.\n")
    memory = AgentMemory()
    app = build_graph(memory=memory)
    state = {"messages": []}

    while True:
        user_input = input("Sen: ").strip()
        if user_input.lower() in ("exit", "quit", "q"):
            break
        if not user_input:
            continue

        prev_ids = {id(m) for m in state["messages"]}
        state["messages"].append(HumanMessage(content=user_input))
        result = app.invoke(state)
        state = result

        ai_message = next(
            (m for m in reversed(state["messages"])
             if isinstance(m, AIMessage) and m.content),
            None
        )
        if ai_message:
            print(f"\nAsistan: {ai_message.content}\n")

        # Hafızaya kaydet
        ai_response = next(
            (m.content for m in reversed(state["messages"])
             if isinstance(m, AIMessage) and m.content), ""
        )
        if ai_response:
            memory.remember(
                f"Kullanıcı: {user_input}\nAsistan: {ai_response}",
                metadata={"source": "conversation"},
            )


if __name__ == "__main__":
    main()