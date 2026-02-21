from typing import Literal

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import HumanMessage

from src.core.state import KDDState
from src.core.nodes import (
    router_node, 
    goal_definition_node, 
    data_profiling_node,
    eda_agent_node,
    fallback_responder_node,
    PHASE_UNDERSTANDING,
    PHASE_PROFILING,
    PHASE_EDA
)
from src.api.mcp_tools import execute_pandas_code

# Constructor del Grafo para el flujo KDD
workflow = StateGraph(KDDState)

# 1. Añadiendo los Nodos de Trabajo
workflow.add_node("router", router_node)
workflow.add_node("goal_agent", goal_definition_node)
workflow.add_node("profiling_agent", data_profiling_node)
workflow.add_node("eda_agent", eda_agent_node)
workflow.add_node("generic_agent", fallback_responder_node)

# Nodo especial para ejecución de herramientas
tools_node = ToolNode([execute_pandas_code])
workflow.add_node("tools", tools_node)

# Lógica de enrutamiento inicial basado en la fase
def route_to_phase(state: KDDState) -> Literal["goal_agent", "profiling_agent", "eda_agent", "generic_agent"]:
    """
    Decide a qué agente secundario (nodo) redirigir la conversación.
    """
    current_phase = state.get("current_phase", PHASE_PROFILING) # Ahora empieza en perfilado
    if current_phase == PHASE_PROFILING:
        return "profiling_agent"
    elif current_phase == PHASE_UNDERSTANDING:
        return "goal_agent"
    elif current_phase == PHASE_EDA:
        return "eda_agent"
    return "generic_agent"

# 2. Definiendo las Aristas y Flujo Direccional
workflow.add_edge(START, "router")
workflow.add_conditional_edges("router", route_to_phase)
workflow.add_edge("goal_agent", END)
workflow.add_edge("profiling_agent", END)

# === CICLO ReAct para el agente EDA ===
# Si eda_agent devuelve una respuesta con tool_calls, vamos a 'tools'. Si no, a END.
workflow.add_conditional_edges("eda_agent", tools_condition, {"tools": "tools", END: END})
workflow.add_edge("tools", "eda_agent") # Después de ejecutarse, el agente procesa el output.

workflow.add_edge("generic_agent", END)

from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
import os

# Configuración de URI SQLite de LangGraph
os.makedirs("sandbox", exist_ok=True)
DB_URI = "sandbox/kdd_memory.sqlite"

# Funcion asíncrona principal expuesta
async def process_user_input(session_id: str, session_state: dict, user_text: str) -> dict:
    """
    Toma el estado de sesión actual transformado en dict, pre-anexa
    el nuevo input del usuario (HumanMessage) y corre el grafo.
    Usa el Checkpointer SQLite para cargar el historial previo.
    """
    config = {"configurable": {"thread_id": session_id}}
    
    # LangGraph solo necesita el delta de cambio. No le pasamos el historial completo.
    kdd_state_input = {}
    
    # Si tenemos nuevo mensaje, lo pasamos
    if user_text:
        kdd_state_input["messages"] = [HumanMessage(content=user_text)]
        
    # Pasamos las actualizaciones de las variables de estado si existen
    if "current_phase" in session_state:
        kdd_state_input["current_phase"] = session_state["current_phase"]
    if "dataset_context" in session_state and session_state["dataset_context"]:
        kdd_state_input["dataset_context"] = session_state["dataset_context"]
            
    # Ejecutamos el pipeline de LangGraph de manera asíncrona dentro del pool DB
    async with AsyncSqliteSaver.from_conn_string(DB_URI) as memory:
        await memory.setup() # Prepara la BD si no existía (crea tablas LangGraph)
        app_graph = workflow.compile(checkpointer=memory)
        final_state = await app_graph.ainvoke(kdd_state_input, config=config)
    
    return final_state

async def get_current_kdd_state(session_id: str):
    """
    Permite a componentes externos como la vista principal consultar 
    el estado interno de un hilo/sesión.
    """
    config = {"configurable": {"thread_id": session_id}}
    async with AsyncSqliteSaver.from_conn_string(DB_URI) as memory:
        await memory.setup()
        app_graph = workflow.compile(checkpointer=memory)
        state_snapshot = await app_graph.aget_state(config)
        return state_snapshot

async def get_all_sessions():
    """Recupera la lista de todas las sesiones activas persistidas en la DB de LangGraph"""
    import aiosqlite
    sessions_info = []
    async with aiosqlite.connect(DB_URI) as db:
        async with db.execute("SELECT DISTINCT thread_id FROM checkpoints") as cursor:
            rows = await cursor.fetchall()
            for row in rows:
                session_id = row[0]
                state_snapshot = await get_current_kdd_state(session_id)
                if state_snapshot and state_snapshot.values:
                    phase = state_snapshot.values.get("current_phase", "unknown")
                    ctx = state_snapshot.values.get("dataset_context", {})
                    filename = ctx.get("current_filename", "Sin Dataset") if ctx else "Sin Dataset"
                    sessions_info.append({
                        "session_id": session_id,
                        "current_phase": phase,
                        "filename": filename
                    })
    return sessions_info
