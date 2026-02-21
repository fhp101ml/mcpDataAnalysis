import streamlit as st
import requests
import os
import json

# Constantes API
API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="KDD Copilot",
    page_icon="📊",
    layout="wide"
)

# Inicialización de estados locales
if 'session_id' not in st.session_state:
    st.session_state.session_id = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'artifacts' not in st.session_state:
    st.session_state.artifacts = []
if 'current_phase' not in st.session_state:
    st.session_state.current_phase = "1_understanding_problem"

def init_kdd_session():
    """Llama a la API para crear una nueva UUID Session KDD"""
    try:
        response = requests.post(f"{API_URL}/session/new")
        if response.status_code == 200:
            data = response.json()
            st.session_state.session_id = data["session_id"]
            st.session_state.current_phase = data["current_phase"]
            st.session_state.chat_history = []
            st.session_state.artifacts = []
            st.sidebar.success(f"Sesión iniciada: {st.session_state.session_id[:8]}...")
        else:
            st.sidebar.error("Error al conectar con la API KDD.")
    except Exception as e:
        st.sidebar.error(f"Error de conexión: {e}")

def refresh_chat():
    """Actualiza el historial y los artefactos leyendo del estado del backend"""
    if st.session_state.session_id:
        try:
            res = requests.get(f"{API_URL}/session/{st.session_state.session_id}")
            if res.status_code == 200:
                data = res.json()
                st.session_state.chat_history = data["chat_history"]
                st.session_state.artifacts = data.get("artifacts", [])
                st.session_state.current_phase = data["current_phase"]
                st.session_state.user_goal = data.get("user_goal")
        except Exception as e:
            st.error(f"No se pudo refrescar el chat: {e}")

# ======= SIDEBAR ========
st.sidebar.title("Configuración KDD ⚙️")

if st.sidebar.button("NUEVA SESIÓN KDD", use_container_width=True):
    init_kdd_session()

st.sidebar.markdown("---")
st.sidebar.markdown("### Seleccionar Sesión Existente")
try:
    res_sessions = requests.get(f"{API_URL}/sessions")
    if res_sessions.status_code == 200:
        sessions_list = res_sessions.json().get("sessions", [])
        if sessions_list:
            options = {s["session_id"]: f"{s['filename']} ({s['current_phase']})" for s in sessions_list}
            
            # Detectar índice por defecto
            default_index = 0
            if st.session_state.session_id in options:
                default_index = list(options.keys()).index(st.session_state.session_id)
                
            selected_option = st.sidebar.selectbox(
                "Historial de análisis KDD",
                options=list(options.keys()),
                format_func=lambda x: options[x],
                index=default_index,
            )
            
            if st.sidebar.button("Cargar Sesión Seleccionada"):
                st.session_state.session_id = selected_option
                refresh_chat()
                st.rerun()
except Exception as e:
    st.sidebar.error(f"Error recuperando sesiones: {e}")

st.sidebar.markdown("---")

# Uploader solo activo si hay sesión
if st.session_state.session_id:
    st.sidebar.info(f"Fase actual: `{st.session_state.current_phase}`")
    
    if hasattr(st.session_state, 'user_goal') and st.session_state.user_goal:
        st.sidebar.success(f"🎯 **Objetivo**: {st.session_state.user_goal}")
        
    uploaded_file = st.sidebar.file_uploader("Subir Dataset (CSV)", type=["csv"], help="La fase de Ingestión se activará automáticamente.")
    if uploaded_file is not None:
        if st.sidebar.button("Ingestar y Analizar Dataset"):
            with st.spinner('Orquestando Agentes KDD & Profiling Sandbox...'):
                files = {'file': (uploaded_file.name, uploaded_file.getvalue(), 'text/csv')}
                data = {'session_id': st.session_state.session_id}
                
                try:
                    response = requests.post(f"{API_URL}/dataset/upload", files=files, data=data, timeout=300)
                    if response.status_code == 200:
                        st.sidebar.success("Ingestión completada.")
                        refresh_chat()
                    else:
                        st.sidebar.error(f"Fallo del workflow KDD: {response.text}")
                except Exception as e:
                    st.sidebar.error(f"Timeout del orquestador: {str(e)}")

