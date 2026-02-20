from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title="KDD Conversational API",
    description="Backend para el sistema de Descubrimiento de Conocimiento en Datos",
    version="0.1.0"
)

class HealthCheckResponse(BaseModel):
    status: str
    message: str

@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Endpoint de comprobación de salud del sistema."""
    return HealthCheckResponse(status="ok", message="KDD Conversational System is running")
