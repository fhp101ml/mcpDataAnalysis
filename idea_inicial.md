# Sistema Conversacional KDD

Construir un sistema conversacional que acompañe al usuario durante todo el proceso de descubrimiento de conocimiento en datos (KDD), guiándolo de forma progresiva mediante diálogo en lenguaje natural, ejecutando análisis automáticamente y culminando con la generación autónoma de un dashboard interactivo que sintetice resultados, insights y modelos.

## 🧭 El chat como “guía del proceso KDD”

No es solo un chat reactivo.

Es un:
👉 facilitador metodológico
👉 copiloto analítico
👉 orquestador del workflow

El sistema sabe en qué fase está el análisis y adapta la conversación.

## 🧬 Fases del KDD guiadas por conversación

### 1️⃣ Ingestión y Pre-análisis automático (Comprensión de Datos Inicial)
El proceso comienza cuando el usuario sube el dataset.
Automáticamente el sistema realiza:
- Perfilado básico rápido
- Calidad de datos (nulos, tipos)
- Identificación de variables clave y posibles targets

Explica: *El dataset tiene 32 variables, con valores faltantes en 3 columnas...*

### 2️⃣ Definición del problema y Trazado de Objetivos (IA Proactiva)
Basándose en el pre-análisis anterior, el sistema actúa proactivamente. No solo presenta los datos, sino que **da una visión del problema**:
- Indica qué objetivos asume que se pueden conseguir con esos datos.
- Pregunta al usuario por sus intenciones reales para alinear el objetivo.
- Ofrece una guía de los próximos pasos.

Ejemplo: *Veo que tienes una variable 'Churn' muy desbalanceada. Podríamos predecir la fuga de clientes. ¿Es este tu objetivo principal o solo quieres explorar patrones?*

### 3️⃣ Preparación de datos
Propone:
- Limpieza
- Transformaciones
- Feature engineering

Consulta: ¿Quieres imputar los valores faltantes con la media o eliminar filas?

### 4️⃣ Análisis exploratorio
Ejecuta:
- Distribuciones
- Correlaciones
- Outliers
- Visualizaciones

Interpreta: Observamos una correlación fuerte entre…

### 5️⃣ Modelado
Sugiere:
- Modelos adecuados
- Baselines
- Evaluación

Explica: Un modelo de regresión parece apropiado…

### 6️⃣ Evaluación e interpretación
Presenta:
- Métricas
- Importancias
- Limitaciones

Pregunta: ¿Quieres probar otro enfoque?

### 7️⃣ Síntesis → Dashboard automático
Aquí está tu objetivo clave.

El sistema:
- Decide qué mostrar
- Genera paneles
- Integra resultados

## 📊 Qué contiene el dashboard final

El dashboard no es genérico — es contextual.
Incluye:

🟢 **Overview:** Resumen del dataset, Calidad, Tamaño, Variables clave
🟢 **Insights:** Hallazgos principales, Patrones detectados
🟢 **Visualizaciones:** Distribuciones, Correlaciones, Tendencias
🟢 **Modelos:** Métricas, Comparaciones, Importancias
🟢 **Explorador:** Predicciones interactivas, Segmentación
🟢 **Recomendaciones:** Siguientes pasos

## 🧠 El sistema decide cuándo generar el dashboard

No se genera al principio.
Se genera cuando:
✅ Hay suficiente contexto
✅ El análisis está maduro
✅ El usuario lo solicita o el agente lo propone

Ejemplo: Creo que tenemos suficiente información para construir un dashboard. ¿Lo genero?

## 🛰️ Arquitectura conceptual del flujo
Chat
  ↓
Agente KDD (LangGraph)
  ↓
MCP tools
  ↓
Análisis incremental
  ↓
Síntesis
  ↓
Dashboard generator

## 🔌 El KDD como Motor Central (Servidor MCP)

El objetivo final del sistema trasciende a su propia interfaz de usuario. Está diseñado para ser un **cerebro analítico interoperable**. En la fase final, el proyecto expondrá toda su inteligencia (el Grafo LangGraph y el Sandbox seguro) a través del **Model Context Protocol (MCP)**.

En lugar de ser solo una aplicación web aislada (Streamlit + FastAPI), el KDD actuará como un **Servidor MCP**.

¿Qué permite esto?
- **Exposición como Tools:** Agentes externos (ej: Claude Desktop, Cursor, Asistentes de otros proyectos) podrán solicitar al KDD que ejecute perfiles de datos, limpiezas o entrenamientos de modelos delegando la tarea en nuestro Sandbox. Ejemplo: `ejecutar_eda_avanzado(dataset.csv)`.
- **Exposición como Resources:** Nuestro sistema compartirá su memoria (el Estado KDD) en formato estándar para que otros sistemas lean los *insights* extraídos y los reportes generados sin intervención humana.

**Arquitectura final:**
1. Interfaz Humana: `UI Streamlit -> FastAPI REST -> LangGraph KDD`
2. Interfaz Inter-Agentes (M2M): `Cliente MCP Externo -> Servidor MCP (KDD) -> LangGraph KDD`

## 🧩 El dashboard como artefacto vivo

Importante:
👉 No es estático.

El usuario puede decir:
- Añade este gráfico
- Filtra por región
- Compara modelos
- Muestra importancia de variables
Y el sistema lo actualiza.

## 🧬 Filosofía de interacción

El sistema actúa como:
Un analista senior que no solo responde preguntas, sino que conduce el proceso.

## 🧠 Insight clave (muy importante)

El valor no está solo en el dashboard.
Está en:
👉 el proceso guiado que lleva a construirlo

Porque:
- Evita análisis incorrectos
- Reduce errores
- Mejora interpretación
- Enseña al usuario

## 🧭 En resumen

Sí:
✅ El chat guía el proceso KDD
✅ El sistema ejecuta análisis progresivamente
✅ El usuario participa mediante diálogo
✅ El sistema sintetiza conocimiento
✅ Y finalmente genera un dashboard automáticamente
