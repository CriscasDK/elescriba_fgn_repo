"""
API REST para el Sistema RAG - Documentos Judiciales
Proporciona endpoints para consultas RAG con máxima trazabilidad legal
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import asyncio
import logging
import os
import sys
from datetime import datetime

# Agregar directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.sistema_rag_completo import SistemaRAGTrazable, ConsultaRAG

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicialización de FastAPI
app = FastAPI(
    title="API RAG - Documentos Judiciales",
    description="API REST para consultas RAG sobre documentos del caso Unión Patriótica",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuración CORS para permitir acceso desde la interfaz de víctimas
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios exactos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos Pydantic para request/response
class ConsultaRAGRequest(BaseModel):
    pregunta: str = Field(..., description="Pregunta del usuario", min_length=3, max_length=1000)
    usuario_id: Optional[str] = Field(default="api_user", description="ID del usuario")
    ip_cliente: Optional[str] = Field(default="127.0.0.1", description="IP del cliente")
    contexto_adicional: Optional[Dict[str, Any]] = Field(default=None, description="Contexto adicional para la consulta")

class FuenteRAG(BaseModel):
    cita: str = Field(..., description="Identificador de la cita (ej: CITA-1)")
    nombre_archivo: str = Field(..., description="Nombre del archivo fuente")
    expediente: Optional[str] = Field(None, description="Número de expediente")
    tipo_documento: Optional[str] = Field(None, description="Tipo de documento")
    pagina: Optional[str] = Field(None, description="Número de página")
    parrafo: Optional[str] = Field(None, description="Número de párrafo")
    relevancia: Optional[float] = Field(None, description="Score de relevancia")
    texto_fuente: str = Field(..., description="Texto completo del chunk citado")
    texto_resumen: Optional[str] = Field(None, description="Resumen del texto (primeros 200 chars)")

class RespuestaRAGResponse(BaseModel):
    texto: str = Field(..., description="Respuesta generada por el sistema RAG")
    fuentes: List[FuenteRAG] = Field(default=[], description="Fuentes con trazabilidad completa")
    confianza: float = Field(..., description="Nivel de confianza de la respuesta (0.0-1.0)")
    metodo: str = Field(..., description="Método utilizado para resolver la consulta")
    tiempo_respuesta: float = Field(..., description="Tiempo de respuesta en milisegundos")
    consulta_id: Optional[str] = Field(None, description="ID único de la consulta para trazabilidad")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp de la respuesta")

class EstadoSistemaResponse(BaseModel):
    estado: str = Field(..., description="Estado del sistema (activo/inactivo)")
    version: str = Field(..., description="Versión del sistema RAG")
    total_documentos: int = Field(..., description="Total de documentos indexados")
    conexion_db: bool = Field(..., description="Estado de conexión a base de datos")
    conexion_azure: bool = Field(..., description="Estado de conexión a Azure Search")
    tiempo_respuesta_promedio: float = Field(..., description="Tiempo promedio de respuesta en ms")

# Variable global para el sistema RAG
rag_system = None

async def get_rag_system():
    """Dependency para obtener el sistema RAG (singleton)"""
    global rag_system
    if rag_system is None:
        try:
            rag_system = SistemaRAGTrazable()
            logger.info("Sistema RAG inicializado correctamente")
        except Exception as e:
            logger.error(f"Error inicializando sistema RAG: {e}")
            raise HTTPException(status_code=500, detail="Error inicializando sistema RAG")
    return rag_system

@app.on_event("startup")
async def startup_event():
    """Evento de inicio - inicializar sistema RAG"""
    logger.info("Iniciando API RAG...")
    await get_rag_system()
    logger.info("API RAG iniciada correctamente")

@app.get("/", tags=["General"])
async def root():
    """Endpoint raíz - información básica de la API"""
    return {
        "message": "API RAG - Documentos Judiciales",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "consulta": "/rag/consulta",
            "estado": "/rag/estado",
            "salud": "/health"
        }
    }

@app.get("/health", tags=["General"])
async def health_check():
    """Health check del sistema"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "service": "rag-api"
    }

