"""
Adaptador AGE Graph → Formato Visualizador 3D

Convierte datos de Apache AGE al formato estándar del Network3DVisualizer.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import sys
from pathlib import Path

# Imports relativos
from ..age_connector import AGEConnector
from ..config import GraphConfig


@dataclass
class GraphQuery:
    """Define una consulta predefinida al grafo"""
    name: str
    description: str
    cypher: str
    column_definitions: List[str]
    params: Optional[Dict[str, Any]] = None


class AGEGraphAdapter:
    """
    Adaptador que convierte datos de Apache AGE al formato del visualizador 3D.

    Formato estándar esperado por Network3DVisualizer:
    {
        "nodes": [
            {
                "id": str,
                "name": str,
                "type": str,  # persona, organizacion, lugar, documento
                "level": int,  # nivel Z en visualización 3D
                "size": float,
                "weight": float,
                "metadata": dict
            }
        ],
        "edges": [
            {
                "source": str,
                "target": str,
                "type": str,
                "weight": float,
                "metadata": dict
            }
        ],
        "config": {
            "node_colors": dict,
            "edge_colors": dict
        }
    }
    """

    def __init__(self, config: Optional[GraphConfig] = None):
        """
        Inicializa el adaptador.

        Args:
            config: Configuración del grafo AGE
        """
        self.config = config or GraphConfig()
        self.connector = AGEConnector(self.config)

        # Mapeo de tipos a niveles Z
        self.type_to_level = {
            'Documento': 0,
            'Persona': 1,
            'Organizacion': 2,
            'Lugar': 3
        }

        # Colores por tipo
        self.node_colors = {
            'Documento': '#FF6B6B',      # Rojo
            'Persona': '#4ECDC4',         # Turquesa
            'Organizacion': '#45B7D1',    # Azul
            'Lugar': '#96CEB4',           # Verde
            'default': '#888888'
        }

        self.edge_colors = {
            'co_ocurrencia_persona': '#4ECDC4',
            'co_ocurrencia_persona_org': '#96CEB4',
            'co_ocurrencia_org': '#45B7D1',
            'MENCIONADO_EN': '#FF6B6B',
            'UBICADO_EN': '#96CEB4',
            'OPERA_EN': '#45B7D1',
            'PERTENECE_A': '#FFEAA7',
            'default': '#666666'
        }

        # Queries predefinidas
        self.predefined_queries = self._setup_predefined_queries()

    def _setup_predefined_queries(self) -> Dict[str, GraphQuery]:
        """Define consultas predefinidas útiles"""
        return {
            'full_graph': GraphQuery(
                name="Grafo Completo",
                description="Todos los nodos y relaciones",
                cypher="""
                MATCH (n)
                OPTIONAL MATCH (n)-[r]->(m)
                RETURN n, r, m
                """,
                column_definitions=["n agtype", "r agtype", "m agtype"]
            ),
            'top_connected': GraphQuery(
                name="Nodos Más Conectados",
                description="Muestra de nodos conectados (límite 100 aristas)",
                cypher="""
                MATCH (n)-[r]-(m)
                RETURN n, r, m
                LIMIT 100
                """,
                column_definitions=["n agtype", "r agtype", "m agtype"]
            ),
            'personas_y_organizaciones': GraphQuery(
                name="Personas y Organizaciones",
                description="Red de personas y organizaciones conectadas",
                cypher="""
                MATCH (p:Persona)-[r]-(o:Organizacion)
                RETURN p as n, r, o as m
                UNION
                MATCH (p:Persona)-[r]-(p2:Persona)
                RETURN p as n, r, p2 as m
                """,
                column_definitions=["n agtype", "r agtype", "m agtype"]
            ),
            'documentos_recientes': GraphQuery(
                name="Documentos y Menciones",
                description="Documentos con sus entidades mencionadas (límite 100)",
                cypher="""
                MATCH (d:Documento)
                WITH d
                LIMIT 100
                MATCH (n)-[r:VINCULADO {tipo_relacion: 'MENCIONADO_EN'}]->(d)
                RETURN n, r, d as m
                """,
                column_definitions=["n agtype", "r agtype", "m agtype"]
            ),
            'geografia': GraphQuery(
                name="Red Geográfica",
                description="Lugares y entidades ubicadas en ellos",
                cypher="""
                MATCH (n)-[r:VINCULADO]-(l:Lugar)
                WHERE r.tipo_relacion IN ['UBICADO_EN', 'OPERA_EN', 'PERTENECE_A']
                RETURN n, r, l as m
                """,
                column_definitions=["n agtype", "r agtype", "m agtype"]
            )
        }

    def query_entity_neighborhood(self, entity_name: str, depth: int = 2) -> Dict[str, Any]:
        """
        Consulta el vecindario de una entidad específica.

        Args:
            entity_name: Nombre de la entidad
            depth: Profundidad de búsqueda (1-3 saltos)

        Returns:
            Datos en formato visualizador 3D
        """
        cypher = f"""
        MATCH (center)
        WHERE toLower(center.nombre) CONTAINS toLower('{entity_name}')
        WITH center
        LIMIT 1
        MATCH path = (center)-[*1..{depth}]-(connected)
        WITH center, relationships(path) as rels, nodes(path) as nodes_path
        UNWIND rels as r
        MATCH (a)-[r]-(b)
        RETURN DISTINCT a as n, r, b as m
        """

        column_defs = ["n agtype", "r agtype", "m agtype"]
        results = self.connector.execute_cypher(
            cypher,
            graph_name=self.config.graph_name,
            column_definitions=column_defs
        )

        return self._convert_results_to_standard(results, f"Vecindario de '{entity_name}'")

    def execute_predefined_query(self, query_key: str) -> Dict[str, Any]:
        """
        Ejecuta una consulta predefinida.

        Args:
            query_key: Clave de la consulta predefinida

        Returns:
            Datos en formato visualizador 3D
        """
        if query_key not in self.predefined_queries:
            raise ValueError(f"Query '{query_key}' no encontrada. Disponibles: {list(self.predefined_queries.keys())}")

        query = self.predefined_queries[query_key]

        results = self.connector.execute_cypher(
            query.cypher,
            graph_name=self.config.graph_name,
            column_definitions=query.column_definitions,
            parameters=query.params or {}
        )

        return self._convert_results_to_standard(results, query.name)

    def _convert_results_to_standard(self, results: List[Dict], title: str = "Grafo") -> Dict[str, Any]:
        """
        Convierte resultados de AGE al formato estándar del visualizador.

        Args:
            results: Resultados de consulta Cypher
            title: Título de la visualización

        Returns:
            Diccionario con formato estándar
        """
        nodes_dict = {}
        edges_list = []

        for row in results:
            # Extraer nodo origen (n)
            if 'n' in row and row['n']:
                node_data = self._parse_agtype_node(row['n'])
                if node_data and node_data['id'] not in nodes_dict:
                    nodes_dict[node_data['id']] = node_data

            # Extraer nodo destino (m)
            if 'm' in row and row['m']:
                node_data = self._parse_agtype_node(row['m'])
                if node_data and node_data['id'] not in nodes_dict:
                    nodes_dict[node_data['id']] = node_data

            # Extraer relación (r)
            if 'r' in row and row['r']:
                edge_data = self._parse_agtype_edge(row['r'], row.get('n'), row.get('m'))
                if edge_data:
                    edges_list.append(edge_data)

        # Convertir a formato final
        standard_data = {
            "nodes": list(nodes_dict.values()),
            "edges": edges_list,
            "config": {
                "title": title,
                "node_colors": self.node_colors,
                "edge_colors": self.edge_colors
            }
        }

        return standard_data

    def _parse_agtype_node(self, agtype_value: Any) -> Optional[Dict[str, Any]]:
        """Parsea un nodo agtype a formato estándar"""
        try:
            import json
            import re

            # AGE retorna nodos como strings JSON con ::vertex al final
            if isinstance(agtype_value, str):
                # Remover ::vertex suffix
                json_str = agtype_value.replace('::vertex', '').strip()
                node_data = json.loads(json_str)

                node_id = node_data.get('id', 'unknown')
                node_label = node_data.get('label', 'default')
                properties = node_data.get('properties', {})

                nombre = properties.get('nombre') or properties.get('archivo', 'Sin nombre')
                node_type = node_label  # Documento, Persona, Organizacion, Lugar

                # Mapear tipo a nivel Z
                level = self.type_to_level.get(node_type, 0)

                # Calcular tamaño basado en número de documentos
                size = 5.0
                if 'documentos' in properties:
                    docs = properties['documentos']
                    if isinstance(docs, list):
                        size = min(15.0, max(3.0, len(docs) * 2))

                return {
                    "id": str(node_id),
                    "name": nombre,
                    "type": node_type,
                    "level": level,
                    "size": size,
                    "weight": 1.0,
                    "metadata": properties
                }

        except Exception as e:
            print(f"Error parseando nodo: {e} - Valor: {agtype_value}")

        return None

    def _parse_agtype_edge(self, agtype_value: Any, source_node: Any, target_node: Any) -> Optional[Dict[str, Any]]:
        """Parsea una arista agtype a formato estándar"""
        try:
            import json

            # AGE retorna aristas como strings JSON con ::edge al final
            if isinstance(agtype_value, str):
                # Remover ::edge suffix
                json_str = agtype_value.replace('::edge', '').strip()
                edge_data = json.loads(json_str)

                # Parsear nodos para obtener IDs
                source_id = None
                target_id = None

                if isinstance(source_node, str):
                    source_json = source_node.replace('::vertex', '').strip()
                    source_data = json.loads(source_json)
                    source_id = source_data.get('id')

                if isinstance(target_node, str):
                    target_json = target_node.replace('::vertex', '').strip()
                    target_data = json.loads(target_json)
                    target_id = target_data.get('id')

                if not source_id or not target_id:
                    return None

                properties = edge_data.get('properties', {})
                edge_type = properties.get('tipo_relacion', 'default')
                weight = properties.get('fuerza', 0.5)

                return {
                    "source": str(source_id),
                    "target": str(target_id),
                    "type": edge_type,
                    "weight": weight,
                    "metadata": properties
                }

        except Exception as e:
            print(f"Error parseando arista: {e} - Valor: {agtype_value}")

        return None

    def get_available_queries(self) -> List[Dict[str, str]]:
        """Retorna lista de consultas predefinidas disponibles"""
        return [
            {
                "key": key,
                "name": query.name,
                "description": query.description
            }
            for key, query in self.predefined_queries.items()
        ]

    def search_nodes_by_name(self, nombre: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Busca nodos por nombre (búsqueda parcial case-insensitive).

        Args:
            nombre: Nombre o parte del nombre a buscar
            limit: Máximo de resultados

        Returns:
            Lista de nodos encontrados
        """
        # Escapar comillas simples
        nombre_escaped = nombre.replace("'", "\\'")

        # Estrategia 1: Buscar solo en nodos Persona con match exacto primero (más rápido)
        cypher_exact = f"""
        MATCH (n:Persona {{nombre: '{nombre_escaped}'}})
        RETURN n
        LIMIT {limit}
        """

        try:
            results = self.connector.execute_cypher(
                cypher_exact,
                graph_name=self.config.graph_name,
                column_definitions=["n agtype"]
            )

            if results and len(results) > 0:
                nodes = []
                for row in results:
                    node = self._parse_agtype_node(row.get('n'))
                    if node:
                        nodes.append(node)
                if nodes:
                    return nodes
        except Exception:
            pass  # Si falla, continuar con búsqueda case-insensitive

        # Estrategia 2: Búsqueda case-insensitive (preserva grafía original)
        cypher_case_insensitive = f"""
        MATCH (n:Persona)
        WHERE toLower(n.nombre) = toLower('{nombre_escaped}')
        RETURN n
        LIMIT {limit}
        """

        try:
            results = self.connector.execute_cypher(
                cypher_case_insensitive,
                graph_name=self.config.graph_name,
                column_definitions=["n agtype"]
            )

            if results and len(results) > 0:
                nodes = []
                for row in results:
                    node = self._parse_agtype_node(row.get('n'))
                    if node:
                        nodes.append(node)
                if nodes:
                    return nodes
        except Exception:
            pass  # Si falla, continuar con búsqueda parcial

        # Estrategia 3: Búsqueda parcial solo en nodos Persona (más específico)
        cypher_partial = f"""
        MATCH (n:Persona)
        WHERE n.nombre CONTAINS '{nombre_escaped}'
        RETURN n
        LIMIT {limit}
        """

        try:
            results = self.connector.execute_cypher(
                cypher_partial,
                graph_name=self.config.graph_name,
                column_definitions=["n agtype"]
            )

            nodes = []
            for row in results:
                node = self._parse_agtype_node(row.get('n'))
                if node:
                    nodes.append(node)

            return nodes
        except Exception as e:
            print(f"Error en búsqueda de nodos: {e}")
            return []

    def get_node_neighborhood(self, node_id: str, depth: int = 1, max_nodes: int = 50) -> Dict[str, Any]:
        """
        Obtiene el vecindario de un nodo (N saltos).

        Args:
            node_id: ID del nodo central
            depth: Profundidad de búsqueda (1-3)
            max_nodes: Límite de nodos totales

        Returns:
            Subgrafo con vecindario
        """
        depth = min(max(depth, 1), 3)  # Limitar entre 1 y 3

        cypher = f"""
        MATCH (center)
        WHERE id(center) = {node_id}
        MATCH (center)-[relationship]-(neighbor)
        RETURN DISTINCT center as n, relationship as r, neighbor as m
        LIMIT {max_nodes}
        """

        results = self.connector.execute_cypher(
            cypher,
            graph_name=self.config.graph_name,
            column_definitions=["n agtype", "r agtype", "m agtype"]
        )

        return self._convert_results_to_standard(results, f"Vecindario (depth={depth})")

    def find_path_between_nodes(self, node_id_1: str, node_id_2: str, max_depth: int = 5) -> Dict[str, Any]:
        """
        Encuentra el camino más corto entre dos nodos.

        Args:
            node_id_1: ID del primer nodo
            node_id_2: ID del segundo nodo
            max_depth: Profundidad máxima de búsqueda

        Returns:
            Subgrafo con el camino
        """
        cypher = f"""
        MATCH (a), (b)
        WHERE id(a) = {node_id_1} AND id(b) = {node_id_2}
        MATCH path = shortestPath((a)-[*..{max_depth}]-(b))
        WITH nodes(path) as path_nodes, relationships(path) as path_rels
        UNWIND range(0, size(path_rels)-1) as i
        RETURN path_nodes[i] as n, path_rels[i] as r, path_nodes[i+1] as m
        """

        results = self.connector.execute_cypher(
            cypher,
            graph_name=self.config.graph_name,
            column_definitions=["n agtype", "r agtype", "m agtype"]
        )

        return self._convert_results_to_standard(results, "Camino más corto")

    def query_by_entity_names(self, nombres: List[str], include_neighborhood: bool = False, depth: int = 1) -> Dict[str, Any]:
        """
        Consulta contextual basada en nombres de entidades.

        Args:
            nombres: Lista de nombres a buscar
            include_neighborhood: Si incluir vecindario de cada entidad
            depth: Profundidad del vecindario si está activado

        Returns:
            Subgrafo con las entidades y opcionalmente sus vecindarios
        """
        if not nombres:
            return {"nodes": [], "edges": [], "config": {}}

        # Buscar nodos para cada nombre
        nodos_encontrados = []
        for nombre in nombres:
            found = self.search_nodes_by_name(nombre, limit=5)
            nodos_encontrados.extend(found)

        if not nodos_encontrados:
            return {"nodes": [], "edges": [], "config": {}}

        # Obtener IDs
        node_ids = [n['id'] for n in nodos_encontrados]

        # Si solo hay 1 entidad, mostrar su vecindario (o solo el nodo si no tiene vecindario)
        if len(node_ids) == 1:
            neigh_data = self.get_node_neighborhood(node_ids[0], depth=depth)
            # Si no tiene vecindario, al menos mostrar el nodo solo
            if len(neigh_data['nodes']) == 0:
                return {
                    "nodes": nodos_encontrados,
                    "edges": [],
                    "config": {
                        "title": f"Nodo: {nombres[0]}",
                        "node_colors": self.node_colors,
                        "edge_colors": self.edge_colors
                    }
                }
            return neigh_data

        # Si hay 2+ entidades, intentar buscar caminos entre ellas
        all_data = {"nodes": {}, "edges": []}

        # Primero agregar todos los nodos encontrados
        for node in nodos_encontrados:
            all_data['nodes'][node['id']] = node

        # Intentar buscar camino entre cada par (puede fallar si no hay relaciones)
        for i in range(len(node_ids)):
            for j in range(i + 1, len(node_ids)):
                try:
                    path_data = self.find_path_between_nodes(node_ids[i], node_ids[j])

                    # Merge nodes del camino
                    for node in path_data['nodes']:
                        all_data['nodes'][node['id']] = node

                    # Add edges
                    all_data['edges'].extend(path_data['edges'])
                except Exception as e:
                    # Si no hay camino o falla la búsqueda, continuar
                    pass

        # Si include_neighborhood, agregar vecindarios
        if include_neighborhood:
            for node_id in node_ids:
                neigh_data = self.get_node_neighborhood(node_id, depth=depth, max_nodes=20)

                # Merge nodes
                for node in neigh_data['nodes']:
                    all_data['nodes'][node['id']] = node

                # Add edges
                all_data['edges'].extend(neigh_data['edges'])

        return {
            "nodes": list(all_data['nodes'].values()),
            "edges": all_data['edges'],
            "config": {
                "title": f"Relaciones entre {', '.join(nombres[:3])}{'...' if len(nombres) > 3 else ''}",
                "node_colors": self.node_colors,
                "edge_colors": self.edge_colors
            }
        }

    def query_by_entity_names_semantic(self, nombres: List[str], max_nodes: int = 50) -> Dict[str, Any]:
        """
        Búsqueda usando RELACIONES SEMÁNTICAS desde tabla relaciones_extraidas.

        Retorna relaciones reales como VICTIMA_DE, PERPETRADOR, ORGANIZACION, MIEMBRO_DE,
        en lugar de solo co-ocurrencias.

        Args:
            nombres: Lista de nombres a buscar
            max_nodes: Límite de nodos (default 50)

        Returns:
            Grafo en formato estándar del visualizador con relaciones semánticas
        """
        import psycopg2
        import sys
        from pathlib import Path

        # Agregar path del proyecto para imports
        sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
        from core.consultas import get_db_connection

        conn = get_db_connection()
        cur = conn.cursor()

        nodes = {}
        edges = []

        # Buscar relaciones semánticas desde tabla relaciones_extraidas
        # SOLO usar relaciones extraídas con IA (gpt4_from_analisis) para evitar falsos positivos
        for nombre in nombres:
            # Obtener relaciones donde el nombre aparece como origen o destino
            # EXCLUIR instituciones estatales que aparecen como victimarios (son investigadores, no perpetradores)

            # Construir parámetros para la query
            nombre_pattern = f'%{nombre}%'

            # Usar query parametrizada simple (evitar % dentro de strings SQL)
            sql_query = """
                SELECT
                    r.entidad_origen,
                    r.entidad_destino,
                    r.tipo_relacion,
                    r.confianza,
                    COUNT(DISTINCT r.documento_id) as num_documentos
                FROM relaciones_extraidas r
                WHERE (LOWER(r.entidad_origen) LIKE LOWER(%s)
                       OR LOWER(r.entidad_destino) LIKE LOWER(%s))
                  AND r.confianza >= 0.6
                  AND r.metodo_extraccion = 'gpt4_from_analisis'
                  AND NOT (r.tipo_relacion = 'victima_de' AND (
                      LOWER(r.entidad_destino) SIMILAR TO '%%(fiscalía|fiscal|unidad nacional|grupo especial|juzgado|tribunal|procuradur|defensor|medicina legal|sirdec|instituto nacional)%%'
                  ))
                GROUP BY r.entidad_origen, r.entidad_destino, r.tipo_relacion, r.confianza
                ORDER BY r.confianza DESC, num_documentos DESC
                LIMIT %s
            """

            cur.execute(sql_query, (nombre_pattern, nombre_pattern, max_nodes))

            for row in cur.fetchall():
                # Validar que el row tenga 5 elementos antes de unpacking
                if not row or len(row) < 5:
                    print(f"⚠️  Row inválido: {row}")
                    continue

                entidad_origen, entidad_destino, tipo_relacion, confianza, num_docs = row

                # ✅ CLASIFICAR TIPO DE ENTIDAD basado en nombre y relación
                def clasificar_entidad(nombre, es_origen, tipo_rel):
                    """Clasifica entidad según su nombre y contexto"""
                    nombre_lower = nombre.lower()

                    # 1. Entidades ilegales (grupos armados)
                    if any(x in nombre_lower for x in ['auc', 'autodefensas', 'paramilitares', 'farc',
                                                         'eln', 'guerrilla', 'bloque', 'frente']):
                        return 'entidad_ilegal'

                    # 2. Entidades estatales
                    if any(x in nombre_lower for x in ['fiscalía', 'juzgado', 'tribunal', 'policía',
                                                         'ejército', 'defensoría', 'procuraduría',
                                                         'medicina legal', 'sirdec']):
                        return 'entidad_estatal'

                    # 3. Victimario (destino en relación victima_de)
                    if not es_origen and tipo_rel == 'victima_de':
                        return 'victimario'

                    # 4. Familiar (relaciones familiares)
                    if tipo_rel in ['hijo', 'hija', 'hermano', 'hermana', 'esposo', 'esposa',
                                   'padre', 'madre', 'abuelo', 'abuela', 'tio', 'tia', 'primo', 'prima']:
                        return 'familiar'

                    # 5. Víctima (origen en relación victima_de)
                    if es_origen and tipo_rel == 'victima_de':
                        return 'victima'

                    # 6. Por defecto: persona
                    return 'persona'

                # Agregar nodo origen
                if entidad_origen not in nodes:
                    tipo_origen = clasificar_entidad(entidad_origen, True, tipo_relacion)
                    nodes[entidad_origen] = {
                        'id': f"pg_{hash(entidad_origen) % 1000000}",
                        'name': entidad_origen,
                        'type': tipo_origen,
                        'level': 0,
                        'size': 1.5,
                        'weight': float(num_docs),
                        'relations': [tipo_relacion]  # Track relations
                    }
                else:
                    # Actualizar tipo si es más específico
                    nodes[entidad_origen]['relations'].append(tipo_relacion)

                # Agregar nodo destino
                if entidad_destino not in nodes:
                    tipo_destino = clasificar_entidad(entidad_destino, False, tipo_relacion)
                    nodes[entidad_destino] = {
                        'id': f"pg_{hash(entidad_destino) % 1000000}",
                        'name': entidad_destino,
                        'type': tipo_destino,
                        'level': 1,
                        'size': 1.0,
                        'weight': float(num_docs),
                        'relations': [tipo_relacion]  # Track relations
                    }
                else:
                    # Actualizar tipo si es más específico
                    nodes[entidad_destino]['relations'].append(tipo_relacion)

                # Agregar edge con tipo semántico
                edges.append({
                    'source': nodes[entidad_origen]['id'],
                    'target': nodes[entidad_destino]['id'],
                    'type': tipo_relacion.upper(),  # VICTIMA_DE, PERPETRADOR, etc.
                    'weight': float(confianza),
                    'label': f"{tipo_relacion} ({int(confianza*100)}%)",
                    'metadata': {
                        'confianza': float(confianza),
                        'num_documentos': num_docs
                    }
                })

        # Si no encontramos relaciones semánticas, hacer fallback a co-ocurrencias
        if len(edges) == 0:
            print(f"⚠️  No se encontraron relaciones semánticas para {nombres}, usando co-ocurrencias como fallback")
            return self.query_by_entity_names_fast(nombres, max_nodes)

        cur.close()
        conn.close()

        return {
            "nodes": list(nodes.values()),
            "edges": edges,
            "config": {
                "title": f"Red Semántica: {', '.join(nombres[:3])}{'...' if len(nombres) > 3 else ''}",
                "node_colors": self.node_colors,
                "edge_colors": self.edge_colors
            }
        }

    def query_by_entity_names_fast(self, nombres: List[str], max_nodes: int = 50) -> Dict[str, Any]:
        """
        Búsqueda RÁPIDA usando consulta directa a PostgreSQL.

        Busca co-ocurrencias directamente en la tabla personas (sin filtro de mínimo documentos).
        Mucho más rápido que buscar en AGE.

        Args:
            nombres: Lista de nombres a buscar
            max_nodes: Límite de nodos (default 50)

        Returns:
            Grafo en formato estándar del visualizador
        """
        import psycopg2
        from ...consultas import get_db_connection

        conn = get_db_connection()
        cur = conn.cursor()

        nodes = {}
        edges = []

        # Buscar co-ocurrencias DIRECTAMENTE (sin filtro de mínimo 3 docs)
        for nombre in nombres:
            # Obtener personas que co-ocurren con el nombre buscado
            cur.execute("""
                SELECT
                    p1.nombre as entidad_1,
                    p2.nombre as entidad_2,
                    p1.tipo as tipo_1,
                    p2.tipo as tipo_2,
                    COUNT(DISTINCT p1.documento_id) as fuerza_conexion
                FROM personas p1
                JOIN personas p2 ON p1.documento_id = p2.documento_id
                WHERE p1.nombre != p2.nombre
                  AND LOWER(p1.nombre) LIKE LOWER(%s)
                GROUP BY p1.nombre, p2.nombre, p1.tipo, p2.tipo
                ORDER BY fuerza_conexion DESC
                LIMIT %s
            """, (f'%{nombre}%', max_nodes))

            for row in cur.fetchall():
                entidad_1, entidad_2, tipo_1, tipo_2, fuerza = row

                # Agregar nodos
                if entidad_1 not in nodes:
                    nodes[entidad_1] = {
                        'id': f"pg_{hash(entidad_1) % 1000000}",
                        'name': entidad_1,
                        'type': tipo_1 or 'persona',
                        'level': 0,
                        'size': 1.0,
                        'weight': float(fuerza)
                    }

                if entidad_2 not in nodes:
                    nodes[entidad_2] = {
                        'id': f"pg_{hash(entidad_2) % 1000000}",
                        'name': entidad_2,
                        'type': tipo_2 or 'persona',
                        'level': 1,
                        'size': 1.0,
                        'weight': float(fuerza)
                    }

                # Agregar edge
                edges.append({
                    'source': nodes[entidad_1]['id'],
                    'target': nodes[entidad_2]['id'],
                    'type': 'CO_OCURRE_CON',
                    'weight': float(fuerza),
                    'label': f"{int(fuerza)} docs"
                })

        cur.close()
        conn.close()

        return {
            "nodes": list(nodes.values()),
            "edges": edges,
            "config": {
                "title": f"Red de Conexiones: {', '.join(nombres[:3])}{'...' if len(nombres) > 3 else ''}",
                "node_colors": self.node_colors,
                "edge_colors": self.edge_colors
            }
        }


def main():
    """Función de prueba del adaptador"""
    print("🔄 AGE Graph Adapter - Prueba")
    print("=" * 60)

    adapter = AGEGraphAdapter()

    # Listar queries disponibles
    print("\n📋 Consultas disponibles:")
    for query_info in adapter.get_available_queries():
        print(f"  • {query_info['name']}: {query_info['description']}")

    # Ejecutar query de ejemplo
    print("\n🔍 Ejecutando query: top_connected")
    try:
        data = adapter.execute_predefined_query('top_connected')
        print(f"\n✅ Datos obtenidos:")
        print(f"  Nodos: {len(data['nodes'])}")
        print(f"  Aristas: {len(data['edges'])}")
        print(f"  Tipos de nodos: {set(n['type'] for n in data['nodes'])}")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
