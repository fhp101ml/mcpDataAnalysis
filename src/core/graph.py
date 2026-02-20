from typing import Literal

from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage

from src.core.state import KDDState
from src.core.nodes import (
    router_node, 
    goal_definition_node, 
    fallback_responder_node,
    PHASE_UNDERSTANDING
)

# Constructor del Grafo para el flujo KDD
workflow = StateGraph(KDDState)

# 1. Añadiendo los Nodos de Trabajo
workflow.add_node("router", router_node)
workflow.add_node("goal_agent", goal_definition_node)
workflow.add_node("generic_agent", fallback_responder_node)


# Lógica de enrutamiento inicial basado en la fase
def route_to_phase(state: KDDState) -> Literal["goal_agent", "generic_agent"]:
    """
    Decide a qué agente secundario (nodo) redirigir la conversación 
    en función de la fase actual guardada en el estado.
    """
    current_phase = state.get("current_phase", PHASE_UNDERSTANDING)
    if current_phase == PHASE_UNDERSTANDING:
        return "goal_agent"
    return "generic_agent"

# 2. Definiendo las Aristas y Flujo Direccional
workflow.add_edge(START, "router")
workflow.add_conditional_edges("router", route_to_phase)
workflow.add_edge("goal_agent", END)
workflow.add_edge("generic_agent", END)

# Compilación
app_graph = workflow.compile()

# Funcion asíncrona principal expuesta
async def process_user_input(session_state: dict, user_text: str) -> dict:
    """
    Toma el estado de sesión actual transformado en dict, le añade
    el nuevo input del usuario (HumanMessage) y corre el grafo.
    Retorna el estado resultante.
    """
    kdd_state_input = session_state
    
    # Si tenemos nuevo mensaje, lo pre-anexamos al estado
    if user_text:
        nuevo_msg = HumanMessage(content=user_text)
        if "messages" not in kdd_state_input or kdd_state_input["messages"] is None:
            kdd_state_input["messages"] = [nuevo_msg]
        else:
            kdd_state_input["messages"] = kdd_state_input["messages"] + [nuevo_msg]
            
    # Ejecutamos el pipeline de LangGraph de manera asíncrona
    final_state = await app_graph.ainvoke(kdd_state_input)
    
    return final_state