st.sidebar.markdown("---")
if st.session_state.session_id:
    # Botón de retroceso de fase
    if st.session_state.current_phase not in ["1_data_profiling", "2_understanding_problem"]:
        if st.sidebar.button("🔙 Modificar Propósito Principal", help="Vuelve al Analista Proactivo para redefinir el objetivo de este análisis"):
            try:
                res = requests.post(f"{API_URL}/session/{st.session_state.session_id}/phase", json={"phase": "2_understanding_problem"})
                if res.status_code == 200:
                    st.sidebar.success("Fase reestablecida.")
                    refresh_chat()
                    st.rerun()
            except Exception as e:
                st.sidebar.error(f"Error cambiando fase: {e}")
                
    if st.sidebar.button("Refrescar Interfaz", icon="🔄"):
        refresh_chat()

# ======= MAIN AREA ========
st.title("📊 AutoKDD Conversacional UI")
st.markdown("Interacciona con el *Knowledge Discovery Flow* (FastAPI + LangGraph + Ollama/OpenAI Sandbox).")

if not st.session_state.session_id:
    st.info("👈 Crea una nueva sesión en el panel lateral para empezar el proceso.")
else:
    # Maquetación principal: [Chat y Artefactos (75%)] | [Estado del Grafo (25%)]
    col_main, col_state = st.columns([3, 1])
    
    with col_state:
        st.markdown("### 🧠 Estado del Grafo")
        st.info("Monitor en tiempo real del `KDDState`")
        # Mostramos el estado JSON
        state_dict = {
            "session_id": st.session_state.session_id,
            "current_phase": st.session_state.current_phase,
            "artifacts_count": len(st.session_state.artifacts),
            "messages_count": len(st.session_state.chat_history)
        }
        
        # Le pedimos a FastAPI el context completo para el debug
        agent_trace = []
        try:
            res = requests.get(f"{API_URL}/session/{st.session_state.session_id}")
            if res.status_code == 200:
                full_state = res.json()
                state_dict["dataset_context"] = full_state.get("dataset_context", {})
                agent_trace = full_state.get("agent_trace", [])
        except:
             pass
             
        st.json(state_dict)
        
        # Botón para descargar el estado raw de la sesión
        estado_json_str = json.dumps(state_dict, indent=2, ensure_ascii=False)
        st.download_button(
            label="⬇️ Descargar Estado Bruto (JSON)",
            data=estado_json_str,
            file_name=f"kdd_session_raw_{st.session_state.session_id}.json",
            mime="application/json",
            help="Descarga el historial interno para depuración o para compartir con un LLM de soporte."
        )
        
        # Parseando las tool calls a partir del historial (Trajectory)
        if agent_trace:
            st.markdown("#### 🛠️ Tool Calling Trace")
            for trace in agent_trace:
                if trace["event"] == "tool_call":
                    st.info(f"**Ejecutando**: `{trace['tool']}`\n\n```json\n{trace['args']}\n```")
                elif trace["event"] == "tool_result":
                    st.success(f"**Output de `{trace['tool']}`**:\n\n```text\n{trace['result']}\n```")
        
    with col_main:
        import re
        import os
        
        # Mostramos historial de chat
        for chat in st.session_state.chat_history:
            role = "assistant" if chat["type"] == "AI" else ("user" if chat["type"] == "User" else chat["type"])
            with st.chat_message(role):
                content = chat["content"]
                
                # Expresión regular para buscar la etiqueta Markdown o custom que hemos pedido al LLM
                grafico_match = re.search(r'(?:!\[.*?\]\((/sandbox/datasets/.*?\.png)\)|\[GRAFICO.*?(/sandbox/datasets/.*?\.png)\])', content)
                
                if grafico_match:
                    ruta_docker = grafico_match.group(1) or grafico_match.group(2)
                    ruta_local = "." + ruta_docker # /sandbox/datasets/... -> ./sandbox/datasets/...
                    
                    # Pintamos el texto limpiando la etiqueta
                    content_clean = content.replace(grafico_match.group(0), "")
                    st.markdown(content_clean)
                    
                    # Renderizamos la gráfica generada por Pandas local
                    if os.path.exists(ruta_local):
                        st.image(ruta_local, caption=f"Gráfico generado en Sandbox: {ruta_docker}")
                    else:
                        st.warning(f"El agente guardó un gráfico en `{ruta_docker}` pero no está accesible en disco.")
                else:
                    st.markdown(content)
    
    # Mostramos los artefactos encontrados en pestañas o expanders
    if st.session_state.artifacts:
        st.markdown("### 🗂️ Artefactos Persistidos (EDA / KDD)")
        for art in st.session_state.artifacts:
            if art["type"] == "profiling_html":
                with st.expander("Ver Perfilado Dinámico Interactivo (YData)", expanded=False):
                    # Como el fichero html está en local, lo abrimos y lo inyectamos
                    try:
                        # Ruta asumiendo root del workspace
                        # Recordar que se generaron con /sandbox/datasets/... localmente.
                        # En el entorno anfitrión quitamos el primer slash si era del contenedor e inyectamos.
                        # Sin embargo, src.main salva con "sandbox/datasets/" pero el artefacto tiene el path del docker: f"/sandbox/datasets/{base_name}_profile.html".
                        
                        safe_local_path = "." + art["path"] # ./sandbox/datasets/...
                        if os.path.exists(safe_local_path):
                            with open(safe_local_path, "r", encoding="utf-8") as f:
                                html_string = f.read()
                            st.components.v1.html(html_string, width=1200, height=800, scrolling=True)
                        else:
                            st.error(f"HTML local no encontrado en {safe_local_path}")
                    except Exception as e:
                        st.error(f"Error renderizando artefacto HTML: {e}")
            elif art["type"] == "profiling_json":
                 with st.expander("Ver Metadatos Estructurales (JSON)", expanded=False):
                      safe_local_path = "." + art["path"]
                      if os.path.exists(safe_local_path):
                          with open(safe_local_path, "r", encoding="utf-8") as f:
                               json_parsed = json.loads(f.read())
                          st.json(json_parsed)
            elif art["type"] == "image":
                 with st.expander(f"🖼️ Imagen: {art['filename']}", expanded=False):
                      safe_local_path = "." + art["path"]
                      if os.path.exists(safe_local_path):
                          st.image(safe_local_path, use_container_width=True)
                      else:
                          st.error(f"Imagen no disponible: {safe_local_path}")
            elif art["type"] == "csv":
                 with st.expander(f"📄 Dataset Derivado: {art['filename']}", expanded=False):
                      safe_local_path = "." + art["path"]
                      if os.path.exists(safe_local_path):
                          # Si es posible previsualizarlo
                          import pandas as pd
                          try:
                              df_prev = pd.read_csv(safe_local_path, nrows=100)
                              st.dataframe(df_prev)
                              
                              with open(safe_local_path, "rb") as f:
                                  st.download_button("📥 Descargar CSV", f, file_name=art['filename'], mime="text/csv", key=f"dl_{art['filename']}")
                          except Exception as e:
                              st.error(f"No se puede leer el CSV en memoria: {e}")
                      else:
                          st.error(f"CSV no disponible en disco local: {safe_local_path}")

# Footer placeholder for text input
if st.session_state.session_id:
    user_input = st.chat_input("Escribe tu instrucción de Machine Learning o KDD aquí...")
    if user_input:
        # Añade vista previa local optimista
        st.session_state.chat_history.append({"type": "User", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
            
        with st.spinner("El Agente KDD está pensando..."):
            try:
                res = requests.post(
                    f"{API_URL}/session/{st.session_state.session_id}/message", 
                    json={"user_text": user_input},
                    timeout=120
                )
                if res.status_code == 200:
                    data = res.json()
                    st.session_state.current_phase = data["current_phase"]
                    # Refrescamos todo el historial oficial
                    refresh_chat()
                    st.rerun() # Fuerza repintado de los chat_messages recientes
                else:
                    st.error(f"Error procesando mensaje: {res.text}")
            except Exception as e:
                st.error(f"Fallo en la comunicación: {e}")
