from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage
import asyncio

async def main():
    llm = ChatOllama(model="llama3.1:latest", temperature=0, num_ctx=8192)
    # Payload pequeño
    payload = "{'test': 'data'}" * 10
    print(f"Enviando info. Len: {len(payload)}")
    resp = await llm.ainvoke([SystemMessage(content=f"Resume esto en tres palabras:\n{payload}")])
    print(f"RAW RES: '{resp.content}'")

asyncio.run(main())
