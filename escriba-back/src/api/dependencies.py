"""
Dependencias de la API
Auth, conexiones a BD, etc.
"""
import sys
from pathlib import Path
from typing import Optional
from fastapi import Header, HTTPException
import psycopg2
import psycopg2.extras

# Agregar path para importar módulos core del monolito
proyecto_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(proyecto_root))

# Importar la función de conexión desde el MONOLITO (core/consultas.py)
from core.consultas import get_db_connection as core_get_db_connection


# TODO: Implementar autenticación real
async def verify_token(x_token: Optional[str] = Header(None)):
    """
    Verificar token de autenticación
    Por ahora es un placeholder
    """
    # if x_token != "secret-token":
    #     raise HTTPException(status_code=401, detail="Invalid token")
    return True


# Conexión a base de datos usando la función del core
def get_db_connection():
    """
    Obtener conexión a la base de datos PostgreSQL
    Usa la función del core para consistencia con app_dash.py
    """
    return core_get_db_connection()


# Dependency para FastAPI (con cleanup automático)
def get_db():
    """
    Dependency de FastAPI para obtener conexión a BD
    Se cierra automáticamente después de la request
    """
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()
