"""
Interfaz base para servicios de consulta
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from .models import QueryRequest, QueryResponse, SearchFilter

class BaseQueryService(ABC):
    """Interfaz base para todos los servicios de consulta"""
    
    @abstractmethod
    async def process_query(self, request: QueryRequest) -> QueryResponse:
        """Procesar una consulta y devolver respuesta"""
        pass
    
    @abstractmethod
    def is_capable(self, query_text: str) -> float:
        """
        Determinar si este servicio puede manejar la consulta
        Returns: Score de 0.0 a 1.0 indicando capacidad
        """
        pass
    
    @abstractmethod
    def get_service_info(self) -> Dict[str, Any]:
        """Información sobre las capacidades del servicio"""
        pass

class DatabaseQueryService(BaseQueryService):
    """Interfaz específica para servicios de base de datos"""
    
    @abstractmethod
    def execute_sql_query(self, sql: str, params: List[Any] = None) -> List[Dict[str, Any]]:
        """Ejecutar consulta SQL directa"""
        pass
    
    @abstractmethod
    def get_specialized_queries(self) -> List[str]:
        """Obtener lista de consultas especializadas disponibles"""
        pass

class RAGQueryService(BaseQueryService):
    """Interfaz específica para servicios RAG"""
    
    @abstractmethod
    async def search_documents(self, query: str, filters: SearchFilter = None) -> List[Dict[str, Any]]:
        """Buscar documentos relevantes"""
        pass
    
    @abstractmethod
    async def generate_response(self, query: str, context: str) -> str:
        """Generar respuesta basada en contexto"""
        pass
