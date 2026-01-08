#!/usr/bin/env python3
"""
Verificar qué campos existen realmente en cada índice de Azure Search
"""

import asyncio
import os
from dotenv import load_dotenv
from azure.search.documents.aio import SearchClient
from azure.core.credentials import AzureKeyCredential

load_dotenv('config/.env')

async def verificar_campos():
    """Verifica campos disponibles en cada índice"""
    print("🔍 VERIFICACIÓN DE CAMPOS EN ÍNDICES DE AZURE SEARCH")
    print("=" * 80)
    
    endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
    key = os.getenv('AZURE_SEARCH_KEY')
    
    indices = ['exhaustive-legal-index', 'exhaustive-legal-chunks-v2']
    
    for index_name in indices:
        print(f"\n📋 {index_name.upper()}:")
        print("-" * 50)
        
        search_client = SearchClient(endpoint, index_name, AzureKeyCredential(key))
        
        try:
            # Obtener un documento de muestra sin especificar campos
            results = await search_client.search(
                search_text="*",
                top=1
            )
            
            async for doc in results:
                print(f"📄 Documento de muestra:")
                campos = list(doc.keys())
                campos.sort()
                
                for campo in campos:
                    valor = doc.get(campo)
                    tipo_valor = type(valor).__name__
                    valor_muestra = str(valor)[:50] if valor else "None"
                    print(f"   {campo}: {tipo_valor} = {valor_muestra}{'...' if len(str(valor)) > 50 else ''}")
                
                print(f"\n📊 Total campos encontrados: {len(campos)}")
                break
        
        finally:
            await search_client.close()

async def main():
    await verificar_campos()

if __name__ == "__main__":
    asyncio.run(main())