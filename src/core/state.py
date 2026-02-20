from typing import Annotated, TypedDict, List, Dict, Any
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class KDDState(TypedDict):
    """
    Estado global del proceso KDD gestionado por LangGraph.
    
    Atributos:
    - messages: El historial de la conversación (usuario/asistente/tools).
    - current_phase: Fase actual del KDD.
    - dataset_context: Información estructural del dataset (columnas, tipos).
    - user_goal: El objetivo general (ej: exploración, predicción, agrupamiento).
    - artifacts: Lista de diccionarios con metadatos de archivos guardados (paths).
    """
    messages: Annotated[list[BaseMessage], add_messages]
    current_phase: str
    dataset_context: Dict[str, Any] | None
    user_goal: str | None
    artifacts: List[Dict[str, str]] | None
