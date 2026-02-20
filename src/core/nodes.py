from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from src.core.state import KDDState

# Constantes de Fases
PHASE_UNDERSTANDING = "1_understanding_problem"
PHASE_PROFILING = "2_data_profiling"
PHASE_PREPARATION = "3_data_preparation"
PHASE_EDA = "4_eda"
PHASE_MODELING = "5_modeling"
PHASE_EVALUATION = "6_evaluation"
PHASE_SYNTHESIS = "7_synthesis"
PHASE_DASHBOARD = "9_dashboard"


def router_node(state: KDDState) -> Dict[str, Any]:
    """
    Nodo inicial de enrutamiento mental.
    Como es paso simple de routing puro, devolvemos el ID de ruta de inicio para no saltar error de LangGraph `InvalidUpdateError`
    O devolvemos simplemente la current_phase de passthrough
    """
    return {"current_phase": state.get("current_phase")}

def goal_definition_node(state: KDDState) -> Dict[str, Any]:
    """
    Nodo responsabe de la Fase 1. Solicita y procesa la comprensión del problema.
    """
    messages = state.get("messages", [])
    current_phase = state.get("current_phase", PHASE_UNDERSTANDING)
    
    # Comportamiento mockeado de "LLM" estructurado para el test inicial
    response_text = "¿Cuál es el objetivo de tu análisis? (Ej: explorar patrones, hacer predicción)"
    
    return {
        "messages": [AIMessage(content=response_text)],
        "current_phase": PHASE_UNDERSTANDING
    }

def fallback_responder_node(state: KDDState) -> Dict[str, Any]:
    """
    Nodo general transitorio cuando no estemos en entendimiento de objetivo.
    (Posteriormente alojará al LLM principal)
    """
    return {
        "messages": [AIMessage(content="Estoy procesando tu solicitud en la fase actual.")]
    }
