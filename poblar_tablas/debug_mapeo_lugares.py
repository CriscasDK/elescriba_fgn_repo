#!/usr/bin/env python3
"""
Script de debug para verificar mapeo entre Azure Search y PostgreSQL
"""

import asyncio
import os
from dotenv import load_dotenv
from azure.search.documents.aio import SearchClient
from azure.core.credentials import AzureKeyCredential
import psycopg2

load_dotenv('config/.env')

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'documentos_juridicos_gpt4',
    'user': 'docs_user',
    'password': 'docs_password_2025'
}

async def debug_mapeo():
    """Debug del mapeo entre archivos"""
    print("🔍 DEBUG MAPEO ARCHIVOS AZURE ↔ POSTGRESQL")
    print("=" * 60)
    
    # 1. Obtener archivos de Azure Search
    endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
    key = os.getenv('AZURE_SEARCH_KEY')
    
    search_client = SearchClient(
        endpoint=endpoint,
        index_name='exhaustive-legal-index',
        credential=AzureKeyCredential(key)
    )
    
    archivos_azure = []
    
    try:
        results = await search_client.search(
            search_text="*",
            top=10,
            select="id,archivo"
        )
        
        print("📋 ARCHIVOS EN AZURE SEARCH:")
        async for doc in results:
            archivo = doc.get('archivo', '')
            if archivo:
                nombre = os.path.basename(archivo)
                archivos_azure.append(nombre)
                print(f"   Azure: {nombre}")
    
    finally:
        await search_client.close()
    
    # 2. Obtener archivos de PostgreSQL
    print(f"\n📋 ARCHIVOS EN POSTGRESQL:")
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
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
        nombre = os.path.basename(archivo)
        archivos_pg.append(nombre)
        print(f"   PostgreSQL: {nombre}")
    
    cursor.close()
    conn.close()
    
    # 3. Comparar mapeos
    print(f"\n🔍 ANÁLISIS DE MAPEO:")
    print(f"   Archivos en Azure: {len(archivos_azure)}")
    print(f"   Archivos en PostgreSQL: {len(archivos_pg)}")
    
    # Buscar coincidencias
    print(f"\n🎯 COINCIDENCIAS DIRECTAS:")
    coincidencias = 0
    for archivo_azure in archivos_azure:
        if archivo_azure in archivos_pg:
            print(f"   ✅ {archivo_azure}")
            coincidencias += 1
        else:
            print(f"   ❌ {archivo_azure}")
    
    print(f"\n📊 Total coincidencias directas: {coincidencias}/{len(archivos_azure)}")
    
    # Buscar coincidencias por patrón
    print(f"\n🔍 BÚSQUEDA POR PATRONES:")
    for archivo_azure in archivos_azure[:3]:
        print(f"\n🔍 Buscando matches para: {archivo_azure}")
        
        # Extraer parte base (sin _batch_resultado_)
        if '_batch_resultado_' in archivo_azure:
            base = archivo_azure.split('_batch_resultado_')[0]
            print(f"   Base extraída: {base}")
            
            # Buscar en PostgreSQL
            for archivo_pg in archivos_pg:
                if base in archivo_pg:
                    print(f"   🎯 Posible match: {archivo_pg}")

async def main():
    await debug_mapeo()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ Error: {e}")