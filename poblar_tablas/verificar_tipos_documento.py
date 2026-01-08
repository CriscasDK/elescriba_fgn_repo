#!/usr/bin/env python3
"""
Script para verificar estado del campo tipo_documento en Azure Search
"""

import asyncio
import os
import sys
from dotenv import load_dotenv
from azure.search.documents.aio import SearchClient
from azure.core.credentials import AzureKeyCredential

# Cargar configuración
load_dotenv('config/.env')

async def verificar_tipos_documento():
    """Verifica estado de tipo_documento en ambos índices"""
    print("🔍 VERIFICANDO ESTADO DEL CAMPO tipo_documento")
    print("=" * 60)
    
    endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
    key = os.getenv('AZURE_SEARCH_KEY')
    
    indices = [
        ('exhaustive-legal-index', 'Documentos'),
        ('exhaustive-legal-chunks-v2', 'Chunks')
    ]
    
    for index_name, descripcion in indices:
        print(f"\n📋 {descripcion} ({index_name})")
        print("-" * 40)
        
        search_client = SearchClient(
            endpoint=endpoint,
            index_name=index_name,
            credential=AzureKeyCredential(key)
        )
        
        try:
            # Total documentos
            count_result = await search_client.search(search_text="*", top=0, include_total_count=True)
            total = await count_result.get_count()
            
            # Con tipo_documento poblado
            try:
                filter_query = "tipo_documento ne null and tipo_documento ne ''"
                results = await search_client.search(
                    search_text="*",
                    filter=filter_query,
                    top=0,
                    include_total_count=True
                )
                poblados = await results.get_count()
                porcentaje = (poblados / total * 100) if total > 0 else 0
                
                print(f"   Total documentos: {total:,}")
                print(f"   Con tipo_documento poblado: {poblados:,}")
                print(f"   Progreso: {porcentaje:.1f}%")
                
                # Mostrar algunos ejemplos
                if poblados > 0:
                    print("   Ejemplos de tipos:")
                    sample_results = await search_client.search(
                        search_text="*",
                        filter=filter_query,
                        top=5,
                        select="tipo_documento"
                    )
                    
                    tipos_ejemplos = set()
                    async for doc in sample_results:
                        tipo = doc.get('tipo_documento')
                        if tipo:
                            tipos_ejemplos.add(tipo)
                    
                    for i, tipo in enumerate(sorted(tipos_ejemplos), 1):
                        print(f"     {i}. {tipo}")
                
                # Verificar documentos sin tipo
                filter_sin_tipo = "tipo_documento eq null or tipo_documento eq ''"
                results_sin_tipo = await search_client.search(
                    search_text="*",
                    filter=filter_sin_tipo,
                    top=3
                )
                
                print("   Documentos sin tipo_documento:")
                count = 0
                async for doc in results_sin_tipo:
                    count += 1
                    if index_name == 'exhaustive-legal-index':
                        doc_id = doc.get('id', 'N/A')
                        archivo = doc.get('archivo', 'N/A')
                        print(f"     {count}. ID: {doc_id[:30]}... | Archivo: {os.path.basename(archivo) if archivo else 'N/A'}")
                    else:
                        chunk_id = doc.get('chunk_id', 'N/A') 
                        nombre_archivo = doc.get('nombre_archivo', 'N/A')
                        print(f"     {count}. Chunk: {chunk_id[:30]}... | Archivo: {nombre_archivo}")
                
                if count == 0:
                    print("     ✅ Todos los documentos tienen tipo_documento")
                    
            except Exception as e:
                print(f"   ❌ Error verificando tipo_documento: {e}")
        
        except Exception as e:
            print(f"   ❌ Error general: {e}")
        
        finally:
            await search_client.close()

async def main():
    await verificar_tipos_documento()

if __name__ == "__main__":
    sys.path.append(os.path.dirname(__file__))
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
    
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()