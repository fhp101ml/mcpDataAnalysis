import logging
import sys
import os

# Nivel de log desde variable de entorno o INFO por defecto
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()

# Format estándar claro para trazabilidad
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

def setup_logger(name: str) -> logging.Logger:
    """
    Configura y devuelve un logger estructurado para el módulo especificado.
    Evita los print() dispersos y permite trazabilidad.
    """
    logger = logging.getLogger(name)
    
    # Previene duplicidad si ya está configurado
    if logger.hasHandlers():
        return logger
        
    logger.setLevel(LOG_LEVEL)
    
    # Salida por consola estándar
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(console_handler)
    
    # Salida a fichero para auditoría u observabilidad local
    os.makedirs("logs", exist_ok=True)
    file_handler = logging.FileHandler("logs/kdd_app.log")
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(file_handler)
    
    # Propagar = False para evitar que uvicorn lo duplique 
    logger.propagate = False
    
    return logger
