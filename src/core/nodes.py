from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, SystemMessage
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
    from src.core.agent_factory import AgentFactory
    
    messages = state.get("messages", [])
    
    # Instanciamos el modelo dinámico
    llm = AgentFactory.create_llm()
    
    system_prompt = SystemMessage(content="Eres un Asistente Experto en Data Science y KDD. Estás en la Fase 1: Comprensión del Problema. Tu objetivo es preguntar al usuario qué quiere lograr con sus datos, qué decisiones desea tomar o qué tipo de análisis busca (predictivo, descriptivo, etc.). Sé proactivo, educado y conciso. No ejecutes código aún.")
    
    # Invocamos al LLM con el contexto del rol y el historial
    response = llm.invoke([system_prompt] + messages)
    
    return {
        "messages": [response],
        "current_phase": PHASE_UNDERSTANDING
    }

async def data_profiling_node(state: KDDState) -> Dict[str, Any]:
    """
    Nodo de Fase 2. Cuando se sube un CSV, este nodo se dispara. 
    Llama al SandboxMCPTool para hacer el profiling de forma asíncrona real y luego lo interpreta.
    """
    from src.api.mcp_tools import SandboxMCPTool
    from src.core.agent_factory import AgentFactory
    
    dataset_context = state.get("dataset_context", {})
    filename = dataset_context.get("current_filename")
    
    if not filename:
         return {"messages": [AIMessage(content="Error: No se encontró el nombre del archivo para perfilar.")]}
    
    # 1. Ejecución ASÍNCRONA REAL de la Tool en Docker
    tool_response = await SandboxMCPTool.run_data_profiling(filename)
    
    if tool_response.success:
        profiling_data = tool_response.data.get("profiling_json", "{}")
        # Truncamos preventivamente el JSON a ~20.000 caracteres (aprox 5000 tokens) para evitar Window Overflow
        safe_profiling_data = profiling_data[:20000] + "... [TRUNCATED]" if len(profiling_data) > 20000 else profiling_data
        
        llm = AgentFactory.create_llm()
        system_prompt = SystemMessage(
            content="Eres un Experto Data Scientist que analiza resúmenes de perfilado automático. Tu tarea es ayudar siempre al usuario con respuestas sencillas."
        )
        user_prompt = HumanMessage(
            content=f"Acabas de realizar un EDA (Análisis Exploratorio) al dataset '{filename}'.\\nUsa las siguientes estadísticas JSON y resume en 3-4 viñetas (bullet points) los hallazgos principales (calidad de datos, valores atípicos, descriptiva general).\\nJSON:\\n{safe_profiling_data}"
        )
        
        # DEBUG: Logueamos antes de invocar
        from src.core.logger import setup_logger
        debug_logger = setup_logger("ProfilingNode")
        debug_logger.info(f"Llamando a LLM. JSON length envíado: {len(safe_profiling_data)} (Original: {len(profiling_data)})")
        
        response = await llm.ainvoke([system_prompt, user_prompt])
        debug_logger.info(f"LLM Response Raw: '{response.content}'")
        
        base_name = filename.replace(".csv", "")
        artifacts_metadata = [
            {"type": "profiling_html", "path": f"/sandbox/datasets/{base_name}_profile.html"},
            {"type": "profiling_json", "path": f"/sandbox/datasets/{base_name}_profile.json"}
        ]
        
        return {
            "messages": [response],
            "current_phase": PHASE_PROFILING,
            "artifacts": artifacts_metadata
        }
    else:
        error_msg = f"Hubo un fallo generando el EDA en el Sandbox: {tool_response.error}\\nInfo técnica: {tool_response.data.get('stderr')}"
        return {
            "messages": [AIMessage(content=error_msg)],
            "current_phase": PHASE_PROFILING
        }

async def fallback_responder_node(state: KDDState) -> Dict[str, Any]:
    """
    Nodo general transitorio. (Post Fase 2)
    """
    from src.core.agent_factory import AgentFactory
    
    llm = AgentFactory.create_llm()
    system_prompt = SystemMessage(content="Eres un experto en KDD. Responde de forma útil a las dudas del usuario basándote en el historial de la conversación.")
    
    response = await llm.ainvoke([system_prompt] + state.get("messages", []))
    
    return {
        "messages": [response]
    }
