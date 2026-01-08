#!/usr/bin/env python3
"""
Script para verificar si las actualizaciones se aplicaron correctamente
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# Agregar path del proyecto
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Cargar configuración
load_dotenv('config/.env')

from azure.search.documents.aio import SearchClient
from azure.core.credentials import AzureKeyCredential

async def verificar_actualizaciones():
    """Verifica si las actualizaciones se aplicaron"""
    print("🔍 VERIFICANDO ACTUALIZACIONES EN AZURE SEARCH")
    print("=" * 80)
    
    endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
    key = os.getenv('AZURE_SEARCH_KEY')
    
    indices = [
        ('exhaustive-legal-index', 'Documentos Completos'),
        ('exhaustive-legal-chunks-v2', 'Chunks con Trazabilidad')
    ]
    
    for index_name, descripcion in indices:
        print(f"\n📋 {descripcion} ({index_name})")
        print("-" * 60)
        
        search_client = SearchClient(
            endpoint=endpoint,
            index_name=index_name,
            credential=AzureKeyCredential(key)
        )
        
        try:
            # Buscar documentos con campos específicos poblados
            campos_busqueda = []
            
            if index_name == 'exhaustive-legal-index':
                # Buscar documentos que TENGAN metadatos poblados
                results = await search_client.search(
                    search_text="*",
                    filter="metadatos_nuc ne null and metadatos_nuc ne ''",
                    top=10
                )
                campos_busqueda = ['metadatos_nuc', 'metadatos_cuaderno', 'personas_todas']
            else:
                # Buscar chunks que TENGAN NUC poblado
                results = await search_client.search(
                    search_text="*", 
                    filter="nuc ne null and nuc ne ''",
                    top=10
                )
                campos_busqueda = ['nuc', 'entidad_productora', 'tipo_documento']
            
            count = 0
            async for result in results:
                count += 1
                print(f"\n✅ Documento {count}:")
                print(f"   ID: {result.get('id', result.get('chunk_id', 'N/A'))}")
                
                for campo in campos_busqueda:
                    valor = result.get(campo, 'NO_EXISTE')
                    if valor and str(valor).strip():
                        print(f"   {campo}: {valor[:100]}...")
                    else:
                        print(f"   {campo}: ❌ VACÍO")
            
            if count == 0:
                print("❌ No se encontraron documentos con campos poblados")
                
                # Verificar algunos documentos aleatorios
                print("\n🔍 Verificando muestra aleatoria:")
                results_sample = await search_client.search(search_text="*", top=3)
                
                sample_count = 0
                async for result in results_sample:
                    sample_count += 1
                    print(f"\n📄 Muestra {sample_count}:")
                    print(f"   ID: {result.get('id', result.get('chunk_id', 'N/A'))}")
                    
                    for campo in campos_busqueda:
                        valor = result.get(campo, 'NO_EXISTE')
                        estado = "✅ LLENO" if valor and str(valor).strip() else "❌ VACÍO"
                        print(f"   {campo}: {estado}")
            else:
                print(f"\n✅ {count} documentos encontrados con campos poblados")
        
        except Exception as e:
            print(f"❌ Error: {e}")
        
        finally:
            await search_client.close()

async def main():
    await verificar_actualizaciones()

if __name__ == "__main__":
    asyncio.run(main())