"""
Modelos de datos para el sistema de consultas jurídicas
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime

class QueryType(Enum):
    """Tipos de consulta disponibles"""
    DATABASE = "database"
    RAG = "rag"
    HYBRID = "hybrid"

class ConfidenceLevel(Enum):
    """Niveles de confianza"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

@dataclass
class QueryRequest:
    """Solicitud de consulta del usuario"""
    text: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    filters: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class Source:
    """Fuente de información utilizada"""
    type: str  # "database", "document", "azure_search"
    identifier: str  # ID, filename, etc.
    relevance_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class QueryResponse:
    """Respuesta unificada del sistema"""
    # Información básica
    query_id: str
    original_query: str
    method_used: QueryType
    
    # Resultados
    answer: str
    confidence: float
    
    # Metadatos de ejecución
    execution_time_ms: int
    tokens_used: Optional[int] = None
    cost_estimate: Optional[float] = None
    
    # Fuentes y trazabilidad
    sources: List[Source] = field(default_factory=list)
    
    # Datos estructurados (para consultas BD)
    structured_data: Optional[List[Dict[str, Any]]] = None
    
    # Contexto adicional
    suggested_followups: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # Timestamp
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class DatabaseResult:
    """Resultado específico de consulta a base de datos"""
    query_sql: str
    rows: List[Dict[str, Any]]
    total_count: int
    execution_time_ms: int
    query_type: str  # "victims", "responsibles", "organizations", etc.

@dataclass
class RAGResult:
    """Resultado específico de consulta RAG"""
    answer: str
    context_used: str
    confidence_score: float
    tokens_used: int
    sources: List[Source]
    embedding_time_ms: int
    generation_time_ms: int

@dataclass
class SearchFilter:
    """Filtros para búsquedas"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    document_type: Optional[str] = None
    department: Optional[str] = None
    municipality: Optional[str] = None
    nuc: Optional[str] = None
    entity_types: List[str] = field(default_factory=list)
