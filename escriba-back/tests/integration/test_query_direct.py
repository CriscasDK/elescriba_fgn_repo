#!/usr/bin/env python3
"""
Test directo de consulta SQL para Oswaldo Olivo
"""

import psycopg2
import psycopg2.extras

def test_direct_query():
    print("🔍 TEST DIRECTO DE CONSULTA SQL")
    print("=" * 50)

    try:
        # Conectar a BD
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="documentos_juridicos_gpt4",
            user="docs_user",
            password="docs_password_2025"
        )
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # Test 1: Contar menciones
        print("\n1️⃣ TEST: Contar menciones")
        cur.execute("""
            SELECT COUNT(*) FROM personas
            WHERE nombre ILIKE %s AND tipo ILIKE %s
        """, ('%oswaldo%olivo%', '%victim%'))
        result = cur.fetchone()
        print(f"Resultado: {result}")
        print(f"Count: {result[0] if result else 'N/A'}")

        # Test 2: Obtener documentos
        print("\n2️⃣ TEST: Obtener documentos relacionados")
        cur.execute("""
            SELECT DISTINCT
                d.archivo,
                m.nuc,
                m.fecha_creacion as fecha,
                m.despacho,
                m.detalle as tipo_documental,
                p.nombre,
                p.tipo,
                COALESCE(d.analisis, '') as analisis_ia
            FROM personas p
            JOIN documentos d ON p.documento_id = d.id
            LEFT JOIN metadatos m ON d.id = m.documento_id
            WHERE p.nombre ILIKE %s AND p.tipo ILIKE %s
            ORDER BY m.fecha_creacion DESC NULLS LAST
            LIMIT %s
        """, ('%oswaldo%olivo%', '%victim%', 10))

        rows = cur.fetchall()
        print(f"Número de filas: {len(rows)}")

        for i, row in enumerate(rows):
            print(f"\nFila {i+1}:")
            print(f"  Columnas: {len(row)}")
            try:
                print(f"  Archivo: {row[0]}")
                print(f"  NUC: {row[1]}")
                print(f"  Fecha: {row[2]}")
                print(f"  Despacho: {row[3]}")
                print(f"  Tipo: {row[4]}")
                print(f"  Nombre: {row[5]}")
                print(f"  Tipo persona: {row[6]}")
                print(f"  Análisis: {row[7][:50] if row[7] else 'N/A'}...")
            except IndexError as e:
                print(f"  ❌ IndexError: {e}")
                print(f"  Row content: {row}")

        cur.close()
        conn.close()
        print("\n✅ Test completado sin errores")

    except Exception as e:
        print(f"❌ Error en test directo: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_direct_query()