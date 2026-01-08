#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.consultas import get_db_connection

def test_nuc_filtering():
    """Test the updated NUC filtering function"""

    print("=== TEST NUC FILTERING (21-23 DIGITS) ===")

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # 1. Ver todos los NUCs sin filtro
        print("\n1. TODOS LOS NUCs EN LA BD (antes del filtro):")
        cur.execute("""
            SELECT DISTINCT COALESCE(m.nuc, d.nuc) as nuc,
                   LENGTH(COALESCE(m.nuc, d.nuc)) as longitud,
                   COUNT(*) as docs
            FROM documentos d
            LEFT JOIN metadatos m ON d.id = m.documento_id
            WHERE COALESCE(m.nuc, d.nuc) IS NOT NULL
            GROUP BY COALESCE(m.nuc, d.nuc)
            ORDER BY docs DESC
            LIMIT 20
        """)
        todos_nucs = cur.fetchall()

        for nuc, longitud, docs in todos_nucs:
            es_valido = "✅" if (21 <= longitud <= 23 and nuc.isdigit()) else "❌"
            print(f"   {es_valido} {nuc} (L:{longitud}) - {docs} docs")

        # 2. Ver NUCs con el filtro aplicado (21-23 dígitos)
        print("\n2. NUCs VÁLIDOS (21-23 dígitos, solo números):")
        cur.execute("""
            SELECT DISTINCT COALESCE(m.nuc, d.nuc) as nuc,
                   LENGTH(COALESCE(m.nuc, d.nuc)) as longitud,
                   COUNT(*) as docs
            FROM documentos d
            LEFT JOIN metadatos m ON d.id = m.documento_id
            WHERE COALESCE(m.nuc, d.nuc) IS NOT NULL
              AND LENGTH(COALESCE(m.nuc, d.nuc)) BETWEEN 21 AND 23
              AND COALESCE(m.nuc, d.nuc) ~ '^[0-9]+$'
            GROUP BY COALESCE(m.nuc, d.nuc)
            ORDER BY docs DESC
            LIMIT 15
        """)
        nucs_validos = cur.fetchall()

        total_validos = len(nucs_validos)
        for nuc, longitud, docs in nucs_validos:
            print(f"   ✅ {nuc} (L:{longitud}) - {docs} docs")

        # 3. Ver NUCs inválidos que se filtran
        print("\n3. NUCs INVÁLIDOS (que se filtran):")
        cur.execute("""
            SELECT DISTINCT COALESCE(m.nuc, d.nuc) as nuc,
                   LENGTH(COALESCE(m.nuc, d.nuc)) as longitud,
                   COUNT(*) as docs,
                   CASE
                       WHEN LENGTH(COALESCE(m.nuc, d.nuc)) < 21 THEN 'Muy corto'
                       WHEN LENGTH(COALESCE(m.nuc, d.nuc)) > 23 THEN 'Muy largo'
                       WHEN COALESCE(m.nuc, d.nuc) !~ '^[0-9]+$' THEN 'No numérico'
                       ELSE 'Otro'
                   END as motivo
            FROM documentos d
            LEFT JOIN metadatos m ON d.id = m.documento_id
            WHERE COALESCE(m.nuc, d.nuc) IS NOT NULL
              AND NOT (LENGTH(COALESCE(m.nuc, d.nuc)) BETWEEN 21 AND 23
                      AND COALESCE(m.nuc, d.nuc) ~ '^[0-9]+$')
            GROUP BY COALESCE(m.nuc, d.nuc)
            ORDER BY docs DESC
            LIMIT 15
        """)
        nucs_invalidos = cur.fetchall()

        total_invalidos = len(nucs_invalidos)
        for nuc, longitud, docs, motivo in nucs_invalidos:
            print(f"   ❌ {nuc} (L:{longitud}) - {docs} docs - {motivo}")

        # 4. Estadísticas finales
        print(f"\n4. ESTADÍSTICAS:")
        print(f"   Total NUCs únicos: {len(todos_nucs)}")
        print(f"   NUCs válidos (21-23 dígitos): {total_validos}")
        print(f"   NUCs inválidos (filtrados): {total_invalidos}")
        print(f"   Porcentaje válidos: {(total_validos/(total_validos+total_invalidos)*100):.1f}%")

        # 5. Test de función específica
        print("\n5. TEST DE FUNCIÓN obtener_opciones_nuc():")
        from core.consultas import obtener_opciones_nuc
        opciones = obtener_opciones_nuc()
        print(f"   Opciones disponibles en dropdown: {len(opciones)}")
        if opciones:
            print("   Primeras 5 opciones:")
            for i, opcion in enumerate(opciones[:5]):
                print(f"     {i+1}. {opcion}")

        conn.close()

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_nuc_filtering()