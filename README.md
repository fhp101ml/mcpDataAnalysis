# KDD Conversacional

## Descripción del Proyecto
Sistema conversacional que acompaña al usuario durante todo el proceso de Descubrimiento de Conocimiento en Datos (KDD). Funciona como un copiloto analítico, facilitador metodológico y orquestador del workflow que guía al usuario mediante lenguaje natural, ejecuta análisis de forma automática y culmina con la generación autónoma de un dashboard interactivo que sintetiza resultados, insights y modelos.

### El Horizonte MCP (Model Context Protocol)
El objetivo final arquitectónico de la aplicación transciende su interfaz web (`Streamlit`). Una vez que el ciclo KDD esté totalmente operativo y el motor de agentes sea infalible, **se creará una versión independiente exponiendo el sistema íntegramente como un servicio MCP**.
Esto significa que el proyecto actuará como un "Agente KDD Universal" conectable a cualquier ecosistema de IA corporativo o cliente compatible (como *Claude Desktop* o *Cursor*), permitiéndoles usar a nuestro experto en datos como si fuera una simple función o comando a la que delegarle la ingesta, análisis y creación de modelos de Machine Learning dentro del Sandbox aislado, devolviendo los *insights* y *artefactos* extraídos al agente principal.

## Arquitectura del Motor Conversacional (Agentes)

El corazón conversacional de la aplicación funciona como una máquina de estados orquestada por **LangGraph**. A diferencia de un chatbot tradicional lineal, el sistema actúa como un grupo de agentes especialistas organizados por un **Router**:

- **Nodo Router:** El usuario habla y el mensaje pasa por el router. Este nodo monitoriza la fase metodológica en la que se encuentra la conversación (`1_understanding`, `4_eda`, etc.) y decide a qué agente experto enviarle el flujo.
- **Goal Agent (Especialista Fase 1):** Un modelo dedicado exclusivamente a hacer preguntas exploratorias al principio de la conversación. No ejecuta código. Su misión es garantizar que el usuario define claramente "qué quiere conseguir" (predecir, agrupar, encontrar anomalías) y almacenarlo en la memoria del sistema.
- **Generic/Specialist Agents (Fases > 1):** A medida que la fase avanza a perfilado, EDA o modelado, el router despertará a agentes que tienen capacidades de escribir Python (usando LLMs a los que se asocia el Tool_Node). Estos agentes delegarán la ejecución del código al [Sandbox Docker], recuperarán las respuestas y se las explicarán al usuario.

*Para el desarrollo es imprescindible que exista un archivo `src/.env` configurado que contenga al menos las API keys de los LLM predeterminados (Ej: `OPENAI_API_KEY`, `MISTRAL_API_KEY`, etc), que la aplicación se encargará de cargar en tiempo de inicialización.*

## Utilidad
El valor principal del sistema no radica únicamente en el dashboard final, sino en el **proceso guiado**. Al actuar como un analista senior, el sistema:
- Evita análisis estadísticos o de machine learning incorrectos.
- Reduce errores en la preparación de datos.
- Mejora la interpretación de los resultados.
- Educa y enseña al usuario durante la exploración.

## Instalación y Ejecución Local

Para reproducir este sistema en local, se recomienda el uso de `pyenv` para preservar la pureza del entorno de desarrollo.

### Pre-requisitos
- Python 3.12.3 (Configurado a través de `pyenv`)
- Docker Desktop / Engine (Activo en segundo plano para el Sandbox Analítico)

### 1. Preparación del Entorno
```bash
# 1. Configurar la versión correcta de Python
pyenv local 3.12.3

# 2. Crear entorno virtual
python -m venv .venv
source .venv/bin/activate

# 3. Instalar librerías
pip install -r requirements.txt
```

### 2. Variables de Entorno
Es imprescindible crear un archivo `src/.env` y, opcionalmente, `.env` en la raíz del proyecto para definir las claves base de los LLM que alimentan LangGraph. Un ejemplo del archivo (o su plantilla `.env.example` si existe) sería:
```ini
OPENAI_API_KEY=sk-....
MISTRAL_API_KEY=your_key_here
```

### 3. Ejecución Paralela
El sistema utiliza una arquitectura bi-modal manual para depuración. Se requieren dos terminales abiertas:

**Terminal 1: Iniciar el Motor Inteligente KDD (FastAPI)**
Conserva el contexto, la memoria SQLite de las sesiones, y el enrutamiento LangGraph.
```bash
source .venv/bin/activate
uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
```

**Terminal 2: Iniciar la Interfaz de Usuario Experto (Streamlit)**
Levanta la SPA que interactúa con el backend consumiendo los endpoints REST.
```bash
source .venv/bin/activate
streamlit run src/ui/app.py
```
Accede posteriormente por navegador web a `http://localhost:8501`.

## Fases de Construcción del Sistema

### 🟢 Fase 1 — Fundaciones del sistema (infraestructura base)
**Objetivo:** Crear el "esqueleto" donde todo podrá ejecutarse.
**Qué se construyó:** Backend FastAPI async, contrato inicial de servers MCP, Docker sandbox para ejecución analítica aislada y logging estandarizado.

