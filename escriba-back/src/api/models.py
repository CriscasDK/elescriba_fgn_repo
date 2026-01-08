"""
Modelos Pydantic para la API REST de ESCRIBA
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ==================== MODELOS DE VÍCTIMAS ====================

class Victima(BaseModel):
    """Modelo de víctima con menciones"""
    nombre: str = Field(..., description="Nombre completo de la víctima")
    menciones: int = Field(..., description="Número de menciones en documentos")


class VictimaDetalle(BaseModel):
    """Detalle completo de una víctima"""
    nombre: str
    menciones: int
    documentos: List[Dict[str, Any]]
    analisis_ia: Optional[str] = None


class VictimasResponse(BaseModel):
    """Respuesta de listado de víctimas paginado"""
    victimas: List[Victima]
    total: int
    page: int
    page_size: int
    total_pages: int


# ==================== MODELOS DE DOCUMENTOS ====================

class DocumentoMetadatos(BaseModel):
    """Metadatos completos de un documento"""
    archivo: str
    nuc: Optional[str] = None
    fecha: Optional[str] = None
    despacho: Optional[str] = None
    tipo_documental: Optional[str] = None
    serie: Optional[str] = None
    codigo: Optional[str] = None
    analisis_ia: Optional[str] = None
    texto_extraido: Optional[str] = None
    hash_sha256: Optional[str] = None
    cuaderno: Optional[str] = None
    folio_inicial: Optional[int] = None
    folio_final: Optional[int] = None
    subserie: Optional[str] = None
    paginas: Optional[int] = None
    tamano_mb: Optional[float] = None
    estado: Optional[str] = None


# ==================== MODELOS DE CONSULTAS ====================

class ConsultaBDRequest(BaseModel):
    """Request para consulta de base de datos"""
    consulta: str = Field(..., description="Texto de la consulta")
    nuc: Optional[str] = Field(None, description="Número Único de Caso")
    departamento: Optional[str] = Field(None, description="Departamento")
    municipio: Optional[str] = Field(None, description="Municipio")
    tipo_documento: Optional[str] = Field(None, description="Tipo de documento")
    despacho: Optional[str] = Field(None, description="Despacho judicial")
    fecha_inicio: Optional[str] = Field(None, description="Fecha inicio (YYYY-MM-DD)")
    fecha_fin: Optional[str] = Field(None, description="Fecha fin (YYYY-MM-DD)")
    limit_victimas: Optional[int] = Field(100, description="Límite de víctimas")


class ConsultaBDResponse(BaseModel):
    """Respuesta de consulta de base de datos"""
    tipo: str = "bd"
    victimas: List[Victima]
    fuentes: List[Dict[str, Any]]
    total_victimas: int
    total_fuentes: int
    tiempo_ms: int
    metadata: Optional[Dict[str, Any]] = None


class ConsultaRAGRequest(BaseModel):
    """Request para consulta RAG (semántica)"""
    consulta: str = Field(..., description="Pregunta en lenguaje natural")
    contexto_conversacional: Optional[str] = Field(None, description="Contexto previo")
    top_k: Optional[int] = Field(5, description="Número de documentos a recuperar")


class ConsultaRAGResponse(BaseModel):
    """Respuesta de consulta RAG"""
    tipo: str = "rag"
    respuesta: str
    fuentes: List[Dict[str, Any]]
    confianza: Optional[float] = None
    tiempo_ms: int
    metadata: Optional[Dict[str, Any]] = None


class ConsultaHibridaRequest(BaseModel):
    """Request para consulta híbrida (BD + RAG)"""
    consulta: str = Field(..., description="Consulta que requiere BD y RAG")
    # Filtros BD
    nuc: Optional[str] = None
    departamento: Optional[str] = None
    municipio: Optional[str] = None
    tipo_documento: Optional[str] = None
    despacho: Optional[str] = None
    fecha_inicio: Optional[str] = None
    fecha_fin: Optional[str] = None
    # Parámetros RAG
    top_k: Optional[int] = Field(5, description="Documentos RAG")


class ConsultaHibridaResponse(BaseModel):
    """Respuesta de consulta híbrida"""
    tipo: str = "hibrida"
    # Resultados BD
    victimas: List[Victima]
    total_victimas: int
    # Resultados RAG
    respuesta_rag: str
    fuentes_rag: List[Dict[str, Any]]
    # Metadata
    tiempo_ms: int
    metadata: Optional[Dict[str, Any]] = None


# ==================== MODELOS DE OPCIONES/FILTROS ====================

class OpcionesFiltrosResponse(BaseModel):
    """Opciones disponibles para filtros"""
    nucs: List[str]
    departamentos: List[str]
    municipios: List[str]
    tipos_documento: List[str]
    despachos: List[str]
    rango_fechas: Dict[str, Optional[str]]  # {"min": "2020-01-01", "max": "2025-12-31"}


# ==================== MODELOS GENERALES ====================

class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    version: str


class ErrorResponse(BaseModel):
    """Respuesta de error estándar"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime
