import asyncio
import httpx
from src.core.session import SessionManager
import os

async def e2e_test():
    # 0. Crear un CSV válido para testear
    import os
    os.makedirs("sandbox/datasets", exist_ok=True)
    file_path = "sandbox/datasets/test.csv"
    with open(file_path, "w") as f:
        f.write("id,name,age,salary\n1,Juan,28,40000\n2,Ana,34,55000\n3,Luis,45,80000\n4,Marta,,45000\n5,Pedro,30,42000\n")
    
    # 1. Crear sesión vía API REST (para que el bucle de FastAPI de Uvicorn la registre)
    async with httpx.AsyncClient() as client:
        print("[*] Levantando nueva sesión KDD...")
        resp_sesion = await client.post("http://localhost:8000/session/new", timeout=10.0)
        session_id = resp_sesion.json()["session_id"]
        print(f"[*] Sesión {session_id} inicializada en el Uvicorn Worker.")
    
    # 2. Hacer el POST contra FastAPI local
    async with httpx.AsyncClient() as client:
        file_path = "sandbox/datasets/test.csv"
        with open(file_path, "rb") as f:
            files = {'file': ('test.csv', f, 'text/csv')}
            data = {'session_id': session_id}
            
            print("[*] Enviando el CSV a FastApi para detonar el Grafo (Profiling Fase 2)...")
            # Apuntamos a la API local que está corriendo en background
            response = await client.post("http://localhost:8000/dataset/upload", files=files, data=data, timeout=300.0)
            print(f"Status Code: {response.status_code}")
            
            # Obtener el log conversacional completo
            resp_chat = await client.get(f"http://localhost:8000/session/{session_id}", timeout=10.0)
            if resp_chat.status_code == 200:
                print("\n=== HISTORIAL KDD ===")
                for msg in resp_chat.json().get("chat_history", []):
                     print(f"[{msg['type']}]: {msg['content']}")
                
                print("\n=== ARTEFACTOS GENERADOS ===")
                for art in resp_chat.json().get("artifacts", []):
                     print(f"- {art['type']}: {art['path']}")
            else:
                print(f"Response Raw: {response.json()}")

if __name__ == "__main__":
    asyncio.run(e2e_test())