### 🟢 Fase 2 — Motor conversacional y estado del análisis
**Objetivo:** Que el sistema entienda conversaciones y mantenga contexto analítico.
**Qué se construyó:** Grafo maestro de LangGraph, Memoria de sesión y Estado Global KDD.

### 🟢 Fase 3 — Ingestión y comprensión de datos
**Objetivo:** Que el sistema entienda datasets automáticamente.
**Capacidades:** Upload CSV, Perfilado automático, Identificación de tipos, Evaluación de calidad, Resumen interpretado.
**Resultado:** Dataset contextualizado.

### 🟢 Fase 4 — Interfaz Gráfica de Usuario (Web UI)
**Objetivo:** Permitir al experto interactuar con el flujo sin usar la terminal.
**Qué se implementa:** Cliente Streamlit asíncrono, renderizado the componentes HTML (Reportes YData) y subida de archivos al Sandbox.

### 🟢 Fase 5 — Guía conversacional del proceso KDD y Memoria Avanzada
**Objetivo:** Que el sistema actúe como facilitador metodológico con memoria persistente.
**Qué se implementa:** 
- Flujo guiado, Preguntas inteligentes, Propuestas de pasos.
- Sustitución del Session Manager virtual por **Checkpointers de LangGraph** (SqliteSaver/PostgresSaver) para ganar persistencia nativa de hilos, capacidad de *Time Travel* (volver atrás en análisis) e interrupciones dinámicas (*Human-in-the-loop*).

### 🟢 Fase 6 — Ejecución de análisis exploratorio automático (EDA ampliado)
**Objetivo:** EDA profundo generado dinámicamente.
**Capacidades:** Estadística descriptiva a demanda, Correlaciones avanzadas, Outliers dinámicos por el Sandbox.

### 🟢 Fase 7 — Agente Generador y Linaje de Datos con MinIO
**Objetivo:** Construir un pipeline reproducible y centralizado de artefactos.
**Qué incluye:** 
- Almacenamiento físico de archivos (gráficos, CSVs procesados, modelos) en Buckets de **MinIO (S3)**.
- **KDDState tracking**: Inyección de metadatos ricos en el estado global para que el Dashboad Final o los agentes los consuman.

**Estructura del Estado de Artefactos:**
```python
class KDDArtifact(TypedDict):
    nombre_artefacto: str
    breve_descripcion: str
    s3_path: str          # Ej: s3://kdd-artifacts/session_123/eda/correlaciones.png
    fase_generacion: str  # Ej: '4_eda', '5_modelado'
    tipo: str             # Ej: 'plot', 'dataset_limpio', 'model_pkl'
```
*Mecánica:* El Sandbox o el Agente sube el archivo a MinIO y añade un objeto `KDDArtifact` a la lista `state["artifacts"]`. Cuando se genere el Dashboard final, el LLM tendrá a su disposición el inventario completo, su descripción y su ruta directa para ensamblar interactividad.

### 🟢 Fase 8 — Modelado y descubrimiento de patrones
**Objetivo:** Extraer conocimiento y baseline predictors.

### 🟢 Fase 9 — Síntesis automática del conocimiento
**Objetivo:** Convertir análisis en narrativa coherente a los usuarios del KDD.

### 🟢 Fase 10 — Dashboard como artefacto vivo
**Objetivo:** Permitir iteración.
**Capacidades:** Modificar paneles vía chat, Añadir gráficos de Plotly u otras librerías.

### 🟢 Fase 11 y 12 — Sandbox Alternativo y Robustez
**Objetivo:** Seguridad, logging, auditoria y alternativas LangChain.

### 🟢 Fase 13 — Interoperabilidad (El KDD como Servidor MCP)
**Objetivo:** Convertir el motor analítico en un "Agente Especialista" conectable (enchufable) a otros sistemas, proyectos y herramientas LLM (Claude Desktop, Cursor, etc.).
**Qué se implementa:** 
- Exposición de la lógica LangGraph a través del protocolo estándar **MCP (Model Context Protocol)**.
- El sistema ofrecerá sus capacidades (*Tools*: perfilar datos, entrenar modelos en sandbox) y su memoria (*Resources*: insights, reportes EDA) a agentes "Generalistas" externos.
- La aplicación mantendrá una arquitectura dual: Backend REST (para humanos vía UI) + Servidor MCP (para interoperabilidad IA a IA).

---

## Historial de Versiones
- **v0.5.0** (Actual): Fase 6 (EDA Dinámico y Sandbox Efímero) y completado final de la Fase 5 (Recarga de historial desde bases de datos vectoriales persistentes). Agente de código Python plenamente funcional, enrutamiento condicional perfecto en el Session Manager.
- **v0.4.0**: Fase 5 (Guía conversacional y Memoria Avanzada) completada. Integración de `AsyncSqliteSaver` nativo de LangGraph para ruteo asíncrono y reordenación del flujo para IA Proactiva post-perfilado. 
- **v0.3.0**: Fase 3 (Ingestión asíncrona y Pefilado con YData en Sandbox) y Fase 4 (UI en Streamlit con Reportes Interactivos) completadas.
- **v0.2.0**: Infraestructura Docker y Arquitectura LangGraph completada. Carga de entornos integradas.
- **v0.1.0**: Definición de la idea inicial, objetivos y fases del proyecto.
