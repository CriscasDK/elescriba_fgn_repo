"""
Servicio especializado para consultas de base de datos
"""

import time
import logging
import psycopg2
import psycopg2.extras
from typing import List, Dict, Any, Optional
from ..core.base_query_service import DatabaseQueryService
from ..core.models import QueryRequest, QueryResponse, QueryType, DatabaseResult, Source

class PostgreSQLDatabaseService(DatabaseQueryService):
    """Servicio para consultas especializadas en PostgreSQL"""
    
    def __init__(self):
        self.connection = None
        self.specialized_queries = {
            'victims_total': self._query_victims_total,
            'victims_leadership': self._query_victims_leadership,
            'victims_families': self._query_victims_families,
            'responsibles_mentioned': self._query_responsibles_mentioned,
            'documents_with_victims': self._query_documents_with_victims,
            'crimes_against_humanity': self._query_crimes_against_humanity,
            'organizations': self._query_organizations
        }
        self._connect()
    
    def _connect(self):
        """Establecer conexión a PostgreSQL"""
        try:
            self.connection = psycopg2.connect(
                host='localhost',
                port='5432',
                user='docs_user',
                password='docs_password_2025',
                database='documentos_juridicos_gpt4'
            )
            logging.info("✅ Conexión a PostgreSQL establecida")
        except Exception as e:
            logging.error(f"❌ Error conectando a PostgreSQL: {e}")
            raise
    
    def is_capable(self, query_text: str) -> float:
        """Determinar si puede manejar la consulta basándose en palabras clave"""
        query_lower = query_text.lower()
        
        # Palabras clave que indican consulta de BD (datos estructurados)
        db_keywords = [
            'cuántos', 'cuantos', 'cantidad', 'número', 'numero', 'total',
            'listado', 'lista', 'nombres de', 'dame el listado',
            'víctimas', 'victimas', 'responsables', 'organizaciones',
            'documentos mencionan', 'expediente', 'nuc', 'fecha'
        ]
        
        matches = sum(1 for keyword in db_keywords if keyword in query_lower)
        return min(matches / 3.0, 1.0)  # Max score si hay 3+ matches
    
    async def process_query(self, request: QueryRequest) -> QueryResponse:
        """Procesar consulta de base de datos"""
        start_time = time.time()
        
        try:
            # Clasificar tipo de consulta
            query_type = self._classify_query(request.text)
            
            # Ejecutar consulta especializada
            if query_type in self.specialized_queries:
                result = self.specialized_queries[query_type](request.text, request.filters)
            else:
                result = self._execute_general_query(request.text, request.filters)
            
            execution_time = int((time.time() - start_time) * 1000)
            
            # Construir respuesta
            sources = [Source(
                type="database",
                identifier="postgresql_documentos_juridicos",
                relevance_score=1.0,
                metadata={"query_type": query_type, "row_count": len(result.rows)}
            )]
            
            response = QueryResponse(
                query_id=f"db_{int(time.time())}",
                original_query=request.text,
                method_used=QueryType.DATABASE,
                answer=self._format_database_response(result),
                confidence=0.95,  # Alta confianza en datos estructurados
                execution_time_ms=execution_time,
                sources=sources,
                structured_data=result.rows
            )
            
            return response
            
        except Exception as e:
            logging.error(f"Error en consulta BD: {e}")
            raise
    
    def _classify_query(self, query_text: str) -> str:
        """Clasificar el tipo de consulta específica"""
        query_lower = query_text.lower()
        
        if any(word in query_lower for word in ['listado total de victimas', 'dame el listado total']):
            return 'victims_total'
        elif any(word in query_lower for word in ['militante', 'líder', 'sindicalista', 'up']):
            return 'victims_leadership'
        elif any(word in query_lower for word in ['familiares', 'deudos', 'parientes']):
            return 'victims_families'
        elif any(word in query_lower for word in ['responsables más mencionados', 'quienes son los responsables']):
            return 'responsables_mentioned'
        elif any(word in query_lower for word in ['documentos mencionan más víctimas', 'documentos con más víctimas']):
            return 'documents_with_victims'
        elif any(word in query_lower for word in ['crímenes de lesa humanidad', 'crimenes de lesa humanidad']):
            return 'crimes_against_humanity'
        elif any(word in query_lower for word in ['organizaciones', 'grupos']):
            return 'organizations'
        else:
            return 'general'
    
    def _query_victims_total(self, query: str, filters: Dict) -> DatabaseResult:
        """Consulta especializada: Total de víctimas"""
        sql = """
        SELECT 
            p.nombre as nombre_victima,
            p.tipo,
            COUNT(DISTINCT d.id) AS documentos_menciones,
            COUNT(p.id) AS total_menciones,
            STRING_AGG(DISTINCT d.archivo, ' | ') as documentos_lista,
            STRING_AGG(DISTINCT d.nuc, ' | ') as nucs_casos
        FROM personas p
        JOIN documentos d ON p.documento_id = d.id
        WHERE p.tipo = 'victimas'
        AND p.nombre IS NOT NULL 
        AND p.nombre != ''
        AND LENGTH(p.nombre) > 3
        GROUP BY p.nombre, p.tipo
        ORDER BY total_menciones DESC, documentos_menciones DESC
        LIMIT 100
        """
        
        return self._execute_query(sql, [], "victims_total")
    
    def _query_responsables_mentioned(self, query: str, filters: Dict) -> DatabaseResult:
        """Consulta especializada: Responsables más mencionados"""
        sql = """
        SELECT 
            p.nombre as nombre_responsable,
            p.tipo,
            COUNT(DISTINCT d.id) AS documentos_menciones,
            COUNT(p.id) AS total_menciones,
            CASE 
                WHEN p.nombre ~* '\\bfarc\\b|fuerzas armadas revolucionarias' THEN 'FARC'
                WHEN p.nombre ~* '\\bauc\\b|autodefensas|paramilitares' THEN 'PARAMILITARES/AUC'
                WHEN p.nombre ~* 'ejército|ejercito|militar|coronel|general' THEN 'FUERZAS MILITARES'
                WHEN p.nombre ~* 'policía|policia|agente' THEN 'POLICÍA'
                ELSE 'OTROS RESPONSABLES'
            END as categoria_responsable
        FROM personas p
        JOIN documentos d ON p.documento_id = d.id
        WHERE p.tipo = 'victimarios'
        AND p.nombre IS NOT NULL 
        AND LENGTH(p.nombre) > 3
        GROUP BY p.nombre, p.tipo
        HAVING COUNT(DISTINCT d.id) >= 2
        ORDER BY total_menciones DESC
        LIMIT 50
        """
        
        return self._execute_query(sql, [], "responsables_mentioned")
    
    def _execute_query(self, sql: str, params: List, query_type: str) -> DatabaseResult:
        """Ejecutar consulta SQL y devolver resultado estructurado"""
        start_time = time.time()
        
        try:
            cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute(sql, params)
            rows = [dict(row) for row in cursor.fetchall()]
            
            execution_time = int((time.time() - start_time) * 1000)
            
            return DatabaseResult(
                query_sql=sql,
                rows=rows,
                total_count=len(rows),
                execution_time_ms=execution_time,
                query_type=query_type
            )
            
        except Exception as e:
            logging.error(f"Error ejecutando consulta {query_type}: {e}")
            raise
    
    def _format_database_response(self, result: DatabaseResult) -> str:
        """Formatear respuesta de BD para presentación"""
        if not result.rows:
            return "No se encontraron resultados para la consulta."
        
        if result.query_type == 'victims_total':
            return f"Se encontraron {result.total_count} víctimas en la base de datos."
        elif result.query_type == 'responsables_mentioned':
            return f"Se identificaron {result.total_count} responsables principales en los documentos."
        else:
            return f"Consulta ejecutada exitosamente. {result.total_count} resultados encontrados."
    
    def execute_sql_query(self, sql: str, params: List[Any] = None) -> List[Dict[str, Any]]:
        """Ejecutar consulta SQL directa"""
        cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(sql, params or [])
        return [dict(row) for row in cursor.fetchall()]
    
    def get_specialized_queries(self) -> List[str]:
        """Obtener lista de consultas especializadas"""
        return list(self.specialized_queries.keys())
    
    def get_service_info(self) -> Dict[str, Any]:
        """Información del servicio"""
        return {
            "name": "PostgreSQL Database Service",
            "type": "database",
            "capabilities": [
                "Consultas estructuradas de víctimas",
                "Análisis de responsables",
                "Estadísticas documentales",
                "Búsquedas por metadatos"
            ],
            "specialized_queries": len(self.specialized_queries)
        }
    
    # Implementar métodos para otras consultas especializadas...
    def _query_victims_leadership(self, query: str, filters: Dict) -> DatabaseResult:
        """Implementar consulta de víctimas con liderazgo"""
        # TODO: Implementar
        pass
    
    def _query_victims_families(self, query: str, filters: Dict) -> DatabaseResult:
        """Implementar consulta de familiares"""
        # TODO: Implementar
        pass
    
    def _query_documents_with_victims(self, query: str, filters: Dict) -> DatabaseResult:
        """Implementar consulta de documentos con víctimas"""
        # TODO: Implementar
        pass
    
    def _query_crimes_against_humanity(self, query: str, filters: Dict) -> DatabaseResult:
        """Implementar consulta de crímenes de lesa humanidad"""
        # TODO: Implementar
        pass
    
    def _query_organizations(self, query: str, filters: Dict) -> DatabaseResult:
        """Implementar consulta de organizaciones"""
        # TODO: Implementar
        pass
    
    def _execute_general_query(self, query: str, filters: Dict) -> DatabaseResult:
        """Consulta general cuando no hay especializada"""
        # TODO: Implementar lógica general
        return DatabaseResult(
            query_sql="SELECT 'No implementado' as message",
            rows=[{"message": "Consulta general no implementada aún"}],
            total_count=1,
            execution_time_ms=1,
            query_type="general"
        )
