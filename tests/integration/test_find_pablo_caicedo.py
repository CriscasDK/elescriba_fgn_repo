#!/usr/bin/env python3
"""Buscar documento de Pablo Caicedo Siachoque en BD"""

import sys
sys.path.insert(0, '/home/lab4/scripts/documentos_judiciales')

from core.consultas import get_db_connection

conn = get_db_connection()
cur = conn.cursor()

# Buscar documento que menciona a Pablo Caicedo
cur.execute("""
    SELECT id, archivo, analisis
    FROM documentos
    WHERE analisis LIKE '%Pablo Caicedo%'
    OR analisis LIKE '%Patricia Caicedo%'
    OR analisis LIKE '%Marco Fidel Castro%'
    LIMIT 1
""")

result = cur.fetchone()

if result:
    doc_id, archivo, analisis = result
    print(f"✅ Encontrado:")
    print(f"Documento ID: {doc_id}")
    print(f"Archivo: {archivo}")
    print(f"\nAnálisis (primeros 3000 caracteres):")
    print("="*80)
    print(analisis[:3000])
    print("="*80)

    # Buscar menciones específicas de relaciones
    if "hermana" in analisis or "hija" in analisis or "hijo" in analisis:
        print("\n✅ Documento contiene relaciones familiares explícitas!")
else:
    print("❌ No se encontró documento con esas personas")

cur.close()
conn.close()
