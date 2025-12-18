#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.consultas import get_db_connection

def test_minimal_antioquia():
    """Test the exact query that should work"""

    print("=== MINIMAL ANTIOQUIA TEST ===")

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # The query I know works from debug_antioquia_data.py
        query = """
            SELECT p.nombre, COUNT(*) as menciones
            FROM personas p
            JOIN documentos d ON p.documento_id = d.id
            LEFT JOIN analisis_lugares al ON d.id = al.documento_id
            WHERE p.tipo ILIKE '%victim%'
              AND p.tipo NOT ILIKE '%victimario%'
              AND al.departamento ILIKE '%Antioquia%'
            GROUP BY p.nombre
            ORDER BY menciones DESC
            LIMIT 10
        """

        cur.execute(query)
        rows = cur.fetchall()

        print(f"Victims found: {len(rows)}")
        for row in rows:
            print(f"  - {row[0]}: {row[1]} mentions")

        conn.close()

        # Now test our function with ILIKE
        from core.consultas import ejecutar_consulta_geografica_directa

        print("\n=== TEST GEOGRAFICA DIRECTA ===")
        resultado = ejecutar_consulta_geografica_directa(
            "victimas en Antioquia",
            departamento="Antioquia"
        )

        print(f"Function result: {len(resultado['victimas'])} victims")
        for v in resultado['victimas'][:5]:
            print(f"  - {v['nombre']}: {v['menciones']}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_minimal_antioquia()