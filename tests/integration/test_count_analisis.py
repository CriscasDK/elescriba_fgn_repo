#!/usr/bin/env python3
"""Verificar cuántos documentos tienen campo analisis"""

import sys
sys.path.insert(0, '/home/lab4/scripts/documentos_judiciales')

from core.consultas import get_db_connection

conn = get_db_connection()
cur = conn.cursor()

# Contar documentos con analisis
cur.execute("""
    SELECT
        COUNT(*) as total_docs,
        COUNT(analisis) as con_analisis,
        COUNT(*) - COUNT(analisis) as sin_analisis
    FROM documentos
""")

stats = cur.fetchone()
print(f"📊 Estadísticas de documentos:")
print(f"   Total documentos:        {stats[0]}")
print(f"   Con análisis:            {stats[1]}")
print(f"   Sin análisis:            {stats[2]}")

# Verificar longitud promedio de analisis
cur.execute("""
    SELECT
        AVG(LENGTH(analisis)) as avg_length,
        MIN(LENGTH(analisis)) as min_length,
        MAX(LENGTH(analisis)) as max_length
    FROM documentos
    WHERE analisis IS NOT NULL
""")

length_stats = cur.fetchone()
print(f"\n📏 Longitud del campo analisis:")
print(f"   Promedio:  {int(length_stats[0]) if length_stats[0] else 0} caracteres")
print(f"   Mínimo:    {length_stats[1]} caracteres")
print(f"   Máximo:    {length_stats[2]} caracteres")

# Buscar análisis con palabras clave de relaciones
cur.execute("""
    SELECT COUNT(*)
    FROM documentos
    WHERE analisis IS NOT NULL
      AND (
        analisis ILIKE '%hermana%'
        OR analisis ILIKE '%hermano%'
        OR analisis ILIKE '%hijo%'
        OR analisis ILIKE '%hija%'
        OR analisis ILIKE '%esposa%'
        OR analisis ILIKE '%esposo%'
        OR analisis ILIKE '%padre%'
        OR analisis ILIKE '%madre%'
        OR analisis ILIKE '%miembro de%'
      )
""")

con_relaciones = cur.fetchone()[0]
print(f"\n👨‍👩‍👧‍👦 Documentos con posibles relaciones familiares/organizacionales:")
print(f"   {con_relaciones} documentos contienen palabras clave")

cur.close()
conn.close()
