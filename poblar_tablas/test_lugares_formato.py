#!/usr/bin/env python3
"""
Script de prueba para verificar el formato correcto de campos de lugares
"""

import asyncio
import os
from dotenv import load_dotenv
from azure.search.documents.aio import SearchClient
from azure.core.credentials import AzureKeyCredential

load_dotenv('config/.env')

async def test_formato_lugares():
    """Prueba diferentes formatos para campos de lugares"""
    print("🧪 PROBANDO FORMATOS DE CAMPOS LUGARES")
    print("=" * 50)
    
    endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
    key = os.getenv('AZURE_SEARCH_KEY')
    
    # Probar con exhaustive-legal-index
    search_client = SearchClient(
        endpoint=endpoint,
        index_name='exhaustive-legal-index',
        credential=AzureKeyCredential(key)
    )
    
    try:
        # Obtener un documento para ver su estructura
        results = await search_client.search(search_text="*", top=1, select="id,lugares_hechos")
        
        async for doc in results:
            doc_id = doc['id']
            lugares_actuales = doc.get('lugares_hechos', None)
            
            print(f"📋 Documento ID: {doc_id}")
            print(f"📋 lugares_hechos actual: {lugares_actuales}")
            print(f"📋 Tipo: {type(lugares_actuales)}")
            
            # Probar formatos diferentes
            formatos_test = [
                # Formato 1: Lista de strings
                ["Antioquia", "Medellín"],
                
                # Formato 2: String con separador
                "Antioquia | Medellín",
                
                # Formato 3: String simple
                "Antioquia, Medellín"
            ]
            
            for i, formato in enumerate(formatos_test, 1):
                try:
                    print(f"\n🧪 Probando formato {i}: {formato} (tipo: {type(formato)})")
                    
                    test_doc = {
                        "id": doc_id,
                        "lugares_hechos": formato
                    }
                    
                    result = await search_client.merge_or_upload_documents([test_doc])
                    if result and result[0].succeeded:
                        print(f"   ✅ Formato {i} EXITOSO")
                        
                        # Verificar el resultado
                        verify_results = await search_client.search(
                            search_text="*",
                            filter=f"id eq '{doc_id}'",
                            select="lugares_hechos"
                        )
                        async for verify_doc in verify_results:
                            print(f"   📋 Resultado guardado: {verify_doc.get('lugares_hechos')}")
                        
                        break  # Usar el primer formato exitoso
                    else:
                        print(f"   ❌ Formato {i} falló en resultado")
                        
                except Exception as e:
                    print(f"   ❌ Formato {i} falló: {str(e)[:100]}")
            
            break  # Solo probar con un documento
    
    finally:
        await search_client.close()

async def main():
    await test_formato_lugares()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()