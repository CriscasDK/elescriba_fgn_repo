#!/usr/bin/env python3
"""
API REST para el Sistema RAG de Documentos Jurídicos
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio
import json
import sys
import os
from datetime import datetime

# Agregar el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

# Importar desde src/core que tiene Azure Search integrado
from src.core.sistema_rag_completo import SistemaRAGTrazable, RespuestaRAG

# Instancia global del sistema RAG
sistema_rag = None

# Inicializar FastAPI
app = FastAPI(
    title="Sistema RAG - Documentos Jurídicos",
    description="API REST para consultas inteligentes sobre documentos jurídicos usando RAG",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configurar CORS para desarrollo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos Pydantic para requests/responses

class ConsultaRequest(BaseModel):
    pregunta: str
    usuario_id: Optional[str] = "api_user"
    ip_cliente: Optional[str] = "127.0.0.1"
    user_agent: Optional[str] = "API Client"

class ConsultaResponse(BaseModel):
    consulta_id: int
    respuesta_id: int
    pregunta: str
    respuesta: str
    metodo: str
    confianza: float
    tiempo_respuesta: int
    fuentes: List[Dict[str, Any]]
    metadatos_llm: Optional[Dict[str, Any]] = None
    timestamp: str

class FeedbackRequest(BaseModel):
    consulta_id: int
    respuesta_id: int
    calificacion: int  # 1-5
    comentario: Optional[str] = None
    aspectos: Optional[Dict[str, int]] = None
    respuesta_esperada: Optional[str] = None

class FeedbackResponse(BaseModel):
    feedback_id: int
    mensaje: str
    timestamp: str

class EstadisticasResponse(BaseModel):
    total_consultas: int
    consultas_hoy: int
    calificacion_promedio: float
    tiempo_respuesta_promedio: float
    metodos_utilizados: Dict[str, int]
    consultas_recientes: List[Dict[str, Any]]

# Eventos de startup y shutdown

@app.on_event("startup")
async def startup_event():
    """Inicializar el sistema RAG al arrancar"""
    global sistema_rag
    try:
        print("🚀 Inicializando Sistema RAG Completo...")
        sistema_rag = SistemaRAGTrazable()
        print("✅ Sistema RAG inicializado exitosamente")
    except Exception as e:
        print(f"❌ Error inicializando sistema RAG: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Limpiar recursos al cerrar la API"""
    print("🔄 Cerrando API del Sistema RAG")

# Endpoints principales

@app.get("/")
async def root():
    """Endpoint raíz con información de la API"""
    return {
        "mensaje": "Sistema RAG - Documentos Jurídicos",
        "version": "1.0.0",
        "estado": "operativo",
        "documentacion": "/api/docs",
        "endpoints": {
            "consulta": "/api/consulta",
            "feedback": "/api/feedback",
            "estadisticas": "/api/estadisticas",
            "salud": "/api/salud"
        }
    }

@app.get("/api/salud")
async def verificar_salud():
    """Endpoint de health check"""
    try:
        # Verificar que el sistema RAG esté funcionando
        if sistema_rag is None:
            raise HTTPException(status_code=503, detail="Sistema RAG no inicializado")
        
        return {
            "estado": "saludable",
            "timestamp": datetime.now().isoformat(),
            "sistema_rag": "operativo",
            "base_datos": "conectada"
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Sistema no saludable: {str(e)}")

@app.post("/consulta")
async def procesar_consulta(request: ConsultaRequest):
    """Procesar una consulta usando el sistema RAG con Azure Search"""
    try:
        if sistema_rag is None:
            raise HTTPException(status_code=503, detail="Sistema RAG no disponible")
        
        # Procesar consulta directamente
        resultado = sistema_rag.consultar(request.pregunta)
        
        # Formatear respuesta
        return {
            "pregunta": request.pregunta,
            "respuesta": resultado.respuesta,
            "metodo": resultado.metodo,
            "confianza": resultado.confianza,
            "tiempo_respuesta_ms": resultado.tiempo_ms,
            "fuentes": resultado.fuentes,
            "tokens_usados": resultado.tokens_usados,
            "costo_estimado": resultado.costo_estimado,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando consulta: {str(e)}")

@app.get("/api/estadisticas")
async def obtener_estadisticas():
    """Obtener estadísticas del sistema"""
    try:
        if sistema_rag is None:
            raise HTTPException(status_code=503, detail="Sistema RAG no disponible")
        
        # Obtener estadísticas del sistema
        stats = await sistema_rag.obtener_estadisticas_mejora_continua(7)  # Últimos 7 días
        
        # Procesar estadísticas para la respuesta
        metricas = {m['metrica']: m['valor'] for m in stats['metricas_generales']}
        
        return EstadisticasResponse(
            total_consultas=metricas.get('total_consultas', 0),
            consultas_hoy=metricas.get('consultas_hoy', 0),
            calificacion_promedio=metricas.get('calificacion_promedio', 0.0),
            tiempo_respuesta_promedio=metricas.get('tiempo_respuesta_promedio', 0.0),
            metodos_utilizados=metricas.get('metodos_utilizados', {}),
            consultas_recientes=stats.get('consultas_recientes', [])[:10]  # Últimas 10
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo estadísticas: {str(e)}")

@app.get("/api/consultas/ejemplos")
async def obtener_ejemplos_consultas():
    """Obtener ejemplos de consultas que se pueden hacer al sistema"""
    return {
        "ejemplos": [
            {
                "categoria": "Dashboard Ejecutivo",
                "consultas": [
                    "¿Cuántos documentos hay en total?",
                    "¿Cuáles son las estadísticas principales?",
                    "¿Cuántas personas y organizaciones han sido identificadas?"
                ]
            },
            {
                "categoria": "Búsqueda de Entidades",
                "consultas": [
                    "¿Quiénes son las personas más mencionadas?",
                    "¿Cuáles son las organizaciones principales?",
                    "¿Qué actores están relacionados con las FARC?"
                ]
            },
            {
                "categoria": "Análisis Complejo (RAG)",
                "consultas": [
                    "¿Cómo afectó el conflicto armado a las comunidades rurales?",
                    "¿Cuál fue el impacto de la violencia en el departamento de Meta?",
                    "¿Qué patrones se observan en los testimonios de víctimas?"
                ]
            },
            {
                "categoria": "Análisis Geográfico", 
                "consultas": [
                    "¿Qué departamentos fueron más afectados?",
                    "¿Cuáles son las zonas de mayor conflicto?",
                    "¿Cómo se distribuyó geográficamente la violencia?"
                ]
            }
        ]
    }

# Endpoint para desarrollo y debugging
@app.get("/api/debug/info")
async def obtener_info_debug():
    """Información de debug del sistema (solo para desarrollo)"""
    try:
        import psycopg2
        from dotenv import load_dotenv
        
        load_dotenv('.env.gpt41')
        
        # Información básica del sistema
        return {
            "sistema_rag": "inicializado" if sistema_rag else "no_inicializado",
            "timestamp": datetime.now().isoformat(),
            "python_version": sys.version,
            "variables_entorno": {
                "POSTGRES_DB": os.getenv('POSTGRES_DB', 'no_configurada'),
                "AZURE_OPENAI_ENDPOINT": os.getenv('AZURE_OPENAI_ENDPOINT', 'no_configurada')[:50] + "..." if os.getenv('AZURE_OPENAI_ENDPOINT') else 'no_configurada'
            }
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Iniciando API del Sistema RAG")
    print("📍 URL: http://localhost:8007")
    print("📚 Documentación: http://localhost:8007/api/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8007,
        log_level="info"
    )
