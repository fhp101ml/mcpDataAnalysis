from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, SystemMessage
from src.core.state import KDDState

# Constantes de Fases reordenadas
PHASE_PROFILING = "1_data_profiling"
PHASE_UNDERSTANDING = "2_understanding_problem"
PHASE_EDA = "3_eda_and_planning"
PHASE_PREPARATION = "4_data_preparation"
PHASE_MODELING = "5_modeling"
PHASE_EVALUATION = "6_evaluation"
PHASE_SYNTHESIS = "7_synthesis"
PHASE_DASHBOARD = "10_dashboard"


def router_node(state: KDDState) -> Dict[str, Any]:
    """
    Nodo inicial de enrutamiento mental.
    Como es paso simple de routing puro, devolvemos el ID de ruta de inicio para no saltar error de LangGraph `InvalidUpdateError`
    O devolvemos simplemente la current_phase de passthrough
    """
    return {"current_phase": state.get("current_phase")}


def goal_definition_node(state: KDDState) -> Dict[str, Any]:
    """
    Nodo responsabe de la Fase 2 (Analista Proactivo). Evalúa el perfilado automático del dataset y pregunta por el objetivo.
    También tiene acceso a una Tool para avanzar de fase cuando el objetivo analítico esté claro.
    """
    from src.core.agent_factory import AgentFactory
    from langchain_core.tools import tool
    from langchain_core.messages import ToolMessage
    import json
    
    @tool
    def set_analysis_goal(goal_description: str) -> str:
        """Llama a esta herramienta EXACTAMENTE cuando el usuario y tú hayáis acordado el objetivo analítico principal del proyecto de datos (ej: 'predecir supervivencia', 'análisis exploratorio de ventas'). Esta acción guarda el objetivo en el sistema y avanza a la Fase 3 (Ejecución de Código)."""
        return "Objetivo guardado y transición a Fase 3 iniciada."

    messages = state.get("messages", [])
    dataset_context = state.get("dataset_context", {})
    filename = dataset_context.get("current_filename", "desconocido.csv")
    
    llm = AgentFactory.create_llm().bind_tools([set_analysis_goal])
    
    system_prompt = SystemMessage(
        content="Eres el 'Analista Proactivo' de un ecosistema multi-agente KDD. Estás en la Fase 2: Definición del Problema.\n"
                f"Dataset cargado: '{filename}'. Tienes el perfilado en el historial de mensajes anterior.\n"
                "TU ROL ES ESTRICTAMENTE AYUDAR AL USUARIO A DEFINIR EL OBJETIVO EMPRESARIAL O ANALÍTICO (ej: 'predecir X', 'agrupar Y', 'exploración general').\n"
                "REGLAS CRÍTICAS QUE NO PUEDES ROMPER BAJO NINGÚN CONCEPTO:\n"
                "1. NO PUEDES ejecutar código, NI generar scripts de Python, NI pedirle al usuario que copie/pegue código en su entorno local.\n"
                "2. Si el usuario te pide un gráfico, modelos, análisis estadístico o dice que ejecutes algo, DEBES RESPONDER ALGO COMO: 'En esta fase inicial mi rol es únicamente asentar el objetivo teórico. Si tu objetivo está claro, puedo dar por terminada esta fase para que mi compañero (el Agente Programador) tome el control y ejecute el código real en la Fase 3. ¿Quieres que guarde el objetivo y avancemos?'\n"
                "3. CUANDO el usuario indique explícitamente que quiere avanzar, O si el objetivo ya ha quedado claro en la conversación, TIENES LA OBLIGACIÓN ESTRICTA E INELUDIBLE de invocar tu tool `set_analysis_goal` pasándole el resumen del objetivo. NUNCA pretendas avanzar solo respondiendo texto. Si tu respuesta dice 'vamos a la Fase 3', DEBES incluir la llamada a la tool."
    )
    
    response = llm.invoke([system_prompt] + messages)
    
    # Comprobamos si el LLM decidió llamar a la tool para transicionar
    if getattr(response, "tool_calls", None):
        tool_call = response.tool_calls[0]
        if tool_call["name"] == "set_analysis_goal":
            goal = tool_call["args"].get("goal_description", "Objetivo no especificado explícitamente")
            # Mensaje de sistema simulando la respuesta de la tool para mantener la coherencia del historial
            tool_msg = ToolMessage(
                content="El sistema ha guardado el objetivo correctamente. Has sido transferido a la Fase 3 (Análisis Exploratorio), donde ya podrás pedir gráficos y ejecutar código.", 
                tool_call_id=tool_call["id"]
            )
            return {
                "messages": [response, tool_msg],
                "user_goal": goal,
                "current_phase": PHASE_EDA # Transición automática
            }
            
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
            content=f"Acabas de realizar un EDA (Análisis Exploratorio) al dataset '{filename}'.\nUsa las siguientes estadísticas JSON y resume en 3-4 viñetas (bullet points) los hallazgos principales (calidad de datos, valores atípicos, descriptiva general).\nAl final de tu respuesta, INCLUYE ESTA PREGUNTA PARA EL USUARIO: '\\n\\n**Siguiente paso:** Para poder ayudarte con análisis visuales o predictivos avanzados en la próxima fase, ¿cuál es el TU OBJETIVO PRINCIPAL con este dataset? (ej: predecir una variable, ver correlaciones, explorar libremente...)'.\nJSON:\n{safe_profiling_data}"
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
            "current_phase": PHASE_UNDERSTANDING, # Ahora pasamos a la fase de comprensión de problema
            "artifacts": artifacts_metadata
        }
    else:
        error_msg = f"Hubo un fallo generando el EDA en el Sandbox: {tool_response.error}\\nInfo técnica: {tool_response.data.get('stderr')}"
        return {
            "messages": [AIMessage(content=error_msg)],
            "current_phase": PHASE_PROFILING
        }

