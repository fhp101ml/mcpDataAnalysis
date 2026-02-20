# KDD Conversacional

## Descripción del Proyecto
Sistema conversacional que acompaña al usuario durante todo el proceso de Descubrimiento de Conocimiento en Datos (KDD). Funciona como un copiloto analítico, facilitador metodológico y orquestador del workflow que guía al usuario mediante lenguaje natural, ejecuta análisis de forma automática y culmina con la generación autónoma de un dashboard interactivo que sintetiza resultados, insights y modelos.

## Utilidad
El valor principal del sistema no radica únicamente en el dashboard final, sino en el **proceso guiado**. Al actuar como un analista senior, el sistema:
- Evita análisis estadísticos o de machine learning incorrectos.
- Reduce errores en la preparación de datos.
- Mejora la interpretación de los resultados.
- Educa y enseña al usuario durante la exploración.

## Fases de Construcción del Sistema

### 🟢 Fase 1 — Fundaciones del sistema (infraestructura base)
**Objetivo:** Crear el "esqueleto" donde todo podrá ejecutarse.
**Qué se construye:** Backend FastAPI async, MCP server, Contratos de tools, Sistema de sesiones, Persistencia de artefactos, Layout del workspace por run, Docker sandbox básico (ejecución Python aislada).
**Resultado:** Sistema capaz de ejecutar código seguro y guardar resultados.

### 🟢 Fase 2 — Motor conversacional y estado del análisis
**Objetivo:** Que el sistema entienda conversaciones y mantenga contexto analítico.
**Qué se construye:** LangGraph orchestration, Memoria de sesión, Estado KDD, Interpretación de intención.
**Resultado:** El sistema sabe "en qué fase está" el análisis.

### 🟢 Fase 3 — Ingestión y comprensión de datos
**Objetivo:** Que el sistema entienda datasets automáticamente.
**Capacidades:** Upload CSV, Perfilado automático, Identificación de tipos, Evaluación de calidad, Resumen interpretado.
**Resultado:** Dataset contextualizado.

### 🟢 Fase 4 — Guía conversacional del proceso KDD
**Objetivo:** Que el sistema actúe como facilitador metodológico.
**Qué se implementa:** Flujo guiado (objetivo → datos → preparación → análisis → modelado → síntesis), Preguntas inteligentes, Propuestas de pasos.
**Resultado:** Experiencia tipo "analista experto".

### 🟢 Fase 5 — Ejecución de análisis exploratorio automático
**Objetivo:** EDA profundo generado dinámicamente.
**Capacidades:** Estadística descriptiva, Missing analysis, Outliers, Correlaciones, Visualizaciones, Interpretación automática.
**Resultado:** Insights iniciales claros.

### 🟢 Fase 6 — Preparación de datos y feature engineering
**Objetivo:** Construir pipeline reproducible.
**Qué incluye:** Limpieza, Imputación, Codificación, Transformaciones, Feature creation.
**Resultado:** Dataset listo para modelado.

### 🟢 Fase 7 — Modelado y descubrimiento de patrones
**Objetivo:** Extraer conocimiento.
**Capacidades:** Baseline ML, Comparación de modelos, Reglas de asociación, Segmentación, Evaluación.
**Resultado:** Conclusiones cuantificadas.

### 🟢 Fase 8 — Síntesis automática del conocimiento
**Objetivo:** Convertir análisis en narrativa coherente.
**Qué se construye:** Resumen interpretativo, Hallazgos clave, Limitaciones, Recomendaciones.
**Resultado:** Comprensión global.

### 🟢 Fase 9 — Generador automático de dashboard
**Objetivo:** Generar la interfaz final interactiva.
**Qué hace el sistema:** Decide qué paneles incluir, Genera layout, Inserta visualizaciones, Muestra métricas, Presenta insights.
**Resultado:** Dashboard listo para usar con Overview, Data quality, Visualizaciones, Model performance e Insights.

### 🟢 Fase 10 — Dashboard como artefacto vivo
**Objetivo:** Permitir iteración.
**Capacidades:** Modificar paneles vía chat, Añadir gráficos, Comparar modelos, Filtrar.
**Resultado:** Dashboard evolutivo.

### 🟢 Fase 11 — Sandbox alternativo (LangChain Deep Agents)
**Objetivo:** Añadir backend opcional.
**Qué se hace:** Adapter LangChain sandbox, Configuración intercambiable.
**Resultado:** Flexibilidad de ejecución.

### 🟢 Fase 12 — Robustez y producción
**Objetivo:** Preparar el sistema de forma estable.
**Qué incluye:** Logging, Observabilidad, Seguridad avanzada, Límites de recursos, Auditoría.
**Resultado:** Sistema estable.

---

## Historial de Versiones
- **v0.1.0** (Draft): Definición de la idea inicial, objetivos y fases del proyecto.
