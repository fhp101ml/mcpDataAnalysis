# KDD Conversacional

## Descripción del Proyecto
Sistema conversacional que acompaña al usuario durante todo el proceso de Descubrimiento de Conocimiento en Datos (KDD). Funciona como un copiloto analítico, facilitador metodológico y orquestador del workflow que guía al usuario mediante lenguaje natural, ejecuta análisis de forma automática y culmina con la generación autónoma de un dashboard interactivo que sintetiza resultados, insights y modelos.

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

### 🟢 Fase 5 — Guía conversacional del proceso KDD
**Objetivo:** Que el sistema actúe como facilitador metodológico.
**Qué se implementa:** Flujo guiado, Preguntas inteligentes, Propuestas de pasos.

### 🟢 Fase 6 — Ejecución de análisis exploratorio automático (EDA ampliado)
**Objetivo:** EDA profundo generado dinámicamente.
**Capacidades:** Estadística descriptiva a demanda, Correlaciones avanzadas, Outliers dinámicos por el Sandbox.

### 🟢 Fase 7 — Agente Generador y Linaje de Datos con MinIO
**Objetivo:** Construir pipeline reproducible y versionado de Data.
**Qué incluye:** Nodos capaces the inyectar código Pandas real, Tracking en el `KDDState` y volcado the datos mutables a Buckets de MinIO.

### 🟢 Fase 8 — Modelado y descubrimiento de patrones
**Objetivo:** Extraer conocimiento y baseline predictors.

### 🟢 Fase 9 — Síntesis automática del conocimiento
**Objetivo:** Convertir análisis en narrativa coherente a los usuarios del KDD.

### 🟢 Fase 10 — Dashboard como artefacto vivo
**Objetivo:** Permitir iteración.
**Capacidades:** Modificar paneles vía chat, Añadir gráficos de Plotly u otras librerías.

### 🟢 Fase 11 y 12 — Sandbox Alternativo y Robustez
**Objetivo:** Seguridad, logging, auditoria y alternativas LangChain.

---

## Historial de Versiones
- **v0.3.0** (Actual): Fase 3 (Ingestión asíncrona y Pefilado con YData en Sandbox) y Fase 4 (UI en Streamlit con Reportes Interactivos) completadas.
- **v0.2.0**: Infraestructura Docker y Arquitectura LangGraph completada. Carga de entornos integradas.
- **v0.1.0**: Definición de la idea inicial, objetivos y fases del proyecto.