async def eda_agent_node(state: KDDState) -> Dict[str, Any]:
    """
    Nodo de Fase 3: Post-perfilado (EDA Ampliado y Planificación).
    Recibe un LLM con capacidad de Tool Calling para ejecutar Pandas dinámico.
    """
    from src.core.agent_factory import AgentFactory
    from src.api.mcp_tools import execute_pandas_code
    
    dataset_context = state.get("dataset_context", {})
    filename = dataset_context.get("current_filename", "desconocido.csv")
    
    llm = AgentFactory.create_llm()
    # Inyectamos nuestra Tool de Langchain al LLM
    llm_with_tools = llm.bind_tools([execute_pandas_code])
    
    system_prompt = SystemMessage(
        content="Eres un Experto Científico de Datos. Tu objetivo es explorar, limpiar y preparar datos.\n"
                f"Dataset cargado: '{filename}' (path: '/sandbox/datasets/{filename}').\n"
                "=== MANUAL ESTRICTO DE PROGRAMACIÓN PYTHON (SANDBOX EFÍMERO) ===\n"
                "CADA VEZ que uses 'execute_pandas_code', tu código se ejecuta en un Docker en blanco. Por tanto:\n"
                "1. IMPORTA SIEMPRE: `import pandas as pd`, `import matplotlib.pyplot as plt`, `import seaborn as sns`.\n"
                f"2. LEE EL DATASET SIEMPRE: `df = pd.read_csv('/sandbox/datasets/{filename}')` antes de manipular variables.\n"
                "3. USA PRINT PARA OUTPUT: `print(df.head())`, si no imprimes, tú mismo no verás la respuesta.\n"
                "4. GRÁFICOS: JAMÁS uses `plt.show()`. Usa SIEMPRE `plt.savefig('/sandbox/datasets/out.png')` y devuelve explícitamente `print('[ARTIFACT:/sandbox/datasets/out.png]')` para el usuario.\n"
                "=================================================================\n"
                "Si te piden aplicar un modelo o calcular, USA CÓDIGO en vez de teoría.\n"
                "Si piden re-definir el objetivo (Fase 2), indícales que usen el botón 'Modificar Propósito Principal' del menú lateral."
    )
    
    # Invocamos al LLM con el historial conversacional
    response = await llm_with_tools.ainvoke([system_prompt] + state.get("messages", []))
    
    return {
        "messages": [response],
        "current_phase": PHASE_EDA
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
