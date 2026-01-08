"""Utilidades para la aplicación Dash."""

from .municipios import cargar_municipios_desde_db, obtener_municipios
from .context import reescribir_query_con_contexto
from .entities import extraer_entidades_de_consulta
from .pdf_handlers import convertir_ruta_bd_a_real, obtener_ruta_pdf_real, create_download_endpoint

__all__ = [
    'cargar_municipios_desde_db',
    'obtener_municipios',
    'reescribir_query_con_contexto',
    'extraer_entidades_de_consulta',
    'convertir_ruta_bd_a_real',
    'obtener_ruta_pdf_real',
    'create_download_endpoint',
]
