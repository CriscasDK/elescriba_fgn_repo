#!/usr/bin/env python3
"""
Verificación específica de resultados del poblamiento geográfico
"""

import asyncio
import os
from dotenv import load_dotenv
from azure.search.documents.aio import SearchClient
from azure.core.credentials import AzureKeyCredential

load_dotenv('config/.env')

async def verificar_resultados():
    """Verifica resultados específicos del poblamiento"""
    print("📊 VERIFICACIÓN ESPECÍFICA - POBLAMIENTO GEOGRÁFICO")
    print("=" * 70)
    
    endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
    key = os.getenv('AZURE_SEARCH_KEY')
    
    # 1. Verificar exhaustive-legal-index
    print("\n📋 EXHAUSTIVE-LEGAL-INDEX (lugares_hechos):")
    search_client = SearchClient(endpoint, 'exhaustive-legal-index', AzureKeyCredential(key))
    
    try:
        # Buscar documentos con lugares_hechos específicamente
        results = await search_client.search(
            search_text="*",
            top=5,
            select="id,archivo,lugares_hechos"
        )
        
        poblados = 0
        total = 0
        
        async for doc in results:
            total += 1
            lugares = doc.get('lugares_hechos')
            
            if lugares and str(lugares).strip():
                poblados += 1
                archivo = doc.get('archivo', '')
                archivo_corto = os.path.basename(archivo)[:30] if archivo else "Sin archivo"
                print(f"   ✅ {archivo_corto}... → {lugares}")
            else:
                print(f"   ❌ Sin lugares: {doc.get('id', 'Sin ID')}")
        
        print(f"\n   📊 Muestra: {poblados}/{total} con lugares_hechos")
        
    finally:
        await search_client.close()
    
    # 2. Verificar exhaustive-legal-chunks-v2
    print(f"\n📋 EXHAUSTIVE-LEGAL-CHUNKS-V2 (lugares_chunk):")
    search_client = SearchClient(endpoint, 'exhaustive-legal-chunks-v2', AzureKeyCredential(key))
    
    try:
        # Buscar chunks con lugares_chunk
        results = await search_client.search(
            search_text="*",
            top=5,
            select="chunk_id,nombre_archivo,lugares_chunk"
        )
        
        poblados = 0
        total = 0
        
        async for chunk in results:
            total += 1
            lugares = chunk.get('lugares_chunk')
            
            if lugares and str(lugares).strip():
                poblados += 1
                archivo = chunk.get('nombre_archivo', '')
                archivo_corto = os.path.basename(archivo)[:30] if archivo else "Sin archivo"
                print(f"   ✅ {archivo_corto}... → {lugares}")
            else:
                chunk_id = chunk.get('chunk_id', 'Sin ID')
                print(f"   ❌ Sin lugares: {chunk_id[:30]}...")
        
        print(f"\n   📊 Muestra: {poblados}/{total} con lugares_chunk")
        
    finally:
        await search_client.close()
    
    # 3. Hacer búsquedas específicas para confirmar poblamiento
    print(f"\n🔍 BÚSQUEDAS ESPECÍFICAS:")
    
    # Buscar por departamento
    search_client = SearchClient(endpoint, 'exhaustive-legal-index', AzureKeyCredential(key))
    try:
        antioquia_results = await search_client.search(
            search_text="Antioquia",
            top=3,
            select="id,lugares_hechos"
        )
        
        print(f"\n   🌍 Documentos con 'Antioquia' en lugares_hechos:")
        count = 0
        async for doc in antioquia_results:
            count += 1
            lugares = doc.get('lugares_hechos', '')
            if lugares and 'Antioquia' in str(lugares):
                print(f"      ✅ {lugares}")
        
        if count == 0:
            print("      ❌ No se encontraron documentos con Antioquia")
        
    finally:
        await search_client.close()

async def main():
    await verificar_resultados()

if __name__ == "__main__":
    asyncio.run(main())