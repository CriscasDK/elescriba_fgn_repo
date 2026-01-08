#!/usr/bin/env python3
"""
Script simple para monitorear el progreso de la corrección
verificando algunos documentos actualizados recientemente
"""

import asyncio
import os
import sys
from dotenv import load_dotenv
from azure.search.documents.aio import SearchClient
from azure.core.credentials import AzureKeyCredential
import time

# Cargar configuración
load_dotenv('config/.env')

async def monitorear_progreso():
    """Monitorea el progreso de la corrección"""
    print("📊 MONITOREANDO PROGRESO DE CORRECCIÓN")
    print("=" * 60)
    
    endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
    key = os.getenv('AZURE_SEARCH_KEY')
    
    indices = [
        ('exhaustive-legal-index', 'Documentos'),
        ('exhaustive-legal-chunks-v2', 'Chunks')
    ]
    
    for index_name, tipo in indices:
        print(f"\n📋 {tipo} ({index_name})")
        print("-" * 40)
        
        search_client = SearchClient(
            endpoint=endpoint,
            index_name=index_name,
            credential=AzureKeyCredential(key)
        )
        
        try:
            # Contar total
            count_result = await search_client.search(search_text="*", top=0, include_total_count=True)
            total = await count_result.get_count()
            
            # Contar documentos con campos poblados
            if index_name == 'exhaustive-legal-index':
                filter_query = "metadatos_nuc ne null and metadatos_nuc ne ''"
                campo_verificacion = 'metadatos_nuc'
            else:
                filter_query = "nuc ne null and nuc ne ''"
                campo_verificacion = 'nuc'
            
            results = await search_client.search(
                search_text="*",
                filter=filter_query,
                top=0,
                include_total_count=True
            )
            poblados = await results.get_count()
            
            porcentaje = (poblados / total * 100) if total > 0 else 0
            
            print(f"   Total documentos: {total:,}")
            print(f"   Con {campo_verificacion} poblado: {poblados:,}")
            print(f"   Progreso: {porcentaje:.1f}%")
            
            # Mostrar algunos ejemplos recientes
            print(f"   Últimas actualizaciones:")
            
            sample_results = await search_client.search(
                search_text="*",
                filter=filter_query,
                top=3
            )
            
            count = 0
            async for doc in sample_results:
                count += 1
                doc_id = doc.get('id', doc.get('chunk_id', 'N/A'))
                campo_valor = doc.get(campo_verificacion, 'N/A')
                print(f"     {count}. {doc_id[:50]}... -> {campo_valor}")
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        finally:
            await search_client.close()

async def main():
    await monitorear_progreso()
    print(f"\n⏱️  Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    sys.path.append(os.path.dirname(__file__))
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
    
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ Error: {e}")