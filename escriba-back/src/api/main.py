"""
ESCRIBA-BACK API REST
Sistema de consultas de documentos judiciales
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pathlib import Path

# Cargar variables de entorno del .env
# Buscar .env en el directorio escriba-back
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from src.api.routes import consultas

# Versión de la API
API_VERSION = "1.0.0"

# Crear app FastAPI
app = FastAPI(
    title="ESCRIBA-BACK API",
    description="API REST para consultas de documentos judiciales",
    version=API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS para permitir requests desde frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restringir en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(consultas.router, prefix="/api/v1", tags=["consultas"])

# Health check
@app.get("/")
async def root():
    return {
        "service": "ESCRIBA-BACK",
        "version": API_VERSION,
        "status": "operational"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}