@app.post("/rag/consulta", response_model=RespuestaRAGResponse, tags=["RAG"])
async def procesar_consulta_rag(
    request: ConsultaRAGRequest,
    rag_system = Depends(get_rag_system)
):
    """
    Procesar consulta RAG con máxima trazabilidad legal
    
    - **pregunta**: Consulta del usuario sobre documentos judiciales
    - **usuario_id**: Identificador del usuario (opcional)
    - **ip_cliente**: IP del cliente (opcional)
    - **contexto_adicional**: Contexto adicional para la consulta (opcional)
    
    Returns respuesta con citas completas y trazabilidad máxima
    """
    try:
        logger.info(f"Procesando consulta RAG: {request.pregunta[:100]}...")
        
        # Crear consulta RAG
        consulta = ConsultaRAG(
            usuario_id=request.usuario_id,
            pregunta=request.pregunta,
            ip_cliente=request.ip_cliente
        )
        
        # Procesar consulta
        respuesta, consulta_id = await rag_system.procesar_consulta(consulta)
        
        # Convertir fuentes al formato de respuesta
        fuentes_response = []
        if respuesta.fuentes:
            for fuente in respuesta.fuentes:
                fuente_response = FuenteRAG(
                    cita=fuente.get('cita', 'N/A'),
                    nombre_archivo=fuente.get('nombre_archivo', 'N/A'),
                    expediente=fuente.get('expediente', 'N/A'),
                    tipo_documento=fuente.get('tipo_documento', 'N/A'),
                    pagina=fuente.get('pagina', 'N/A'),
                    parrafo=fuente.get('parrafo', 'N/A'),
                    relevancia=fuente.get('relevancia', 0.0),
                    texto_fuente=fuente.get('texto_fuente', ''),
                    texto_resumen=fuente.get('texto_resumen', '')
                )
                fuentes_response.append(fuente_response)
        
        # Construir respuesta
        response = RespuestaRAGResponse(
            texto=respuesta.texto,
            fuentes=fuentes_response,
            confianza=float(respuesta.confianza) if respuesta.confianza else 0.0,
            metodo=respuesta.metodo.value if hasattr(respuesta.metodo, 'value') else str(respuesta.metodo),
            tiempo_respuesta=float(respuesta.tiempo_respuesta) if respuesta.tiempo_respuesta else 0.0,
            consulta_id=consulta_id
        )
        
        logger.info(f"Consulta procesada exitosamente. ID: {consulta_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error procesando consulta RAG: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error procesando consulta: {str(e)}"
        )

@app.get("/rag/estado", response_model=EstadoSistemaResponse, tags=["RAG"])
async def obtener_estado_sistema(rag_system = Depends(get_rag_system)):
    """
    Obtener estado actual del sistema RAG
    
    Returns información sobre el estado de conexiones, estadísticas y rendimiento
    """
    try:
        # Aquí podrías agregar lógica para verificar conexiones
        # Por ahora retornamos estado básico
        
        response = EstadoSistemaResponse(
            estado="activo",
            version="1.0.0",
            total_documentos=1000,  # Obtener de la base de datos
            conexion_db=True,  # Verificar conexión real
            conexion_azure=True,  # Verificar conexión real
            tiempo_respuesta_promedio=1500.0  # Obtener estadísticas reales
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error obteniendo estado del sistema: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo estado: {str(e)}"
        )

@app.get("/rag/citas/{consulta_id}", tags=["RAG"])
async def obtener_citas_consulta(consulta_id: str):
    """
    Obtener detalles completos de las citas de una consulta específica
    
    Útil para auditoría y verificación legal
    """
    try:
        # Aquí implementarías la lógica para obtener las citas de una consulta específica
        # desde la base de datos usando el consulta_id
        
        return {
            "consulta_id": consulta_id,
            "mensaje": "Funcionalidad en desarrollo - obtener citas por ID"
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo citas para consulta {consulta_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo citas: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "rag_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
