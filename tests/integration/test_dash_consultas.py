#!/usr/bin/env python3
"""
Script de prueba para verificar funcionalidades de Dash
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

# Cargar configuración
load_dotenv()

def test_bd_connection():
    """Probar conexión a base de datos"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=os.getenv('POSTGRES_PORT', '5432'),
            database=os.getenv('POSTGRES_DB', 'documentos_juridicos_gpt4'),
            user=os.getenv('POSTGRES_USER', 'docs_user'),
            password=os.getenv('POSTGRES_PASSWORD', 'docs_password_2025')
        )
        print("✅ Conexión a PostgreSQL exitosa")

        # Verificar tablas principales
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM documentos")
        docs = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM personas")
        personas = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM metadatos")
        metadatos = cur.fetchone()[0]

        print(f"✅ Documentos: {docs}")
        print(f"✅ Personas: {personas}")
        print(f"✅ Metadatos: {metadatos}")

        cur.close()
        conn.close()
        return True

    except Exception as e:
        print(f"❌ Error BD: {e}")
        return False

def test_consultas():
    """Probar funciones de consulta"""
    try:
        from core.consultas import (
            clasificar_consulta,
            ejecutar_consulta,
            obtener_victimas_paginadas,
            obtener_opciones_nuc
        )

        # Prueba 1: Clasificación de consultas
        print("\n=== PRUEBA 1: CLASIFICACIÓN DE CONSULTAS ===")
        consultas_test = [
            "¿Cuántas víctimas hay en Antioquia?",  # BD
            "¿Por qué ocurrieron las masacres?",    # RAG
            "Dame víctimas con contexto de masacres" # Híbrida
        ]

        for consulta in consultas_test:
            tipo = clasificar_consulta(consulta)
            print(f"✅ '{consulta}' → {tipo.upper()}")

        # Prueba 2: Obtener víctimas paginadas
        print("\n=== PRUEBA 2: PAGINACIÓN DE VÍCTIMAS ===")
        victimas, total = obtener_victimas_paginadas(page=1, page_size=5)
        print(f"✅ Víctimas página 1: {len(victimas)} de {total} total")

        if victimas:
            print(f"✅ Primera víctima: {victimas[0]['nombre']}")

        # Prueba 3: Opciones de filtros
        print("\n=== PRUEBA 3: OPCIONES DE FILTROS ===")
        nucs = obtener_opciones_nuc()
        print(f"✅ NUCs disponibles: {len(nucs)}")

        if nucs:
            print(f"✅ Primer NUC: {nucs[0]}")

        return True

    except Exception as e:
        print(f"❌ Error en consultas: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_rag_system():
    """Probar sistema RAG"""
    try:
        from src.core.sistema_rag_completo import SistemaRAGCompleto
        print("\n=== PRUEBA 4: SISTEMA RAG ===")
        print("✅ SistemaRAGCompleto importado correctamente")

        # Instanciar (sin ejecutar consulta completa para evitar lentitud)
        sistema = SistemaRAGCompleto()
        print("✅ SistemaRAGCompleto instanciado")

        return True

    except Exception as e:
        print(f"⚠️  Sistema RAG no disponible: {e}")
        return False

def main():
    """Ejecutar todas las pruebas"""
    print("🚀 INICIANDO PRUEBAS DE DASH FUNCIONAL")
    print("="*50)

    # Prueba 1: Conexión BD
    bd_ok = test_bd_connection()

    # Prueba 2: Funciones de consulta
    consultas_ok = test_consultas()

    # Prueba 3: Sistema RAG
    rag_ok = test_rag_system()

    print("\n" + "="*50)
    print("🎯 RESUMEN DE PRUEBAS:")
    print(f"✅ Base de Datos: {'OK' if bd_ok else 'FAIL'}")
    print(f"✅ Consultas: {'OK' if consultas_ok else 'FAIL'}")
    print(f"✅ Sistema RAG: {'OK' if rag_ok else 'PARCIAL'}")

    if bd_ok and consultas_ok:
        print("\n🎉 ¡DASH ESTÁ LISTO PARA USAR!")
        print("🌐 Acceder a: http://localhost:8050")
        print("\n📋 EJEMPLOS DE CONSULTAS:")
        print("- Cuantitativa: '¿Cuántas víctimas hay?'")
        print("- Cualitativa: '¿Por qué ocurrieron las masacres?'")
        print("- Híbrida: 'Dame víctimas con contexto'")
    else:
        print("\n❌ Hay problemas que necesitan resolución")

    return bd_ok and consultas_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)