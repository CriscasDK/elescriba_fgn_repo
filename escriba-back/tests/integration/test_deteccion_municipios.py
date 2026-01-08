#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test de detección de municipios en consultas
"""

import psycopg2

def cargar_municipios_desde_db():
    """
    Carga lista de municipios únicos desde vista materializada.
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
            # Normalizar para búsqueda (lowercase)
            municipio_norm = municipio.lower()
            # Almacenar original para usar en filtros
            municipios[municipio_norm] = municipio

        cur.close()
        conn.close()

        print(f"✅ Cargados {len(municipios)} municipios desde BD\n")
        return municipios

    except Exception as e:
        print(f"❌ Error cargando municipios: {e}")
        return {}


def detectar_municipio(consulta, municipios_db):
    """
    Detecta municipio en una consulta de texto
    """
    consulta_lower = consulta.lower()

    # Buscar municipios en orden de longitud (más largos primero)
    municipios_ordenados = sorted(municipios_db.keys(), key=len, reverse=True)

    for mun_norm in municipios_ordenados:
        if mun_norm in consulta_lower:
            municipio = municipios_db[mun_norm]
            return municipio

    return None


def main():
    """
    Test de detección de municipios con casos reales
    """
    print("=" * 70)
    print("🧪 TEST DE DETECCIÓN DE MUNICIPIOS")
    print("=" * 70)
    print()

    # Cargar municipios
    municipios = cargar_municipios_desde_db()

    # Casos de prueba
    casos_prueba = [
        "dame la lista de victimas en Medellín",
        "victimas en Apartadó",
        "casos en San José de Apartadó",
        "que paso en Buenaventura",
        "lista de victimas en Florencia",
        "victimas en Villavicencio",
        "casos en Turbo",
        "dame victimas en Cali",
        "lista en Bogotá",
        "victimas en El Doncello",
        "casos en Puerto Asís",
        "que paso en Barrancabermeja",
    ]

    print("RESULTADOS DE DETECCIÓN:")
    print("-" * 70)

    detectados = 0
    no_detectados = 0

    for consulta in casos_prueba:
        municipio_detectado = detectar_municipio(consulta, municipios)

        if municipio_detectado:
            print(f"✅ Consulta: \"{consulta}\"")
            print(f"   → Municipio detectado: '{municipio_detectado}'")
            detectados += 1
        else:
            print(f"❌ Consulta: \"{consulta}\"")
            print(f"   → NO detectado")
            no_detectados += 1
        print()

    print("=" * 70)
    print(f"RESUMEN:")
    print(f"  Detectados: {detectados}/{len(casos_prueba)} ({100*detectados//len(casos_prueba)}%)")
    print(f"  No detectados: {no_detectados}/{len(casos_prueba)}")
    print("=" * 70)


if __name__ == "__main__":
    main()
