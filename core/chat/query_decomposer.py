"""
Query Decomposer para Chat de Investigación Judicial

Descompone consultas complejas en pasos simples secuenciales.
Evita queries muy complejos que confundan al LLM o sean ineficientes.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum

from .session_manager import QueryType


class DecompositionStrategy(Enum):
    """Estrategias de descomposición de queries"""
    SEQUENTIAL = "sequential"  # Un paso tras otro
    FILTER_THEN_EXPAND = "filter_then_expand"  # Filtrar primero, luego expandir
    BREADTH_FIRST = "breadth_first"  # Por capas (nivel 1, luego nivel 2, etc.)


@dataclass
class QueryStep:
    """Un paso individual en la descomposición de una consulta"""
    step_number: int
    description: str
    query_type: QueryType
    depends_on_previous: bool  # ¿Usa resultado del paso anterior?
    cypher_template: Optional[str] = None
    expected_output: str = ""  # Descripción de lo que debería retornar


class QueryDecomposer:
    """
    Descompone consultas complejas en pasos simples.

    Ejemplo de descomposición:

    Query original: "Muéstrame todas las personas relacionadas con Jorge Caicedo que
    aparecen en documentos de 1985 y sus vínculos con la Unión Patriótica"

    Descomposición:
    1. Buscar "Jorge Caicedo" en el grafo
    2. Obtener personas relacionadas con Jorge Caicedo
    3. Filtrar documentos de 1985 donde aparecen esas personas
    4. Obtener vínculos de esas personas con "Unión Patriótica"
    """

    def __init__(self):
        self.decomposition_patterns = self._load_patterns()

    def _load_patterns(self) -> Dict[str, List[QueryStep]]:
        """
        Patrones pre-definidos de descomposición para consultas comunes.

        En producción, estos patrones pueden aprenderse con ML o definirse
        por los usuarios.
        """
        return {
            # Patrón: Buscar persona → Ver relaciones
            "persona_y_relaciones": [
                QueryStep(
                    step_number=1,
                    description="Buscar persona por nombre",
                    query_type=QueryType.BUSCAR_PERSONA,
                    depends_on_previous=False,
                    cypher_template="MATCH (p:Persona {{nombre: '{nombre}'}}) RETURN p",
                    expected_output="Nodo de persona encontrado"
                ),
                QueryStep(
                    step_number=2,
                    description="Obtener relaciones de la persona",
                    query_type=QueryType.RELACIONES,
                    depends_on_previous=True,
                    cypher_template="MATCH (p:Persona {{nombre: '{nombre}'}})-[r]->(p2) RETURN r, p2 LIMIT 50",
                    expected_output="Lista de relaciones y personas conectadas"
                )
            ],

            # Patrón: Buscar persona → Documentos → Relaciones en esos documentos
            "persona_docs_y_contexto": [
                QueryStep(
                    step_number=1,
                    description="Buscar persona por nombre",
                    query_type=QueryType.BUSCAR_PERSONA,
                    depends_on_previous=False
                ),
                QueryStep(
                    step_number=2,
                    description="Obtener documentos donde aparece",
                    query_type=QueryType.DOCUMENTOS,
                    depends_on_previous=True,
                    expected_output="Lista de documentos"
                ),
                QueryStep(
                    step_number=3,
                    description="Obtener otras personas mencionadas en esos documentos",
                    query_type=QueryType.RELACIONES,
                    depends_on_previous=True,
                    expected_output="Personas co-mencionadas"
                )
            ],

            # Patrón: Filtro temporal → Estadísticas
            "periodo_y_estadisticas": [
                QueryStep(
                    step_number=1,
                    description="Filtrar documentos por período",
                    query_type=QueryType.DOCUMENTOS,
                    depends_on_previous=False,
                    expected_output="Documentos del período"
                ),
                QueryStep(
                    step_number=2,
                    description="Calcular estadísticas del período",
                    query_type=QueryType.ESTADISTICAS,
                    depends_on_previous=True,
                    expected_output="Conteos y agregaciones"
                )
            ],

            # Patrón: Organización → Miembros → Red de relaciones
            "organizacion_y_red": [
                QueryStep(
                    step_number=1,
                    description="Buscar organización",
                    query_type=QueryType.BUSCAR_PERSONA,  # En AGE, organizaciones son nodos Persona
                    depends_on_previous=False
                ),
                QueryStep(
                    step_number=2,
                    description="Obtener miembros de la organización",
                    query_type=QueryType.RELACIONES,
                    depends_on_previous=True,
                    cypher_template="MATCH (p:Persona)-[:MIEMBRO_DE]->(org:Persona {{nombre: '{nombre}'}}) RETURN p LIMIT 100",
                    expected_output="Lista de miembros"
                ),
                QueryStep(
                    step_number=3,
                    description="Obtener red de relaciones entre miembros",
                    query_type=QueryType.RELACIONES,
                    depends_on_previous=True,
                    expected_output="Relaciones entre miembros"
                )
            ]
        }

    def decompose(self, query_text: str, context_entities: List[str] = None) -> List[QueryStep]:
        """
        Descompone una consulta en pasos simples.

        Args:
            query_text: Texto de la consulta del usuario
            context_entities: Entidades del contexto actual (última consulta)

        Returns:
            Lista de pasos de consulta
        """
        query_lower = query_text.lower()

        # Si usa referencias contextuales ("sus relaciones", "ver más", etc.)
        if self._is_contextual_query(query_text) and context_entities:
            return self._decompose_contextual_query(query_text, context_entities)

        # Detectar patrón basado en keywords
        pattern = self._detect_pattern(query_text)
        if pattern:
            return self.decomposition_patterns.get(pattern, [])

        # Fallback: query simple sin descomposición
        return [
            QueryStep(
                step_number=1,
                description=query_text,
                query_type=self._infer_query_type(query_text),
                depends_on_previous=False
            )
        ]

    def _is_contextual_query(self, query_text: str) -> bool:
        """Detecta si la query hace referencia al contexto anterior"""
        contextual_keywords = [
            "sus", "su", "esa persona", "ese", "esos",
            "más", "detalle", "expandir", "profundizar",
            "relaciones", "vínculos", "conexiones"
        ]
        query_lower = query_text.lower()
        return any(keyword in query_lower for keyword in contextual_keywords)

    def _decompose_contextual_query(self, query_text: str, context_entities: List[str]) -> List[QueryStep]:
        """
        Descompone query contextual (usa entidades del contexto anterior).

        Ejemplo:
        - Contexto: ["Jorge Caicedo"]
        - Query: "ver sus relaciones"
        - Resultado: Query de relaciones para "Jorge Caicedo"
        """
        entity = context_entities[0] if context_entities else None

        if not entity:
            return []

        # Detectar tipo de query contextual
        if any(word in query_text.lower() for word in ["relacion", "vínculo", "conexion"]):
            return [
                QueryStep(
                    step_number=1,
                    description=f"Obtener relaciones de {entity}",
                    query_type=QueryType.RELACIONES,
                    depends_on_previous=True,
                    expected_output="Relaciones de la entidad del contexto"
                )
            ]
        elif any(word in query_text.lower() for word in ["documento", "archivo", "expediente"]):
            return [
                QueryStep(
                    step_number=1,
                    description=f"Obtener documentos de {entity}",
                    query_type=QueryType.DOCUMENTOS,
                    depends_on_previous=True,
                    expected_output="Documentos donde aparece la entidad"
                )
            ]

        return []

    def _detect_pattern(self, query_text: str) -> Optional[str]:
        """
        Detecta el patrón de descomposición basado en keywords.

        Returns:
            Nombre del patrón o None si no se detecta
        """
        query_lower = query_text.lower()

        # Patrón: Persona y relaciones
        if ("quien es" in query_lower or "buscar" in query_lower) and \
           ("relacion" in query_lower or "vínculo" in query_lower):
            return "persona_y_relaciones"

        # Patrón: Persona, documentos y contexto
        if ("documento" in query_lower or "expediente" in query_lower) and \
           ("relacion" in query_lower or "contexto" in query_lower):
            return "persona_docs_y_contexto"

        # Patrón: Período y estadísticas
        if any(year in query_lower for year in ["198", "199", "200"]) and \
           ("cuántos" in query_lower or "estadística" in query_lower):
            return "periodo_y_estadisticas"

        # Patrón: Organización y red
        if ("organización" in query_lower or "partido" in query_lower) and \
           ("miembro" in query_lower or "red" in query_lower):
            return "organizacion_y_red"

        return None

    def _infer_query_type(self, query_text: str) -> QueryType:
        """
        Infiere el tipo de consulta basado en keywords.

        Args:
            query_text: Texto de la consulta

        Returns:
            QueryType inferido
        """
        query_lower = query_text.lower()

        if any(word in query_lower for word in ["quien", "buscar", "encontrar", "nombre"]):
            return QueryType.BUSCAR_PERSONA
        elif any(word in query_lower for word in ["relacion", "vínculo", "conexion", "enlace"]):
            return QueryType.RELACIONES
        elif any(word in query_lower for word in ["documento", "archivo", "expediente", "pdf"]):
            return QueryType.DOCUMENTOS
        elif any(word in query_lower for word in ["cuántos", "estadística", "total", "conteo"]):
            return QueryType.ESTADISTICAS

        return QueryType.BUSCAR_PERSONA  # Default

    def should_decompose(self, query_text: str) -> bool:
        """
        Determina si una consulta debería descomponerse.

        Consultas simples no necesitan descomposición.
        """
        complexity_indicators = [
            " y ",  # Conjunción
            " que ",  # Filtro/condición
            " con ",  # Relación
            ",",  # Múltiples criterios
        ]

        query_lower = query_text.lower()
        complexity_score = sum(1 for indicator in complexity_indicators if indicator in query_lower)

        return complexity_score >= 2

    def get_step_dependencies(self, steps: List[QueryStep]) -> Dict[int, List[int]]:
        """
        Obtiene dependencias entre pasos.

        Returns:
            Dict donde key=step_number, value=lista de steps de los que depende
        """
        dependencies = {}
        for step in steps:
            if step.depends_on_previous and step.step_number > 1:
                dependencies[step.step_number] = [step.step_number - 1]
            else:
                dependencies[step.step_number] = []
        return dependencies
