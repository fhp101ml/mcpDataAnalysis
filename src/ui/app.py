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
        except Exception as e:
            st.error(f"No se pudo refrescar el chat: {e}")

# ======= SIDEBAR ========
st.sidebar.title("Configuración KDD ⚙️")

if st.sidebar.button("NUEVA SESIÓN KDD", use_container_width=True):
    init_kdd_session()

st.sidebar.markdown("---")

# Uploader solo activo si hay sesión
if st.session_state.session_id:
    st.sidebar.info(f"Fase actual: `{st.session_state.current_phase}`")
    
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
    if st.sidebar.button("Refrescar Interfaz", icon="🔄"):
        refresh_chat()

# ======= MAIN AREA ========
st.title("📊 AutoKDD Conversacional UI")
st.markdown("Interacciona con el *Knowledge Discovery Flow* (FastAPI + LangGraph + Ollama/OpenAI Sandbox).")

if not st.session_state.session_id:
    st.info("👈 Crea una nueva sesión en el panel lateral para empezar el proceso.")
else:
    # Mostramos historial de chat
    for chat in st.session_state.chat_history:
        role = "assistant" if chat["type"] == "AI" else ("user" if chat["type"] == "User" else chat["type"])
        with st.chat_message(role):
            st.markdown(chat["content"])
    
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
                          

# Footer placeholder for text input (Chat Input in Phase 5)
if st.session_state.session_id:
    user_input = st.chat_input("Escribe tu instrucción de Machine Learning o KDD aquí...")
    if user_input:
        with st.chat_message("user"):
            st.markdown(user_input)
        with st.chat_message("assistant"):
            st.markdown("_El motor de conversación para la Fase 5 está pendiente de enganchar a Streamlit. Se guardará tu texto en breve._")
