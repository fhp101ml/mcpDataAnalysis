import shutil
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from src.core.session import session_manager
from src.core.config import config_manager

# Cargar variables de entorno del directorio src
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

app = FastAPI(
    title="KDD Conversational API",
    description="Backend para el sistema de Descubrimiento de Conocimiento en Datos",
    version="0.1.0"
)

class HealthCheckResponse(BaseModel):
    status: str
    message: str

@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Endpoint de comprobación de salud del sistema."""
    return HealthCheckResponse(status="ok", message=f"{config_manager.get.app.name} is running")

@app.post("/session/new")
async def create_new_session():
    """
    Inicializa una nueva sesión de KDD, generando un ID único.
    """
    session = session_manager.create_session()
    return {"session_id": session.session_id, "status": "created", "current_phase": session.current_phase}

@app.post("/dataset/upload")
async def upload_dataset(
    file: UploadFile = File(...), 
    session_id: str = Form(...)
):
    """
    Recibe un dataset CSV, lo guarda en el sistema de archivos temporal
    y notifica al Estado KDD de LangGraph para iniciar el Data Profiling.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Solamente se permiten archivos CSV")
        
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sesión KDD no encontrada")
        
    os.makedirs("sandbox/datasets", exist_ok=True)
    file_path = os.path.join("sandbox/datasets", f"{session_id}_{file.filename}")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Notificamos al grafo de LangGraph de que hemos cambiado de fase y tenemos archivo nuevo
    from src.core.nodes import PHASE_PROFILING
    from src.core.graph import process_user_input
    
    # Reconstruir estado como dict para pasar a proceso KDDGraph
    kdd_state = {
        "messages": session.chat_history,
        "current_phase": PHASE_PROFILING,
        "dataset_context": {
            "current_filename": f"{session_id}_{file.filename}",
            "status": "ready_for_profiling"
        }
    }
    
    # Disparamos el workflow conversacional con esta nueva realidad sin input de usuario
    # El router captará que está en PHASE_PROFILING y derivará al data_profiling_node.
    nuevo_estado = await process_user_input(kdd_state, user_text="")
    
    # Guardamos el nuevo estado de la conversación en nuestra Memory Store
    session.current_phase = nuevo_estado.get("current_phase", session.current_phase)
    # LangGraph concatena a la lista original, asignamos la nueva lista completa
    session.chat_history = nuevo_estado.get("messages", session.chat_history)
    session.dataset_context = nuevo_estado.get("dataset_context", session.dataset_context)
    if "artifacts" in nuevo_estado:
        session.artifacts.extend(nuevo_estado["artifacts"])
    
    # LangChain core messages require manual dict serialization for FastAPI JSONResponse 
    last_msg = session.chat_history[-1].content if len(session.chat_history) > 0 else "Dataset cargado y Profiling KDD disparado."
    
    return {
        "status": "success", 
        "filename": file.filename, 
        "path": file_path, 
        "message": last_msg,
        "artifacts": session.artifacts
    }

@app.get("/session/{session_id}")
async def get_session_info(session_id: str):
    """Obtiene el historial actual de una sesión KDD."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
        
    history = []
    for m in session.chat_history:
         msg_type = "AI" if m.type == "ai" else "User" if m.type == "human" else m.type
         history.append({"type": msg_type, "content": m.content})
         
    return {
        "session_id": session.session_id,
        "current_phase": session.current_phase,
        "chat_history": history,
        "artifacts": session.artifacts
    }
