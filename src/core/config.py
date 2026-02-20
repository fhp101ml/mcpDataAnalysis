import os
import yaml
from pydantic import BaseModel, Field
from src.core.logger import setup_logger

logger = setup_logger("ConfigManager")

class AppConfig(BaseModel):
    name: str = "KDD Conversacional"
    version: str = "0.1.0"
    debug: bool = False

class LLMConfig(BaseModel):
    ai_framework: str = "langgraph"
    provider: str = "ollama"
    model_name: str = "llama3.1:latest"
    temperature: float = 0.1
    max_tokens: int = 1500

class ObservabilityConfig(BaseModel):
    enable_langsmith: bool = False

class GlobalConfig(BaseModel):
    app: AppConfig = Field(default_factory=AppConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    observability: ObservabilityConfig = Field(default_factory=ObservabilityConfig)

class ConfigManager:
    """
    Gestor centralizado de configuración de la aplicación KDD.
    Carga los settings desde el archivo config.yaml y los expone mediante Pydantic.
    """
    _instance = None
    _config: GlobalConfig = None

    def __new__(cls, config_path: str = "config.yaml"):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._load_config(config_path)
        return cls._instance

    def _load_config(self, config_path: str):
        try:
            # Buscar el archivo relativo a la raíz del proyecto
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
            full_path = os.path.join(base_dir, config_path)
            
            with open(full_path, "r", encoding="utf-8") as f:
                yaml_data = yaml.safe_load(f)
                self._config = GlobalConfig(**yaml_data)
                
            logger.info(f"Configuración cargada correctamente desde {config_path}")
            
            # Aplicar configuraciones estructurales (ej: LangSmith)
            if self._config.observability.enable_langsmith:
                os.environ["LANGCHAIN_TRACING_V2"] = "true"
                logger.info("LangSmith Tracing activado vía configuración")
                
        except Exception as e:
            logger.error(f"Error cargando config.yaml. Usando defaults. Detalles: {e}")
            self._config = GlobalConfig()

    @property
    def get(self) -> GlobalConfig:
        return self._config

# Instancia global (Singleton) para fácil acceso
config_manager = ConfigManager()
