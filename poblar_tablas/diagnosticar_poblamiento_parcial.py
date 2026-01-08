#!/usr/bin/env python3
"""
Diagnóstico del poblamiento parcial y análisis de mapeo real
"""

import asyncio
import os
import psycopg2
from dotenv import load_dotenv
from azure.search.documents.aio import SearchClient
from azure.core.credentials import AzureKeyCredential

load_dotenv('config/.env')

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'documentos_juridicos_gpt4',
    'user': 'docs_user',
    'password': 'docs_password_2025'
}

async def diagnosticar_mapeo():
    """Diagnostica el problema de mapeo"""
    print("🔍 DIAGNÓSTICO DE MAPEO - POBLAMIENTO PARCIAL")
    print("=" * 80)
    
    endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
    key = os.getenv('AZURE_SEARCH_KEY')
    
    # 1. Obtener nombres de archivo de Azure Search
    print("\n📋 OBTENIENDO ARCHIVOS DE AZURE SEARCH...")
    search_client = SearchClient(endpoint, 'exhaustive-legal-index', AzureKeyCredential(key))
    
    archivos_azure = []
    try:
        results = await search_client.search(
            search_text="*",
            top=10,
            select="id,archivo"
        )
        
        async for doc in results:
            archivo = doc.get('archivo', '')
            if archivo:
                nombre_base = os.path.basename(archivo)
                archivos_azure.append(nombre_base)
                print(f"   Azure: {nombre_base}")
    finally:
        await search_client.close()
    
    # 2. Obtener nombres de archivo de PostgreSQL
    print(f"\n📋 OBTENIENDO ARCHIVOS DE POSTGRESQL CON LUGARES...")
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT DISTINCT d.archivo
            FROM documentos d
            JOIN analisis_lugares al ON d.id = al.documento_id
            WHERE d.archivo IS NOT NULL
            LIMIT 10
        """)
        
        archivos_pg = []
        for row in cursor.fetchall():
            archivo = row[0]
            nombre_base = os.path.basename(archivo)
            archivos_pg.append(nombre_base)
            print(f"   PostgreSQL: {nombre_base}")
    finally:
        cursor.close()
        conn.close()
    
    # 3. Análisis de mapeo
    print(f"\n🔍 ANÁLISIS DE MAPEO:")
    print(f"   Archivos Azure: {len(archivos_azure)}")
    print(f"   Archivos PostgreSQL con lugares: {len(archivos_pg)}")
    
    # Verificar coincidencias directas
    coincidencias_directas = 0
    print(f"\n🎯 COINCIDENCIAS DIRECTAS:")
    for archivo_azure in archivos_azure:
        if archivo_azure in archivos_pg:
            print(f"   ✅ {archivo_azure}")
            coincidencias_directas += 1
        else:
            print(f"   ❌ {archivo_azure}")
    
    print(f"\n📊 Coincidencias directas: {coincidencias_directas}/{len(archivos_azure)}")
    
    # Verificar mapeo con variaciones
    print(f"\n🔍 MAPEO CON VARIACIONES:")
    
    def generar_variaciones(archivo):
        variaciones = []
        variaciones.append(archivo)
        variaciones.append(archivo.replace('.pdf', ''))
        variaciones.append(archivo.replace('.json', ''))
        if '_batch_resultado_' in archivo:
            base = archivo.split('_batch_resultado_')[0]
            variaciones.extend([base, base + '.pdf', base + '.json'])
        return list(set(variaciones))
    
    mapeos_exitosos = 0
    for archivo_azure in archivos_azure:
        variaciones = generar_variaciones(archivo_azure)
        encontrado = False
        
        for variacion in variaciones:
            if variacion in archivos_pg:
                print(f"   ✅ {archivo_azure} → {variacion}")
                mapeos_exitosos += 1
                encontrado = True
                break
        
        if not encontrado:
            print(f"   ❌ {archivo_azure} → No hay mapeo")
    
    print(f"\n📊 Mapeos con variaciones exitosos: {mapeos_exitosos}/{len(archivos_azure)}")
    
    # 4. Revisar documentos que SÍ tienen lugares poblados
    print(f"\n🌍 DOCUMENTOS QUE SÍ TIENEN LUGARES POBLADOS:")
    search_client = SearchClient(endpoint, 'exhaustive-legal-index', AzureKeyCredential(key))
    
    try:
        antioquia_results = await search_client.search(
            search_text="Antioquia",
            top=5,
            select="id,archivo,lugares_hechos"
        )
        
        async for doc in antioquia_results:
            lugares = doc.get('lugares_hechos', '')
            archivo = doc.get('archivo', '')
            if lugares and 'Antioquia' in str(lugares):
                archivo_base = os.path.basename(archivo) if archivo else 'Sin archivo'
                print(f"   ✅ {archivo_base[:50]}... → {lugares}")
    finally:
        await search_client.close()

async def main():
    await diagnosticar_mapeo()

if __name__ == "__main__":
    asyncio.run(main())