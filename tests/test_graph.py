import pytest
import uuid
from langchain_core.messages import HumanMessage, AIMessage

from src.core.graph import process_user_input
from src.core.nodes import PHASE_PROFILING, PHASE_UNDERSTANDING, PHASE_EDA
from src.core.session import session_manager

@pytest.mark.asyncio
async def test_kdd_initial_routing():
    """
    Prueba que el estado inicial pase por la validación de Profiling.
    """
    session = session_manager.create_session()
    
    initial_payload = {
        "current_phase": PHASE_PROFILING,
        "dataset_context": {"current_filename": ""} # Falta de proposito para forzar error en el mock
    }
    
    # 2. Correr el grafo
    result_state = await process_user_input(session.session_id, initial_payload, "")
    
    assert result_state["current_phase"] == PHASE_PROFILING
    assert "Error" in result_state["messages"][-1].content

@pytest.mark.asyncio
async def test_kdd_understanding_routing():
    """
    Prueba que la fase 2 invoca al Analista Proactivo (goal_agent) y devuelve mensaje de sugerencia.
    """
    session_id = str(uuid.uuid4())
    payload = {
        "current_phase": PHASE_UNDERSTANDING,
        "dataset_context": {"current_filename": "test.csv"}
    }
    
    result = await process_user_input(session_id, payload, "¿Qué me recomiendas hacer?")
    
    assert result["current_phase"] == PHASE_UNDERSTANDING
    assert len(result["messages"]) > 0
    assert isinstance(result["messages"][-1], AIMessage)

@pytest.mark.asyncio
async def test_kdd_generic_routing():
    """
    Prueba que si ya pasamos la fase de understanding (ej. EDA),
    el router dirige al agente generico (eda_agent u otro).
    """
    session_id = str(uuid.uuid4())
    payload_eda = {
        "current_phase": "3_eda_and_planning",
        "dataset_context": {"current_filename": "test.csv"}
    }
    
    result = await process_user_input(session_id, payload_eda, "Hazme un grafico")
    assert result["current_phase"] == "3_eda_and_planning" 
    # El EDA agent intentará usar la tool de Pandas
    assert hasattr(result["messages"][-1], "tool_calls") or "grafico" in result["messages"][-1].content.lower()
