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
            # En Linux (Snap) DEBEMOS usar unix:// porque from_env() hereda scheme rotos.
            docker_host = os.environ.get("DOCKER_HOST", "unix:///var/run/docker.sock")
            cls._client = docker.DockerClient(base_url=docker_host)
        return cls._client

    @staticmethod
    def _run_docker_sync(python_code: str) -> Dict[str, Any]:
        """Versión síncrona aislada para ejecutarse en ThreadPool"""
        client = SandboxMCPTool.get_client()
        tmp_dir = tempfile.mkdtemp(prefix="kdd_sandbox_")
        
        try:
            script_path = os.path.join(tmp_dir, "script.py")
            with open(script_path, "w") as f:
                f.write(python_code)

            container = client.containers.run(
                "kdd-sandbox:latest",
                command=["python", "/app/script.py"],
                volumes={
                    tmp_dir: {'bind': '/app', 'mode': 'ro'},
                    os.path.abspath("sandbox/datasets"): {'bind': '/sandbox/datasets', 'mode': 'rw'}
                },
                remove=False,
                detach=True,  # Necesitamos detach=True para que devuelva el obj Container
                mem_limit="512m",
                network_disabled=True 
            )
            
            # Bloquear la ejecución hasta que acaba
            exit_status = container.wait()
            
            # Extraer strings
            output = container.logs().decode("utf-8")
            
            # Limpiar manualmente
            container.remove(force=True)
            
            if exit_status.get("StatusCode", 0) != 0:
                 return {"error": output}
                 
            return {"output": output}
            
        except docker.errors.ContainerError as e:
            err_msg = e.container.logs().decode("utf-8")
            e.container.remove(force=True)
            return {"error": err_msg}
        except Exception as e:
            return {"error": str(e)}
        finally:
            import shutil
            shutil.rmtree(tmp_dir, ignore_errors=True)

    @staticmethod
    async def execute_python_code(python_code: str) -> MCPToolResponse:
        """
        Versión asíncrona segura que delega a un hilo secundario 
        para evitar el bloqueo del event loop.
        """
        import asyncio
        logger.info("Iniciando ejecución de código en sandbox...")
        logger.debug(f"Código a ejecutar: {python_code}")
        
        # Ejecutar de forma aislada
        result = await asyncio.to_thread(SandboxMCPTool._run_docker_sync, python_code)
        
        if "error" in result:
            logger.error(f"Error en sandbox: {result['error']}")
            return MCPToolResponse(success=False, data={"stdout": "", "stderr": result["error"]}, error=result["error"])
            
        return MCPToolResponse(success=True, data={"stdout": result["output"], "stderr": ""})

    @staticmethod
    async def run_data_profiling(dataset_filename: str) -> MCPToolResponse:
        """
        Ejecuta el EDA automático de ydata-profiling sobre un dataset específico 
        dentro del contenedor (asumiendo que está montado en /sandbox/datasets/)
        """
        python_code = f'''
import pandas as pd
from ydata_profiling import ProfileReport
import json

try:
    # Ruta relativa dentro del docker
    file_path = f"/sandbox/datasets/{dataset_filename}"
    df = pd.read_csv(file_path)
    
    # Perfilamos de manera optimizada (minimal=True evita matrices muy pesadas para LLMs)
    profile = ProfileReport(df, title="KDD Auto-EDA", minimal=True)
    
    # 1. Generamos info estadística en JSON a variable
    json_data = profile.to_json()
    
    # 2. Guardamos persistencia física (JSON y HTML)
    base_name = "{dataset_filename}".replace(".csv", "")
    profile.to_file(f"/sandbox/datasets/{{base_name}}_profile.html")
    with open(f"/sandbox/datasets/{{base_name}}_profile.json", "w") as f:
         f.write(json_data)
         
    print("PROFILING_SUCCESS")
    print(json_data)
except Exception as e:
    import sys
    print(f"PROFILING_ERROR: {{str(e)}}", file=sys.stderr)
    sys.exit(1)
'''
        
        response = await SandboxMCPTool.execute_python_code(python_code)
        
        # Parseando la salida para un uso lógico por el agente conversacional
        if response.success and "PROFILING_SUCCESS" in response.data.get("stdout", ""):
            stdout = response.data.get("stdout", "")
            try:
                # Separamos por el token exacto que pusimos antes del print
                json_part = stdout.split("PROFILING_SUCCESS")[1].strip()
                response.data["profiling_json"] = json_part
            except Exception as e:
                logger.error(f"Error parseando el output del profiling: {e}")
                response.data["profiling_json"] = "{}"
                
        return response
