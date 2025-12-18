#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.consultas import get_db_connection, ejecutar_consulta_geografica_directa

def verificar_datos_disponibles():
    """Verificar qué datos están disponibles para filtros"""

    print("=== VERIFICAR DATOS DISPONIBLES PARA FILTROS ===")

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # 1. Departamentos disponibles
        print("\n1. DEPARTAMENTOS DISPONIBLES:")
        cur.execute("""
            SELECT departamento, COUNT(*) as docs
            FROM analisis_lugares
            WHERE departamento IS NOT NULL AND departamento != ''
            GROUP BY departamento
            ORDER BY docs DESC
            LIMIT 10
        """)
        departamentos = cur.fetchall()
        for dept, count in departamentos:
            print(f"   {dept}: {count} documentos")

        # 2. Municipios en Antioquia
        print("\n2. MUNICIPIOS EN ANTIOQUIA:")
        cur.execute("""
            SELECT municipio, COUNT(*) as docs
            FROM analisis_lugares
            WHERE departamento ILIKE '%Antioquia%'
              AND municipio IS NOT NULL AND municipio != ''
            GROUP BY municipio
            ORDER BY docs DESC
            LIMIT 10
        """)
        municipios = cur.fetchall()
        for mun, count in municipios:
            print(f"   {mun}: {count} documentos")

        # 3. Despachos disponibles
        print("\n3. DESPACHOS DISPONIBLES:")
        cur.execute("""
            SELECT DISTINCT COALESCE(m.despacho, d.despacho) as despacho, COUNT(*) as docs
            FROM documentos d
            LEFT JOIN metadatos m ON d.id = m.documento_id
            WHERE COALESCE(m.despacho, d.despacho) IS NOT NULL
            GROUP BY COALESCE(m.despacho, d.despacho)
            ORDER BY docs DESC
            LIMIT 10
        """)
        despachos = cur.fetchall()
        for desp, count in despachos:
            print(f"   {desp}: {count} documentos")

        # 4. Tipos de documento
        print("\n4. TIPOS DE DOCUMENTO:")
        cur.execute("""
            SELECT DISTINCT m.detalle, COUNT(*) as docs
            FROM metadatos m
            WHERE m.detalle IS NOT NULL
            GROUP BY m.detalle
            ORDER BY docs DESC
            LIMIT 10
        """)
        tipos = cur.fetchall()
        for tipo, count in tipos:
            print(f"   {tipo}: {count} documentos")

        # 5. NUCs disponibles
        print("\n5. NUCs DISPONIBLES (sample):")
        cur.execute("""
            SELECT DISTINCT COALESCE(m.nuc, d.nuc) as nuc, COUNT(*) as docs
            FROM documentos d
            LEFT JOIN metadatos m ON d.id = m.documento_id
            WHERE COALESCE(m.nuc, d.nuc) IS NOT NULL
            GROUP BY COALESCE(m.nuc, d.nuc)
            ORDER BY docs DESC
            LIMIT 5
        """)
        nucs = cur.fetchall()
        for nuc, count in nucs:
            print(f"   {nuc}: {count} documentos")

        conn.close()

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def test_filtro_municipio():
    """Test filtro por municipio"""

    print("\n=== TEST FILTRO MUNICIPIO ===")

    # Test Medellín (municipio en Antioquia)
    try:
        resultado = ejecutar_consulta_geografica_directa(
            "victimas en Medellin",
            departamento="Antioquia",
            municipio="Medellín"
        )

        print(f"✅ Medellín, Antioquia:")
        print(f"   Víctimas: {len(resultado['victimas'])}")
        print(f"   Fuentes: {len(resultado['fuentes'])}")

        if resultado['victimas']:
            print(f"   Top víctima: {resultado['victimas'][0]['nombre']} ({resultado['victimas'][0]['menciones']} menciones)")

    except Exception as e:
        print(f"❌ Error filtro municipio: {e}")

def test_otros_departamentos():
    """Test otros departamentos"""

    print("\n=== TEST OTROS DEPARTAMENTOS ===")

    departamentos_test = ['Meta', 'Bogotá D.C.', 'Tolima']

    for dept in departamentos_test:
        try:
            resultado = ejecutar_consulta_geografica_directa(
                f"victimas en {dept}",
                departamento=dept
            )

            print(f"✅ {dept}:")
            print(f"   Víctimas: {len(resultado['victimas'])}")
            print(f"   Fuentes: {len(resultado['fuentes'])}")

        except Exception as e:
            print(f"❌ Error {dept}: {e}")

if __name__ == "__main__":
    verificar_datos_disponibles()
    test_filtro_municipio()
    test_otros_departamentos()