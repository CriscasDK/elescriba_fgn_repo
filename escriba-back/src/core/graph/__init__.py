"""
Módulo de Grafos para Sistema de Documentos Judiciales

Este módulo maneja la extracción, construcción y consulta de grafos de conocimiento
a partir de los documentos judiciales procesados.

Componentes:
- parser.py: Extrae entidades del campo 'analisis' de los JSONs
- age_connector.py: Conexión a Apache AGE (PostgreSQL Graph Extension)
- graph_builder.py: Construcción del grafo desde entidades extraídas
- graph_queries.py: Consultas especializadas usando Cypher
- config.py: Configuración del módulo

Autor: Sistema Modular
Versión: 1.0.0
Fecha: 2025-09-30
"""

__version__ = "1.0.0"
__author__ = "Sistema Modular"

from .config import GraphConfig
from .parser import AnalisisParser
from .age_connector import AGEConnector
from .graph_builder import GraphBuilder

__all__ = [
    "GraphConfig",
    "AnalisisParser",
    "AGEConnector",
    "GraphBuilder"
]