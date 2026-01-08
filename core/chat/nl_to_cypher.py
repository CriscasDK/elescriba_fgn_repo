"""
Natural Language to Cypher Converter
Convierte consultas en lenguaje natural a queries Cypher para Apache AGE
"""

import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json
from openai import AzureOpenAI

from .session_manager import QueryType, QueryResult
from .query_decomposer import QueryStep


@dataclass
class CypherQuery:
    """Query Cypher generada"""
    cypher: str
    parameters: Dict[str, Any]
    query_type: QueryType
    explanation: str  # Explicación de lo que hace el query
    confidence: float  # 0.0 a 1.0


class NLToCypherConverter:
    """
    Convierte lenguaje natural a Cypher usando Azure OpenAI.

    Ejemplos de conversión:

    NL: "Buscar Jorge Caicedo"
    Cypher: MATCH (p:Persona {nombre: 'Jorge Caicedo'}) RETURN p

    NL: "Ver relaciones de Jorge Caicedo"
    Cypher: MATCH (p:Persona {nombre: 'Jorge Caicedo'})-[r]->(p2) RETURN p, r, p2 LIMIT 50

    NL: "Documentos de 1985"
    Cypher: MATCH (d:Documento) WHERE d.anio = 1985 RETURN d LIMIT 100
    """

    def __init__(self, initialize_llm: bool = True):
        # Azure OpenAI client (opcional para tests)
        self.client = None
        if initialize_llm:
            api_key = os.getenv("AZURE_OPENAI_API_KEY")
            endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")

            if api_key and endpoint:
                self.client = AzureOpenAI(
                    api_key=api_key,
                    api_version="2024-02-15-preview",
                    azure_endpoint=endpoint
                )

        self.model = "gpt-4-1106-preview"

        # Esquema del grafo (nodos y relaciones disponibles)
        self.graph_schema = self._load_graph_schema()

        # Ejemplos de conversión para few-shot learning
        self.examples = self._load_examples()

    def _load_graph_schema(self) -> Dict[str, Any]:
        """
        Carga el esquema del grafo (nodos y relaciones disponibles).

        En producción, esto debería obtenerse dinámicamente del grafo.
        """
        return {
            "node_types": [
                {
                    "label": "Persona",
                    "properties": ["nombre", "nombre_normalizado", "tipo", "descripcion"],
                    "description": "Personas, organizaciones, lugares mencionados en documentos"
                },
                {
                    "label": "Documento",
                    "properties": ["id", "titulo", "anio", "mes", "dia", "contenido"],
                    "description": "Documentos judiciales"
                }
            ],
            "relationship_types": [
                "MIEMBRO_DE", "HIJO", "ESPOSA", "ESPOSO", "VICTIMA_DE",
                "TESTIGO_DE", "ACUSADO_DE", "DENUNCIANTE_DE", "COLABORADOR_DE",
                "MENCIONADO_EN", "RELACIONADO_CON", "PERTENECE_A"
            ],
            "common_patterns": [
                "MATCH (p:Persona) WHERE p.nombre CONTAINS 'X' RETURN p",
                "MATCH (p:Persona {nombre: 'X'})-[r]->(p2) RETURN p, r, p2",
                "MATCH (p:Persona)-[:MENCIONADO_EN]->(d:Documento) WHERE d.anio = X RETURN p, d",
                "MATCH (p:Persona)-[:MIEMBRO_DE]->(org:Persona) RETURN p, org"
            ]
        }

    def _load_examples(self) -> List[Dict[str, str]]:
        """
        Ejemplos de conversión para few-shot learning.

        El LLM aprenderá de estos ejemplos para generar queries similares.
        """
        return [
            {
                "nl": "Buscar Jorge Caicedo",
                "cypher": "MATCH (p:Persona) WHERE p.nombre CONTAINS 'Jorge Caicedo' RETURN p LIMIT 10",
                "explanation": "Busca personas cuyo nombre contenga 'Jorge Caicedo'"
            },
            {
                "nl": "Ver relaciones de Jorge Caicedo",
                "cypher": "MATCH (p:Persona {nombre: 'Jorge Caicedo'})-[r]->(p2) RETURN p, type(r) as relacion, p2 LIMIT 50",
                "explanation": "Obtiene todas las relaciones salientes de Jorge Caicedo"
            },
            {
                "nl": "Documentos de 1985",
                "cypher": "MATCH (d:Documento) WHERE d.anio = 1985 RETURN d ORDER BY d.mes, d.dia LIMIT 100",
                "explanation": "Obtiene documentos del año 1985 ordenados por fecha"
            },
            {
                "nl": "Miembros de la Unión Patriótica",
                "cypher": "MATCH (p:Persona)-[:MIEMBRO_DE]->(org:Persona {nombre: 'Unión Patriótica'}) RETURN p LIMIT 100",
                "explanation": "Obtiene personas que son miembros de la Unión Patriótica"
            },
            {
                "nl": "Personas mencionadas en documentos de 1985",
                "cypher": "MATCH (p:Persona)-[:MENCIONADO_EN]->(d:Documento) WHERE d.anio = 1985 RETURN DISTINCT p, count(d) as num_docs ORDER BY num_docs DESC LIMIT 50",
                "explanation": "Obtiene personas mencionadas en documentos de 1985, ordenadas por frecuencia"
            },
            {
                "nl": "Red de relaciones de Jorge Caicedo hasta 2 niveles",
                "cypher": "MATCH path = (p:Persona {nombre: 'Jorge Caicedo'})-[*1..2]-(p2) RETURN path LIMIT 100",
                "explanation": "Obtiene red de relaciones de Jorge Caicedo hasta 2 niveles de profundidad"
            },
            {
                "nl": "Contar documentos por año",
                "cypher": "MATCH (d:Documento) RETURN d.anio as anio, count(d) as total ORDER BY anio",
                "explanation": "Cuenta documentos agrupados por año"
            },
            {
                "nl": "Personas relacionadas con Jorge Caicedo que también están en la Unión Patriótica",
                "cypher": "MATCH (p1:Persona {nombre: 'Jorge Caicedo'})-[r]-(p2:Persona)-[:MIEMBRO_DE]->(org:Persona {nombre: 'Unión Patriótica'}) RETURN DISTINCT p2, type(r) as relacion LIMIT 50",
                "explanation": "Encuentra personas relacionadas con Jorge Caicedo que son miembros de la Unión Patriótica"
            }
        ]

    def convert(self,
                query_text: str,
                query_type: Optional[QueryType] = None,
                context_entities: List[str] = None) -> CypherQuery:
        """
        Convierte lenguaje natural a Cypher.

        Args:
            query_text: Texto de la consulta en lenguaje natural
            query_type: Tipo de consulta (opcional, para mejorar precisión)
            context_entities: Entidades del contexto (para queries contextuales)

        Returns:
            CypherQuery generada
        """
        # Reemplazar referencias contextuales con entidades concretas
        if context_entities:
            query_text = self._resolve_contextual_references(query_text, context_entities)

        # Construir prompt para LLM
        prompt = self._build_prompt(query_text, query_type)

        # Llamar a Azure OpenAI
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,  # Determinístico
            max_tokens=500
        )

        # Parsear respuesta
        result = self._parse_llm_response(response.choices[0].message.content)

        # Inferir query type si no se proporcionó
        if not query_type:
            query_type = self._infer_query_type(result['cypher'])

        return CypherQuery(
            cypher=result['cypher'],
            parameters=result.get('parameters', {}),
            query_type=query_type,
            explanation=result.get('explanation', ''),
            confidence=result.get('confidence', 0.8)
        )

    def _resolve_contextual_references(self, query_text: str, context_entities: List[str]) -> str:
        """
        Reemplaza referencias contextuales con entidades concretas.

        Ejemplo:
        - "sus relaciones" → "relaciones de Jorge Caicedo"
        - "esa persona" → "Jorge Caicedo"
        """
        if not context_entities:
            return query_text

        entity = context_entities[0]

        replacements = {
            "sus relaciones": f"relaciones de {entity}",
            "su red": f"red de {entity}",
            "sus documentos": f"documentos de {entity}",
            "esa persona": entity,
            "ese": entity,
            "esos": entity,
            "su": entity
        }

        result = query_text
        for pattern, replacement in replacements.items():
            if pattern in result.lower():
                result = result.lower().replace(pattern, replacement)

        return result

    def _build_prompt(self, query_text: str, query_type: Optional[QueryType]) -> str:
        """Construye el prompt para el LLM"""
        prompt = f"""Convierte la siguiente consulta en lenguaje natural a un query Cypher para Apache AGE.

CONSULTA: {query_text}

ESQUEMA DEL GRAFO:
- Nodos: {', '.join([nt['label'] for nt in self.graph_schema['node_types']])}
- Relaciones disponibles: {', '.join(self.graph_schema['relationship_types'])}

EJEMPLOS:
"""
        # Agregar ejemplos relevantes
        for example in self.examples[:5]:
            prompt += f"\nNL: {example['nl']}\nCypher: {example['cypher']}\n"

        if query_type:
            prompt += f"\nTIPO DE CONSULTA: {query_type.value}\n"

        prompt += """
INSTRUCCIONES:
1. Genera un query Cypher válido para Apache AGE
2. Usa LIMIT para evitar resultados masivos
3. Para búsquedas por nombre, usa CONTAINS (no =) para ser flexible
4. Retorna el query en formato JSON: {"cypher": "...", "explanation": "...", "confidence": 0.9}
5. La confianza (confidence) debe ser 0.0 a 1.0

RESPUESTA (solo JSON):"""

        return prompt

    def _get_system_prompt(self) -> str:
        """Prompt del sistema para el LLM"""
        return """Eres un experto en convertir lenguaje natural a queries Cypher para Apache AGE.

REGLAS IMPORTANTES:
1. Siempre usa LIMIT para evitar queries masivos
2. Para búsquedas por nombre, usa CONTAINS (case insensitive) en lugar de =
3. Los nodos Persona pueden ser personas, organizaciones o lugares
4. Las relaciones se escriben en mayúsculas con guiones bajos (MIEMBRO_DE, HIJO, etc.)
5. Para fechas, los documentos tienen propiedades: anio, mes, dia
6. Siempre retorna JSON válido con: cypher, explanation, confidence

FORMATO DE RESPUESTA:
{
    "cypher": "MATCH ... RETURN ...",
    "explanation": "Explicación breve",
    "confidence": 0.9
}"""

    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """Parsea la respuesta del LLM"""
        try:
            # Extraer JSON del response (puede venir con texto adicional)
            start = response_text.find('{')
            end = response_text.rfind('}') + 1

            if start == -1 or end == 0:
                raise ValueError("No JSON found in response")

            json_text = response_text[start:end]
            result = json.loads(json_text)

            # Validar campos requeridos
            if 'cypher' not in result:
                raise ValueError("Missing 'cypher' field in response")

            return result

        except Exception as e:
            # Fallback: asumir que todo el response es el query
            return {
                'cypher': response_text.strip(),
                'explanation': 'Query generado',
                'confidence': 0.5
            }

    def _infer_query_type(self, cypher: str) -> QueryType:
        """Infiere el tipo de query del Cypher generado"""
        cypher_lower = cypher.lower()

        if 'count(' in cypher_lower or 'sum(' in cypher_lower or 'avg(' in cypher_lower:
            return QueryType.ESTADISTICAS
        elif 'documento' in cypher_lower:
            return QueryType.DOCUMENTOS
        elif '-[' in cypher_lower or 'relationship' in cypher_lower:
            return QueryType.RELACIONES
        else:
            return QueryType.BUSCAR_PERSONA

    def convert_step(self, step: QueryStep, previous_results: List[Any] = None) -> CypherQuery:
        """
        Convierte un QueryStep en Cypher.

        Si el step tiene cypher_template, lo usa directamente.
        Si no, llama al LLM para generar el query.

        Args:
            step: Paso de consulta a convertir
            previous_results: Resultados del paso anterior (para dependencias)

        Returns:
            CypherQuery generada
        """
        # Si el step ya tiene template, usarlo
        if step.cypher_template:
            # Extraer parámetros del template
            # Por ahora, simplemente retornar el template
            return CypherQuery(
                cypher=step.cypher_template,
                parameters={},
                query_type=step.query_type,
                explanation=step.description,
                confidence=1.0
            )

        # Si no tiene template, usar LLM
        return self.convert(
            query_text=step.description,
            query_type=step.query_type
        )

    def validate_cypher(self, cypher: str) -> tuple[bool, Optional[str]]:
        """
        Valida sintaxis básica del Cypher.

        Returns:
            (is_valid, error_message)
        """
        # Validaciones básicas
        if not cypher.strip():
            return False, "Query vacío"

        cypher_upper = cypher.upper()

        # Debe tener MATCH o RETURN
        if 'MATCH' not in cypher_upper and 'RETURN' not in cypher_upper:
            return False, "Query debe contener MATCH o RETURN"

        # Validar paréntesis balanceados
        if cypher.count('(') != cypher.count(')'):
            return False, "Paréntesis no balanceados"

        if cypher.count('[') != cypher.count(']'):
            return False, "Corchetes no balanceados"

        if cypher.count('{') != cypher.count('}'):
            return False, "Llaves no balanceadas"

        # Warning si no tiene LIMIT (puede retornar muchos resultados)
        if 'LIMIT' not in cypher_upper and 'COUNT' not in cypher_upper:
            # No es error, pero sí warning
            pass

        return True, None
