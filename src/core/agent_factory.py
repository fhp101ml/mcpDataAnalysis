from langchain_ollama import ChatOllama
from langchain_core.language_models.chat_models import BaseChatModel
from src.core.config import config_manager
from src.core.logger import setup_logger

logger = setup_logger("AgentFactory")

# Import placeholder para los tools
# from src.api.mcp_tools import SandboxMCPTool

class AgentFactory:
    """
    Factoría para instanciar el LLM subyacente de forma agnóstica basándose 
    en el gestor de configuración config.yaml
    """
    
    @staticmethod
    def create_llm(tools: list = None) -> BaseChatModel:
        """
        Instancia el modelo de chat y opcionalmente le hace bing de las 
        herramientas MCP / Tools de Langchain indicadas.
        """
        config = config_manager.get.llm
        logger.info(f"Instanciando LLM model={config.model_name} usando Provider={config.provider}")
        
        llm = None
        
        if config.provider.lower() == "ollama":
            from langchain_ollama import ChatOllama
            llm = ChatOllama(
                model=config.model_name,
                temperature=config.temperature,
                num_ctx=8192,
                num_predict=1024
            )
        elif config.provider.lower() == "openai":
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(
                model=config.model_name,
                temperature=config.temperature,
                max_tokens=config.max_tokens
            )
        else:
            raise NotImplementedError(f"Provider {config.provider} no implementado aún en la factoría.")
            
        # Si se pasan herramientas, se conectan directamente al modelo para Function Calling
        if tools and llm:
            try:
                llm = llm.bind_tools(tools)
                logger.info(f"Se han linkeado {len(tools)} tools al LLM de forma nativa.")
            except Exception as e:
                logger.error(f"El modelo no soporta binding de tools o falló: {e}")
                
        return llm
