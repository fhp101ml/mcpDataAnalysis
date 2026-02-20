import pytest
from langchain_core.messages import HumanMessage, AIMessage

from src.core.graph import process_user_input, PHASE_UNDERSTANDING
from src.core.session import session_manager

@pytest.mark.asyncio
async def test_kdd_initial_routing():
    """
    Prueba que un nuevo input inicie en la fase 'understanding'
    y pase por el 'goal_agent' de LangGraph.
    """
    # 1. Crear sesión virtual (igual a como se haría desde API)
    session = session_manager.create_session()
    
    # El diccionario volcado de pydantic sirve como payload para LangGraph
    # aunque 'chat_history' se debe mapear o convertir a 'messages' de langchain
    initial_payload = {
        "messages": [], 
        "current_phase": PHASE_UNDERSTANDING,
        "dataset_context": None,
        "user_goal": None
    }
    
    # 2. Correr el grafo como si el usuario dijera "Hola"
    result_state = await process_user_input(initial_payload, "Hola, quiero analizar datos")
    
    # 3. Validar resultados
    # Debería seguir en fase comprensión, y tener devuelta la respuesta mockeada AIMessage
    assert result_state["current_phase"] == PHASE_UNDERSTANDING
    
    messages = result_state["messages"]
    assert len(messages) == 2 # 1 HumanMessage + 1 AIMessage
    
    # El último mensaje es del agente
    last_message = messages[-1]
    assert isinstance(last_message, AIMessage)
    assert "¿Cuál es el objetivo" in last_message.content

@pytest.mark.asyncio
async def test_kdd_generic_routing():
    """
    Prueba que si ya pasamos la fase de understanding (ej. EDA),
    el router dirige al agente generico (generic_agent).
    """
    payload_eda = {
        "messages": [HumanMessage(content="Hola"), AIMessage(content="Objetivo seteado")], 
        "current_phase": "4_eda",
        "dataset_context": {"cols": 4},
        "user_goal": "Prediccion"
    }
    
    result = await process_user_input(payload_eda, "Hazme un grafico")
    assert result["current_phase"] == "4_eda" # No debe mutar la fase en el responder generico base
    assert "Estoy procesando" in result["messages"][-1].content
