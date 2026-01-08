#!/usr/bin/env python3
"""
Script para verificar estado del campo metadatos_fecha_creacion en Azure Search
"""

import asyncio
import os
import sys
from dotenv import load_dotenv
from azure.search.documents.aio import SearchClient
from azure.core.credentials import AzureKeyCredential

# Cargar configuración
load_dotenv('config/.env')

async def verificar_campo_fecha():
    """Verifica estado de metadatos_fecha_creacion"""
    print("🔍 VERIFICANDO CAMPO metadatos_fecha_creacion")
    print("=" * 60)
    
    endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
    key = os.getenv('AZURE_SEARCH_KEY')
    
    # Solo exhaustive-legal-index tiene metadatos_fecha_creacion
    search_client = SearchClient(
        endpoint=endpoint,
        index_name='exhaustive-legal-index',
        credential=AzureKeyCredential(key)
    )
    
    try:
        # Total documentos
        count_result = await search_client.search(search_text="*", top=0, include_total_count=True)
        total = await count_result.get_count()
        
        # Con metadatos_fecha_creacion poblado
        filter_query = "metadatos_fecha_creacion ne null"
        results = await search_client.search(
            search_text="*",
            filter=filter_query,
            top=0,
            include_total_count=True
        )
        poblados = await results.get_count()
        porcentaje = (poblados / total * 100) if total > 0 else 0
        
        print(f"📊 Total documentos: {total:,}")
        print(f"📊 Con metadatos_fecha_creacion poblado: {poblados:,}")
        print(f"📊 Progreso: {porcentaje:.1f}%")
        
        # Mostrar algunos ejemplos de fechas
        if poblados > 0:
            print("\n📅 Ejemplos de fechas:")
            sample_results = await search_client.search(
                search_text="*",
                filter=filter_query,
                top=5,
                select="metadatos_fecha_creacion,archivo"
            )
            
            count = 0
            async for doc in sample_results:
                count += 1
                fecha = doc.get('metadatos_fecha_creacion')
                archivo = doc.get('archivo', 'N/A')
                nombre_archivo = os.path.basename(archivo) if archivo else 'N/A'
                print(f"   {count}. Fecha: {fecha} | Archivo: {nombre_archivo}")
        
        # Verificar documentos sin fecha
        filter_sin_fecha = "metadatos_fecha_creacion eq null"
        results_sin_fecha = await search_client.search(
            search_text="*",
            filter=filter_sin_fecha,
            top=3,
            select="id,archivo"
        )
        
        print(f"\n📋 Documentos sin metadatos_fecha_creacion:")
        count = 0
        async for doc in results_sin_fecha:
            count += 1
            doc_id = doc.get('id', 'N/A')
            archivo = doc.get('archivo', 'N/A')
            nombre_archivo = os.path.basename(archivo) if archivo else 'N/A'
            print(f"   {count}. ID: {doc_id[:30]}... | Archivo: {nombre_archivo}")
        
        if count == 0:
            print("   ✅ Todos los documentos tienen metadatos_fecha_creacion")
        
        # Análisis de disponibilidad para chunks-v2
        print(f"\n📋 Para exhaustive-legal-chunks-v2:")
        print("   ❌ No tiene campo de fecha equivalente")
        print("   📝 Se podría agregar fecha_documento o usar fecha_indexacion")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        await search_client.close()

async def main():
    await verificar_campo_fecha()

if __name__ == "__main__":
    sys.path.append(os.path.dirname(__file__))
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
    
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()