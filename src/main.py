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
    
    # Reconstruir estado como dict para pasar a proceso KDDGraph (solo pasamos el delta de cambio)
    kdd_state = {
        "current_phase": PHASE_PROFILING,
        "dataset_context": {
            "current_filename": f"{session_id}_{file.filename}",
            "status": "ready_for_profiling"
        }
    }
    
    # Disparamos el workflow conversacional con esta nueva realidad sin input de usuario
    # El router captará que está en PHASE_PROFILING y derivará al data_profiling_node.
    nuevo_estado = await process_user_input(session_id, kdd_state, user_text="")
    
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

@app.get("/sessions")
async def get_all_sessions_info():
    """Obtiene la lista de todas las sesiones históricas persistidas en LangGraph"""
    from src.core.graph import get_all_sessions
    try:
        sessions = await get_all_sessions()
        return {"sessions": sessions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/session/{session_id}")
async def get_session_info(session_id: str):
    """Obtiene el historial actual de una sesión KDD consultando a LangGraph directmente."""
    from src.core.graph import get_current_kdd_state
    state_snapshot = await get_current_kdd_state(session_id)
    session = session_manager.get_session(session_id)
    
    # Auto-rehidratación: Si FastAPI se reinició, session no existirá en memoria, pero si LangGraph lo tiene, lo reconstruimos
    if state_snapshot and state_snapshot.values and not session:
        session = session_manager.create_session() # Esto crea una con id nuevo
        # Hack in-memory para forzar el id viejo
        del session_manager._sessions[session.session_id]
        session.session_id = session_id
        session_manager._sessions[session_id] = session
        
    if not session and not state_snapshot:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    
    if state_snapshot and state_snapshot.values:
        messages = state_snapshot.values.get("messages", [])
        current_phase = state_snapshot.values.get("current_phase", session.current_phase)
        artifacts = state_snapshot.values.get("artifacts", session.artifacts)
        dataset_context = state_snapshot.values.get("dataset_context", session.dataset_context)
        user_goal = state_snapshot.values.get("user_goal", None)
    else:
        messages = session.chat_history
        current_phase = session.current_phase
        artifacts = session.artifacts
        dataset_context = session.dataset_context
        user_goal = None
        
    history = []
    agent_trace = []
    for m in messages:
         msg_type = "AI" if m.type == "ai" else "User" if m.type == "human" else m.type
         history.append({"type": msg_type, "content": str(m.content) if m.content else ""})
         
         # Traza the invocaciones ReAct / ToolCall
         if getattr(m, "tool_calls", None):
             for tc in m.tool_calls:
                 agent_trace.append({"event": "tool_call", "tool": tc['name'], "args": tc['args']})
         if m.type == "tool":
             # Mostrar truncado si es inmenso
             res_str = str(m.content)
             agent_trace.append({"event": "tool_result", "tool": getattr(m, "name", "unknown"), "result": res_str[:300] + "..." if len(res_str) > 300 else res_str})

    return {
        "session_id": session.session_id,
        "current_phase": current_phase,
        "chat_history": history,
        "agent_trace": agent_trace,
        "artifacts": artifacts,
        "dataset_context": dataset_context,
        "user_goal": user_goal
    }

class PhaseUpdateRequest(BaseModel):
    phase: str

@app.post("/session/{session_id}/phase")
async def update_session_phase(session_id: str, request: PhaseUpdateRequest):
    """Fuerza un cambio de fase en el sistema KDD (para retrocesos manuales por parte del usuario)."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    
    from src.core.graph import DB_URI, workflow, AsyncSqliteSaver
    from langchain_core.messages import SystemMessage
    
    config = {"configurable": {"thread_id": session_id}}
    async with AsyncSqliteSaver.from_conn_string(DB_URI) as memory:
        app_graph = workflow.compile(checkpointer=memory)
        # Forzar actualizacion de estado directamente en langgraph
        await app_graph.aupdate_state(config, {
            "current_phase": request.phase, 
            "messages": [SystemMessage(content=f"[SISTEMA] El analista ha movido forzosamente el pipeline a la fase: {request.phase}")]
        })
        
    session.current_phase = request.phase
    return {"status": "success", "new_phase": request.phase}

class ChatMessageRequest(BaseModel):
    user_text: str

@app.post("/session/{session_id}/message")
async def send_session_message(session_id: str, request: ChatMessageRequest):
    """
    Recibe un mensaje del usuario, lo procesa por el flujo actual del grafo y 
    devuelve la respuesta del sistema.
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
        
    from src.core.graph import process_user_input
    
    kdd_state = {} # Solo pasamos el delta if empty
    
    # Procesar la intención con LangGraph nativo (recuperará el historial solo)
    nuevo_estado = await process_user_input(session_id, kdd_state, user_text=request.user_text)
    
    # Guardar estado devuelto
    session.current_phase = nuevo_estado.get("current_phase", session.current_phase)
    session.chat_history = nuevo_estado.get("messages", session.chat_history)
    session.dataset_context = nuevo_estado.get("dataset_context", session.dataset_context)
    if "artifacts" in nuevo_estado:
        for art in nuevo_estado["artifacts"]:
            if art not in session.artifacts:
                session.artifacts.append(art)
                
    # Recolector de nuevos Artefactos devueltos al vuelo por el LLM o Tools
    import re
    for msg in session.chat_history:
        content_str = str(msg.content)
        artifacts_found = re.findall(r'\[ARTIFACT:(/sandbox/datasets/[^\s\]]+)\]', content_str)
        for path in artifacts_found:
             ext = path.split(".")[-1].lower()
             art_type = "image" if ext in ["png", "jpg", "jpeg"] else "csv" if ext == "csv" else "file"
             if not any(a.get("path") == path for a in session.artifacts):
                 session.artifacts.append({"type": art_type, "path": path, "filename": path.split("/")[-1]})
                
    last_msg = session.chat_history[-1].content if len(session.chat_history) > 0 else "Mensaje procesado."
    
    return {
        "status": "success",
        "message": last_msg,
        "current_phase": session.current_phase
    }
