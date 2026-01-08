"""
Configuración del Módulo de Grafos

Centraliza toda la configuración relacionada con Apache AGE y el grafo.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class GraphConfig:
    """Configuración para el módulo de grafos"""

    # Conexión a PostgreSQL/AGE
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", "5432"))
    db_name: str = os.getenv("DB_NAME", "documentos_juridicos_gpt4")
    db_user: str = os.getenv("DB_USER", "docs_user")
    db_password: str = os.getenv("DB_PASSWORD", "docs_password_2025")

    # Nombre del grafo en AGE
    graph_name: str = "documentos_juridicos_graph"

    # Configuración de parsing
    parse_batch_size: int = 100  # Procesar JSONs en lotes

    # Configuración de construcción del grafo
    build_batch_size: int = 1000  # Insertar nodos/edges en lotes

    # Configuración de performance
    enable_cache: bool = True
    cache_ttl_seconds: int = 300  # 5 minutos

    # Paths
    json_files_dir: str = "json_files"

    # Límites para prototipo
    prototype_limit: Optional[int] = None  # None = sin límite

    def get_connection_string(self) -> str:
        """Retorna string de conexión para psycopg2"""
        return (
            f"host={self.db_host} "
            f"port={self.db_port} "
            f"dbname={self.db_name} "
            f"user={self.db_user} "
            f"password={self.db_password}"
        )

    def get_connection_dict(self) -> dict:
        """Retorna dict de conexión para psycopg2"""
        return {
            "host": self.db_host,
            "port": self.db_port,
            "dbname": self.db_name,
            "user": self.db_user,
            "password": self.db_password
        }


# Instancia global de configuración
config = GraphConfig()