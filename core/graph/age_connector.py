"""
Conector para Apache AGE (PostgreSQL Graph Extension)

Maneja la conexión y operaciones básicas con Apache AGE usando psycopg2.
"""

import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Optional, Tuple, Union
import json
from contextlib import contextmanager

from .config import GraphConfig


def agtype_to_python(value: Any) -> Any:
    """
    Convierte un valor agtype de AGE a tipo Python nativo.

    AGE retorna valores envueltos en objetos agtype que necesitan ser parseados.
    """
    if value is None:
        return None

    # Si es string, intentar parsear como JSON
    if isinstance(value, str):
        # AGE a veces retorna valores como strings JSON
        try:
            parsed = json.loads(value)
            return parsed
        except (json.JSONDecodeError, ValueError):
            # Si no es JSON, retornar como está
            return value

    # Si es un objeto con __str__, intentar parsear su representación
    if hasattr(value, '__str__'):
        str_val = str(value)
        try:
            return json.loads(str_val)
        except (json.JSONDecodeError, ValueError):
            # Si falla, retornar el string
            return str_val

    return value


class AGEConnector:
    """
    Conector para Apache AGE.

    Proporciona métodos para conectar, crear grafos y ejecutar consultas Cypher.
    """

    def __init__(self, config: Optional[GraphConfig] = None):
        """
        Inicializa el conector AGE.

        Args:
            config: Configuración del grafo. Si no se proporciona, usa config por defecto.
        """
        self.config = config or GraphConfig()
        self._connection = None

    @contextmanager
    def get_connection(self):
        """
        Context manager para obtener una conexión a la base de datos.

        Yields:
            psycopg2.connection: Conexión activa a PostgreSQL
        """
        conn = psycopg2.connect(
            host=self.config.db_host,
            port=self.config.db_port,
            dbname=self.config.db_name,
            user=self.config.db_user,
            password=self.config.db_password
        )
        try:
            yield conn
        finally:
            conn.close()

    def test_connection(self) -> bool:
        """
        Prueba la conexión a PostgreSQL.

        Returns:
            bool: True si la conexión es exitosa
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT version();")
                    version = cur.fetchone()[0]
                    print(f"✅ Conexión exitosa: {version}")
                    return True
        except Exception as e:
            print(f"❌ Error de conexión: {e}")
            return False

    def load_age_extension(self, conn) -> None:
        """
        Carga la extensión AGE en la sesión actual.

        Args:
            conn: Conexión activa a PostgreSQL
        """
        with conn.cursor() as cur:
            cur.execute("LOAD 'age';")
            cur.execute('SET search_path = ag_catalog, "$user", public;')
        conn.commit()

    def graph_exists(self, graph_name: str) -> bool:
        """
        Verifica si un grafo existe.

        Args:
            graph_name: Nombre del grafo

        Returns:
            bool: True si el grafo existe
        """
        try:
            with self.get_connection() as conn:
                self.load_age_extension(conn)
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT COUNT(*) FROM ag_catalog.ag_graph WHERE name = %s;",
                        (graph_name,)
                    )
                    count = cur.fetchone()[0]
                    return count > 0
        except Exception as e:
            print(f"Error verificando grafo: {e}")
            return False

    def create_graph(self, graph_name: Optional[str] = None) -> bool:
        """
        Crea un nuevo grafo en AGE.

        Args:
            graph_name: Nombre del grafo. Si no se proporciona, usa config.graph_name

        Returns:
            bool: True si se creó exitosamente
        """
        graph_name = graph_name or self.config.graph_name

        try:
            with self.get_connection() as conn:
                self.load_age_extension(conn)

                # Verificar si ya existe
                if self.graph_exists(graph_name):
                    print(f"⚠️  El grafo '{graph_name}' ya existe")
                    return True

                with conn.cursor() as cur:
                    # Crear grafo usando la función de AGE
                    cur.execute(
                        sql.SQL("SELECT create_graph(%s);"),
                        (graph_name,)
                    )
                conn.commit()
                print(f"✅ Grafo '{graph_name}' creado exitosamente")
                return True

        except Exception as e:
            print(f"❌ Error creando grafo: {e}")
            return False

    def drop_graph(self, graph_name: Optional[str] = None, cascade: bool = True) -> bool:
        """
        Elimina un grafo de AGE.

        Args:
            graph_name: Nombre del grafo. Si no se proporciona, usa config.graph_name
            cascade: Si True, elimina en cascada

        Returns:
            bool: True si se eliminó exitosamente
        """
        graph_name = graph_name or self.config.graph_name

        try:
            with self.get_connection() as conn:
                self.load_age_extension(conn)

                if not self.graph_exists(graph_name):
                    print(f"⚠️  El grafo '{graph_name}' no existe")
                    return True

                with conn.cursor() as cur:
                    cur.execute(
                        sql.SQL("SELECT drop_graph(%s, %s);"),
                        (graph_name, cascade)
                    )
                conn.commit()
                print(f"✅ Grafo '{graph_name}' eliminado exitosamente")
                return True

        except Exception as e:
            print(f"❌ Error eliminando grafo: {e}")
            return False

    def execute_cypher(
        self,
        cypher_query: str,
        parameters: Optional[Dict[str, Any]] = None,
        graph_name: Optional[str] = None,
        column_definitions: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Ejecuta una consulta Cypher en AGE.

        Args:
            cypher_query: Consulta Cypher a ejecutar
            parameters: Parámetros para la consulta (opcional)
            graph_name: Nombre del grafo. Si no se proporciona, usa config.graph_name
            column_definitions: Definiciones de columnas para queries complejas.
                               Ej: ["nombre agtype", "count agtype"]
                               Si None, usa "(result agtype)" por defecto.

        Returns:
            List[Dict]: Resultados de la consulta
        """
        graph_name = graph_name or self.config.graph_name
        parameters = parameters or {}

        try:
            with self.get_connection() as conn:
                self.load_age_extension(conn)

                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Construir definición de columnas
                    if column_definitions:
                        columns_str = ", ".join(column_definitions)
                    else:
                        columns_str = "result agtype"

                    # AGE usa la función cypher() para ejecutar queries
                    query = sql.SQL(
                        "SELECT * FROM cypher(%s, $$ {} $$) as ({});"
                    ).format(sql.SQL(cypher_query), sql.SQL(columns_str))

                    cur.execute(query, (graph_name,))
                    results = cur.fetchall()

                    # IMPORTANTE: Hacer commit para persistir cambios en AGE
                    conn.commit()

                    # Convertir resultados agtype a Python dicts
                    parsed_results = []
                    for row in results:
                        parsed_row = {}
                        for key, value in dict(row).items():
                            parsed_row[key] = agtype_to_python(value)
                        parsed_results.append(parsed_row)

                    return parsed_results

        except Exception as e:
            print(f"❌ Error ejecutando Cypher: {e}")
            print(f"   Query: {cypher_query}")
            return []

    def create_node(
        self,
        label: str,
        properties: Dict[str, Any],
        graph_name: Optional[str] = None
    ) -> bool:
        """
        Crea un nodo en el grafo.

        Args:
            label: Etiqueta del nodo (ej: 'Persona', 'Organizacion')
            properties: Propiedades del nodo
            graph_name: Nombre del grafo

        Returns:
            bool: True si se creó exitosamente
        """
        # Convertir propiedades a formato Cypher {key: 'value', ...}
        props_list = [f"{k}: '{v}'" if isinstance(v, str) else f"{k}: {v}"
                      for k, v in properties.items()]
        props_str = "{" + ", ".join(props_list) + "}"

        cypher = f"CREATE (n:{label} {props_str}) RETURN n"

        result = self.execute_cypher(cypher, graph_name=graph_name)
        return len(result) > 0

    def create_relationship(
        self,
        from_label: str,
        from_property: str,
        from_value: Any,
        to_label: str,
        to_property: str,
        to_value: Any,
        rel_type: str,
        rel_properties: Optional[Dict[str, Any]] = None,
        graph_name: Optional[str] = None
    ) -> bool:
        """
        Crea una relación entre dos nodos.

        Args:
            from_label: Etiqueta del nodo origen
            from_property: Propiedad para buscar nodo origen
            from_value: Valor de la propiedad origen
            to_label: Etiqueta del nodo destino
            to_property: Propiedad para buscar nodo destino
            to_value: Valor de la propiedad destino
            rel_type: Tipo de relación
            rel_properties: Propiedades de la relación (opcional)
            graph_name: Nombre del grafo

        Returns:
            bool: True si se creó exitosamente
        """
        rel_properties = rel_properties or {}

        # Convertir propiedades a formato Cypher
        if rel_properties:
            props_list = [f"{k}: '{v}'" if isinstance(v, str) else f"{k}: {v}"
                          for k, v in rel_properties.items()]
            props_str = "{" + ", ".join(props_list) + "}"
        else:
            props_str = ""

        cypher = f"""
        MATCH (a:{from_label} {{{from_property}: '{from_value}'}})
        MATCH (b:{to_label} {{{to_property}: '{to_value}'}})
        CREATE (a)-[r:{rel_type} {props_str}]->(b)
        RETURN r
        """

        result = self.execute_cypher(cypher, graph_name=graph_name)
        return len(result) > 0

    def get_graph_stats(self, graph_name: Optional[str] = None) -> Dict[str, int]:
        """
        Obtiene estadísticas del grafo.

        Args:
            graph_name: Nombre del grafo

        Returns:
            Dict con estadísticas del grafo
        """
        graph_name = graph_name or self.config.graph_name

        stats = {
            "total_nodes": 0,
            "total_relationships": 0,
            "node_labels": {},
            "relationship_types": {}
        }

        try:
            with self.get_connection() as conn:
                self.load_age_extension(conn)

                # Contar nodos totales
                cypher_nodes = "MATCH (n) RETURN count(n) as count"
                result = self.execute_cypher(cypher_nodes, graph_name=graph_name)
                if result:
                    stats["total_nodes"] = result[0].get("count", 0)

                # Contar relaciones totales
                cypher_rels = "MATCH ()-[r]->() RETURN count(r) as count"
                result = self.execute_cypher(cypher_rels, graph_name=graph_name)
                if result:
                    stats["total_relationships"] = result[0].get("count", 0)

        except Exception as e:
            print(f"⚠️  Error obteniendo estadísticas: {e}")

        return stats