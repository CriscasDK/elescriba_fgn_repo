"""Utilidades para carga y manejo de municipios desde la base de datos."""

import psycopg2
from typing import Dict


def cargar_municipios_desde_db() -> Dict[str, str]:
    """
    Carga lista de municipios únicos desde vista materializada.
    Cache en memoria para evitar múltiples queries.

    Returns:
        dict: {municipio_normalizado: municipio_original}
    """
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="documentos_juridicos_gpt4",
            user="docs_user",
            password="docs_password_2025"
        )
        cur = conn.cursor()

        # Query para obtener todos los municipios únicos
        cur.execute("""
            SELECT DISTINCT municipio
            FROM analisis_lugares
            WHERE municipio IS NOT NULL
              AND municipio <> ''
              AND LENGTH(municipio) > 2
            ORDER BY municipio;
        """)

        municipios = {}
        for row in cur.fetchall():
            municipio = row[0].strip()
            # Normalizar para búsqueda (lowercase, sin acentos)
            municipio_norm = municipio.lower()
            # Almacenar original para usar en filtros
            municipios[municipio_norm] = municipio

        cur.close()
        conn.close()

        print(f"✅ Cargados {len(municipios)} municipios desde BD")
        return municipios

    except Exception as e:
        print(f"❌ Error cargando municipios: {e}")
        return {}


# Cache global de municipios (se carga una vez al inicio)
_MUNICIPIOS_CACHE = None


def obtener_municipios() -> Dict[str, str]:
    """
    Retorna cache de municipios, cargándolo si es necesario.

    Returns:
        dict: {municipio_normalizado: municipio_original}
    """
    global _MUNICIPIOS_CACHE
    if _MUNICIPIOS_CACHE is None:
        _MUNICIPIOS_CACHE = cargar_municipios_desde_db()
    return _MUNICIPIOS_CACHE
