#!/usr/bin/env python3
"""Script de prueba para verificar estructura del campo analisis"""

import sys
sys.path.insert(0, '/home/lab4/scripts/documentos_judiciales')

from core.consultas import get_db_connection

conn = get_db_connection()
cur = conn.cursor()

# Obtener un documento con analisis
cur.execute("""
    SELECT id, archivo, analisis
    FROM documentos
    WHERE analisis IS NOT NULL AND LENGTH(analisis) > 100
    LIMIT 1
""")

result = cur.fetchone()

if result:
    doc_id, archivo, analisis = result
    print(f"Documento ID: {doc_id}")
    print(f"Archivo: {archivo}")
    print(f"\nAnálisis (primeros 2000 caracteres):")
    print("="*80)
    print(analisis[:2000])
    print("="*80)
else:
    print("No se encontraron documentos con campo 'analisis'")

cur.close()
conn.close()
