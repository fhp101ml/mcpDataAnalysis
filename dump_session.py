import asyncio
import json
from src.core.graph import DB_URI, get_current_kdd_state

async def main():
    session_id = "9c891791-6852-4bdc-bb6d-c507b1e23466"
    state = await get_current_kdd_state(session_id)
    if not state or not state.values:
        print("No state found")
        return
    messages = state.values.get("messages", [])
    for m in messages:
        print(f"[{m.type}]: {m.content}")
        if getattr(m, "tool_calls", None):
            print(f"  Tool Calls: {m.tool_calls}")

if __name__ == "__main__":
    asyncio.run(main())
