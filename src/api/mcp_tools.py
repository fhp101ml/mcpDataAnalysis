import docker
from typing import Any, Dict
from pydantic import BaseModel
import tempfile
import os
from src.core.logger import setup_logger

logger = setup_logger("SandboxMCPTool")

class MCPToolResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    error: str | None = None

class SandboxMCPTool:
    """
    Integración real con el contenedor Docker de análisis (kdd-sandbox).
    Permite ejecutar código Python de forma segura.
    """
    
    _client = None

    @classmethod
    def get_client(cls):
        if cls._client is None:
            cls._client = docker.from_env()
        return cls._client

    @staticmethod
    async def execute_python_code(code: str, dataset_path: str = None) -> MCPToolResponse:
        """
        Ejecuta python en el sandbox aislado.
        
        Args:
            code (str): El código Python a ejecutar.
            dataset_path (str): (Pendiente) Ruta a un dataset local para montar.
        """
        client = SandboxMCPTool.get_client()
        
        # Guardamos el código en un archivo temporal para montarlo
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_script:
            temp_script.write(code)
            temp_script_path = temp_script.name

        try:
            logger.info("Iniciando ejecución de código en sandbox...")
            logger.debug(f"Código a ejecutar: {code}")
            
            # TODO: Fase 3 - Añadir volúmenes para pasar datasets al contenedor
            # volumes = {dataset_dir: {'bind': '/data', 'mode': 'ro'}} si aplicara
            
            # Ejecutamos el contenedor con el script montado
            container = client.containers.run(
                image="kdd-sandbox",
                command=["python", "/script.py"],
                volumes={temp_script_path: {'bind': '/script.py', 'mode': 'ro'}},
                remove=True,        # Autodestruir al terminar
                network_disabled=True, # Sin internet
                mem_limit="512m",   # Limitar memoria (aplica a Fase 12, pero es buena práctica inicial)
                user="sandboxuser", # Usuario sin privilegios
                stdout=True,
                stderr=True
            )
            
            # Decodificamos la salida generada
            output = container.decode('utf-8')
            logger.info("Ejecución en sandbox exitosa.")
            
            return MCPToolResponse(
                success=True,
                data={"stdout": output, "stderr": ""},
            )
            
        except docker.errors.ContainerError as e:
            # Captura errores en el código Python ejecutado (SyntaxError, etc)
            error_output = e.stderr.decode('utf-8') if e.stderr else str(e)
            logger.warning(f"Error de ejecución dentro del código Python: {error_output}")
            return MCPToolResponse(
                success=False,
                data={"stdout": "", "stderr": error_output},
                error="El script Python devolvió un error de ejecución."
            )
        except Exception as e:
            # Errores generales de Docker o Sistema
            logger.error(f"Error general en el daemon de Docker: {str(e)}")
            return MCPToolResponse(
                success=False,
                data={"stdout": "", "stderr": ""},
                error=f"Error en el Sandbox: {str(e)}"
            )
        finally:
            # Limpieza del script temporal
            if os.path.exists(temp_script_path):
                os.remove(temp_script_path)
