"""
Session Manager para Chat de Investigación Judicial

Maneja sesiones de usuario, contexto de investigación e historial de consultas.
Permite navegación tipo "breadcrumb" para volver a puntos anteriores.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum
import uuid


class QueryType(Enum):
    """Tipos de consulta soportados"""
    BUSCAR_PERSONA = "buscar_persona"
    RELACIONES = "relaciones"
    DOCUMENTOS = "documentos"
    ESTADISTICAS = "estadisticas"
    NAVEGACION = "navegacion"  # Volver a punto anterior
    CONTEXTO = "contexto"  # Usar resultado anterior


@dataclass
class QueryResult:
    """Resultado de una consulta"""
    query_id: str
    query_text: str
    query_type: QueryType
    cypher_query: Optional[str]
    results: Any
    result_count: int
    timestamp: datetime
    execution_time_ms: float

    # Contexto para navegación
    entities_found: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BreadcrumbItem:
    """Item de navegación tipo breadcrumb"""
    query_id: str
    label: str  # Texto corto para mostrar
    timestamp: datetime
    result_summary: str  # Resumen del resultado


class InvestigationSession:
    """
    Sesión de investigación con contexto y historial navegable.

    Ejemplo de uso:
    ```python
    session = InvestigationSession(user_id="abogado_123")

    # Consulta 1
    result1 = QueryResult(...)
    session.add_query_result(result1)

    # Consulta 2 usa contexto de consulta 1
    result2 = QueryResult(...)
    session.add_query_result(result2)

    # Volver a consulta 1
    session.go_to_breadcrumb(result1.query_id)
    ```
    """

    def __init__(self, user_id: str, session_id: Optional[str] = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.user_id = user_id
        self.created_at = datetime.now()
        self.last_activity = datetime.now()

        # Historial de consultas (orden cronológico)
        self.query_history: List[QueryResult] = []

        # Contexto actual (última consulta ejecutada)
        self.current_context: Optional[QueryResult] = None

        # Breadcrumbs (puntos clave de navegación)
        self.breadcrumbs: List[BreadcrumbItem] = []

        # Entidades en foco (se actualizan con cada consulta)
        self.focused_entities: List[str] = []

    def add_query_result(self, result: QueryResult):
        """
        Agrega resultado de consulta al historial y actualiza contexto.

        Args:
            result: Resultado de la consulta ejecutada
        """
        self.query_history.append(result)
        self.current_context = result
        self.last_activity = datetime.now()

        # Actualizar entidades en foco
        if result.entities_found:
            self.focused_entities = result.entities_found[:5]  # Max 5 entidades

        # Crear breadcrumb si es consulta significativa
        if result.result_count > 0 and result.query_type != QueryType.CONTEXTO:
            self._add_breadcrumb(result)

    def _add_breadcrumb(self, result: QueryResult):
        """Agrega punto de navegación al historial de breadcrumbs"""
        # Generar label descriptivo
        if result.query_type == QueryType.BUSCAR_PERSONA:
            label = f"🔍 {result.entities_found[0] if result.entities_found else 'Búsqueda'}"
        elif result.query_type == QueryType.RELACIONES:
            label = f"🔗 Relaciones ({result.result_count})"
        elif result.query_type == QueryType.DOCUMENTOS:
            label = f"📄 Documentos ({result.result_count})"
        else:
            label = f"{result.query_type.value} ({result.result_count})"

        # Generar resumen
        summary = f"{result.result_count} resultado{'s' if result.result_count != 1 else ''}"

        breadcrumb = BreadcrumbItem(
            query_id=result.query_id,
            label=label,
            timestamp=result.timestamp,
            result_summary=summary
        )

        self.breadcrumbs.append(breadcrumb)

    def go_to_breadcrumb(self, query_id: str) -> Optional[QueryResult]:
        """
        Navega a un punto anterior del historial.

        Args:
            query_id: ID de la consulta a la que volver

        Returns:
            QueryResult si se encuentra, None si no existe
        """
        for result in self.query_history:
            if result.query_id == query_id:
                self.current_context = result
                self.focused_entities = result.entities_found
                self.last_activity = datetime.now()
                return result
        return None

    def get_context_entities(self) -> List[str]:
        """Obtiene entidades del contexto actual"""
        if self.current_context:
            return self.current_context.entities_found
        return []

    def get_breadcrumb_trail(self) -> List[str]:
        """
        Obtiene el trail de breadcrumbs como lista de labels.

        Returns:
            Lista de labels de breadcrumbs
        """
        return [b.label for b in self.breadcrumbs]

    def get_last_query(self) -> Optional[QueryResult]:
        """Obtiene la última consulta ejecutada"""
        return self.query_history[-1] if self.query_history else None

    def clear_context(self):
        """Limpia el contexto actual (empezar investigación nueva)"""
        self.current_context = None
        self.focused_entities = []
        self.breadcrumbs = []

    def get_session_summary(self) -> Dict[str, Any]:
        """
        Obtiene resumen de la sesión actual.

        Returns:
            Dict con estadísticas de la sesión
        """
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'total_queries': len(self.query_history),
            'breadcrumbs': self.get_breadcrumb_trail(),
            'focused_entities': self.focused_entities,
            'current_context_id': self.current_context.query_id if self.current_context else None
        }


class SessionStore:
    """
    Store global de sesiones activas.

    En producción, esto debería ser una base de datos o cache (Redis).
    """

    def __init__(self):
        self.sessions: Dict[str, InvestigationSession] = {}

    def get_or_create_session(self, user_id: str, session_id: Optional[str] = None) -> InvestigationSession:
        """Obtiene sesión existente o crea una nueva"""
        if session_id and session_id in self.sessions:
            return self.sessions[session_id]

        # Crear nueva sesión
        session = InvestigationSession(user_id=user_id, session_id=session_id)
        self.sessions[session.session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[InvestigationSession]:
        """Obtiene sesión por ID"""
        return self.sessions.get(session_id)

    def delete_session(self, session_id: str):
        """Elimina sesión"""
        if session_id in self.sessions:
            del self.sessions[session_id]

    def get_active_sessions_count(self) -> int:
        """Obtiene cantidad de sesiones activas"""
        return len(self.sessions)


# Singleton global para el store de sesiones
session_store = SessionStore()
