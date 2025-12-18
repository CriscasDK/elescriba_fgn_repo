"""
Context Graph Builder
Genera grafos 3D basados en el contexto de consultas RAG+BD

Este módulo extrae entidades de las respuestas y construye grafos relevantes.
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Set

# Agregar path raíz al sys.path
root_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_path))

from config.constants import ENTIDADES_NO_PERSONAS


class ContextGraphBuilder:
    """
    Construye grafos contextuales desde respuestas de consultas.

    Workflow:
    1. Recibe respuesta RAG/BD con entidades mencionadas
    2. Extrae nombres propios y entidades clave
    3. Genera consulta de grafo con esas entidades
    4. Retorna datos listos para visualizar
    """

    def __init__(self):
        """Inicializa el builder"""
        self.entidades_no_personas = set(ENTIDADES_NO_PERSONAS)

        # Palabras clave que indican entidades importantes
        self.keywords_organizaciones = [
            'unión patriótica', 'up', 'farc', 'eln', 'ejército', 'policía',
            'fiscalía', 'partido', 'sindicato', 'comité', 'frente', 'bloque'
        ]

        self.keywords_lugares = [
            'departamento', 'municipio', 'vereda', 'corregimiento', 'región'
        ]

    def extract_entities_from_response(self,
                                      respuesta_ia: str,
                                      victimas: List[Dict] = None,
                                      fuentes: List[Dict] = None) -> Dict[str, List[str]]:
        """
        Extrae entidades relevantes de una respuesta completa.

        Args:
            respuesta_ia: Texto de respuesta IA
            victimas: Lista de víctimas del resultado BD
            fuentes: Lista de fuentes/documentos

        Returns:
            Dict con entidades categorizadas:
            {
                'personas': [...],
                'organizaciones': [...],
                'lugares': [...],
                'todas': [...]  # Union de todas
            }
        """
        entidades = {
            'personas': [],
            'organizaciones': [],
            'lugares': [],
            'todas': []
        }

        # 1. Extraer de víctimas (prioridad más alta)
        # Ordenar por menciones si existe ese campo
        if victimas:
            # Ordenar por menciones descendente
            victimas_ordenadas = sorted(
                victimas,
                key=lambda v: v.get('menciones', 0),
                reverse=True
            )
            # Tomar top 20 más mencionadas
            for victima in victimas_ordenadas[:20]:
                nombre = victima.get('nombre', '')
                if nombre and self._is_valid_entity_name(nombre):
                    entidades['personas'].append(nombre)

        # 2. Extraer nombres propios del texto de respuesta IA
        if respuesta_ia:
            nombres_propios = self._extract_proper_names(respuesta_ia)
            for nombre in nombres_propios[:20]:  # Limitar a top 20
                if self._is_valid_entity_name(nombre):
                    # Clasificar según contexto
                    nombre_lower = nombre.lower()

                    if any(kw in nombre_lower for kw in self.keywords_organizaciones):
                        entidades['organizaciones'].append(nombre)
                    elif any(kw in nombre_lower for kw in self.keywords_lugares):
                        entidades['lugares'].append(nombre)
                    else:
                        entidades['personas'].append(nombre)

        # 3. Extraer de fuentes
        if fuentes:
            for fuente in fuentes[:5]:  # Limitar a top 5
                # Buscar menciones de personas en contenido de fuente
                contenido = fuente.get('contenido', '') or fuente.get('texto_chunk', '')
                if contenido:
                    nombres = self._extract_proper_names(contenido)
                    for nombre in nombres[:5]:  # Solo top 5 por fuente
                        if self._is_valid_entity_name(nombre):
                            entidades['personas'].append(nombre)

        # 4. Deduplicar manteniendo orden
        entidades['personas'] = list(dict.fromkeys(entidades['personas']))[:20]  # Max 20
        entidades['organizaciones'] = list(dict.fromkeys(entidades['organizaciones']))[:10]  # Max 10
        entidades['lugares'] = list(dict.fromkeys(entidades['lugares']))[:10]  # Max 10

        # Union de todas
        entidades['todas'] = (
            entidades['personas'] +
            entidades['organizaciones'] +
            entidades['lugares']
        )[:30]  # Máximo 30 entidades totales para mejor visualización

        return entidades

    def _extract_proper_names(self, text: str) -> List[str]:
        """
        Extrae nombres propios del texto.

        Regex: Palabras que empiezan con mayúscula (2+ palabras).
        """
        if not text or len(text) < 10:
            return []

        # Patrón: 2-5 palabras capitalizadas seguidas
        pattern = r'\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,4}\b'
        matches = re.findall(pattern, text)

        return matches

    def _is_valid_entity_name(self, nombre: str) -> bool:
        """
        Valida si un nombre es una entidad válida.

        Filtra:
        - Nombres muy cortos
        - Palabras comunes (de, la, el, etc.)
        - Entidades no-personas de config
        """
        if not nombre or len(nombre) < 3:
            return False

        nombre_lower = nombre.lower()

        # Filtrar palabras comunes
        palabras_comunes = {
            'de', 'la', 'el', 'los', 'las', 'del', 'al', 'con', 'por', 'para',
            'en', 'un', 'una', 'este', 'esta', 'ese', 'esa', 'aquel', 'aquella'
        }

        if nombre_lower in palabras_comunes:
            return False

        # Filtrar entidades no-personas de config
        if nombre_lower in self.entidades_no_personas:
            return False

        # Filtrar fechas y números
        if re.match(r'^\d+$', nombre):
            return False

        return True

    def build_graph_query_params(self,
                                 entidades: Dict[str, List[str]],
                                 max_nodes: int = 50,
                                 include_neighborhood: bool = True) -> Dict[str, Any]:
        """
        Construye parámetros para query de grafo.

        Args:
            entidades: Dict con entidades extraídas
            max_nodes: Máximo de nodos en el grafo
            include_neighborhood: Si incluir vecindarios

        Returns:
            Dict con parámetros para AGEGraphAdapter
        """
        nombres_buscar = entidades.get('todas', [])

        if not nombres_buscar:
            return {
                'nombres': [],
                'max_nodes': 0,
                'include_neighborhood': False,
                'title': 'Sin entidades para graficar'
            }

        return {
            'nombres': nombres_buscar[:15],  # Limitar a 15 entidades principales
            'max_nodes': max_nodes,
            'include_neighborhood': include_neighborhood,
            'title': f"Red de Relaciones: {', '.join(nombres_buscar[:3])}{'...' if len(nombres_buscar) > 3 else ''}"
        }

    def build_contextual_graph(self,
                              respuesta_ia: str = None,
                              victimas: List[Dict] = None,
                              fuentes: List[Dict] = None,
                              max_nodes: int = 50) -> Dict[str, Any]:
        """
        Construye un grafo contextual completo desde una respuesta.

        Pipeline completo:
        1. Extrae entidades
        2. Genera parámetros de consulta
        3. Prepara datos para visualización

        Args:
            respuesta_ia: Respuesta IA
            victimas: Lista de víctimas
            fuentes: Lista de fuentes
            max_nodes: Máximo de nodos

        Returns:
            Dict con:
            - entidades: Entidades extraídas
            - params: Parámetros para adapter
            - ready: Boolean si está listo para graficar
        """
        # Extraer entidades
        entidades = self.extract_entities_from_response(
            respuesta_ia=respuesta_ia,
            victimas=victimas,
            fuentes=fuentes
        )

        # Construir parámetros
        params = self.build_graph_query_params(
            entidades=entidades,
            max_nodes=max_nodes,
            include_neighborhood=True
        )

        return {
            'entidades': entidades,
            'params': params,
            'ready': len(entidades.get('todas', [])) > 0,
            'entity_count': len(entidades.get('todas', [])),
            'top_entities': entidades.get('todas', [])[:5]
        }

    def should_auto_generate_graph(self,
                                  tipo_consulta: str,
                                  entity_count: int,
                                  consulta_texto: str = "") -> bool:
        """
        Decide si se debe auto-generar el grafo.

        Criterios:
        - Usuario pide explícitamente un grafo/red
        - Consulta RAG con pocas fuentes (análisis cualitativo)
        - NO para consultas BD masivas (listas grandes)
        """
        # Palabras clave que indican solicitud explícita de grafo
        keywords_grafo = [
            'red', 'grafo', 'conexion', 'conexiones', 'relacion', 'relaciones',
            'vinculo', 'vinculos', 'network', 'graph', 'mapa de relaciones',
            'visualiza', 'muestra la red', 'como se relaciona'
        ]

        consulta_lower = consulta_texto.lower()

        # MODO 3: Consulta explícita de grafo
        if any(keyword in consulta_lower for keyword in keywords_grafo):
            return True

        # MODO 1: Consulta RAG con pocas entidades (< 10)
        if tipo_consulta == 'rag' and entity_count >= 2 and entity_count <= 10:
            return True

        # Consulta híbrida que pide patrones/análisis (RAG dominante)
        if tipo_consulta == 'hibrida' and entity_count >= 2 and entity_count <= 10:
            palabras_analisis = ['patron', 'patrones', 'analisis', 'como', 'porque', 'relacion']
            if any(palabra in consulta_lower for palabra in palabras_analisis):
                return True

        # NO auto-generar para listas masivas de BD
        return False


def extract_entities_from_query_result(resultado: Dict[str, Any]) -> Dict[str, Any]:
    """
    Función de conveniencia para extraer entidades de un resultado completo.

    Args:
        resultado: Resultado completo de ejecutar_consulta o ejecutar_consulta_hibrida

    Returns:
        Dict con datos del grafo contextual
    """
    builder = ContextGraphBuilder()

    respuesta_ia = resultado.get('respuesta_ia', '')
    victimas = resultado.get('victimas', [])
    fuentes = resultado.get('fuentes', []) or resultado.get('trazabilidad', [])

    return builder.build_contextual_graph(
        respuesta_ia=respuesta_ia,
        victimas=victimas,
        fuentes=fuentes
    )


def main():
    """Test del módulo"""
    print("🔍 Context Graph Builder - Test")
    print("=" * 60)

    # Simular respuesta de consulta
    respuesta_simulada = {
        'respuesta_ia': """
        La Unión Patriótica fue un partido político colombiano.
        Entre sus miembros destacados estaban Jorge Caicedo y María López.
        Muchos miembros fueron víctimas de violencia en Medellín y Bogotá.
        El Ejército Nacional y las FARC estuvieron involucrados en diferentes eventos.
        """,
        'victimas': [
            {'nombre': 'Jorge Caicedo', 'menciones': 10},
            {'nombre': 'María López', 'menciones': 8},
            {'nombre': 'Pedro Ruiz', 'menciones': 5}
        ],
        'fuentes': [
            {'contenido': 'Documento menciona a Rosa Edith Sierra y Oswaldo Olivo'}
        ]
    }

    # Extraer entidades
    graph_data = extract_entities_from_query_result(respuesta_simulada)

    print("\n✅ Entidades extraídas:")
    print(f"  Total: {graph_data['entity_count']}")
    print(f"  Top entidades: {graph_data['top_entities']}")
    print(f"  Ready to graph: {graph_data['ready']}")

    print("\n📊 Parámetros para grafo:")
    params = graph_data['params']
    print(f"  Nombres a buscar: {params['nombres']}")
    print(f"  Max nodes: {params['max_nodes']}")
    print(f"  Título: {params['title']}")

    print("\n🎯 Clasificación:")
    entidades = graph_data['entidades']
    print(f"  Personas: {entidades['personas']}")
    print(f"  Organizaciones: {entidades['organizaciones']}")
    print(f"  Lugares: {entidades['lugares']}")


if __name__ == "__main__":
    main()
