#!/usr/bin/env python3
"""
Monitor de progreso para el poblamiento geográfico
"""

import asyncio
import os
from dotenv import load_dotenv
from azure.search.documents.aio import SearchClient
from azure.core.credentials import AzureKeyCredential

load_dotenv('config/.env')

async def verificar_progreso():
    """Verifica el progreso del poblamiento"""
    print("📊 MONITOR DE PROGRESO GEOGRÁFICO")
    print("=" * 50)
    
    endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
    key = os.getenv('AZURE_SEARCH_KEY')
    
    indices = [
        ('exhaustive-legal-index', 'lugares_hechos'),
        ('exhaustive-legal-chunks-v2', 'lugares_chunk')
    ]
    
    for index_name, campo in indices:
        print(f"\n📋 {index_name}:")
        
        search_client = SearchClient(endpoint, index_name, AzureKeyCredential(key))
        
        try:
            # Total de documentos
            total_results = await search_client.search(search_text="*", top=0, include_total_count=True)
            total_count = await total_results.get_count()
            
            # Documentos con campo poblado - usar consulta sin filtro por compatibilidad
            populated_results = await search_client.search(
                search_text="*",
                top=1000,  # Muestra para calcular
                select=campo
            )
            
            # Contar manualmente los poblados
            populated_count = 0
            total_checked = 0
            async for doc in populated_results:
                total_checked += 1
                valor = doc.get(campo)
                if valor and str(valor).strip():
                    populated_count += 1
            
            # Calcular porcentaje estimado
            if total_checked > 0:
                percentage = (populated_count / total_checked * 100)
            else:
                percentage = 0
            
            print(f"   Total documentos: {total_count:,}")
            print(f"   Con {campo} (muestra de {total_checked}): {populated_count:,}")
            print(f"   Porcentaje poblado (estimado): {percentage:.1f}%")
            
            # Mostrar algunas muestras
            if populated_count > 0:
                print(f"   Muestras de {campo}:")
                sample_count = 0
                async for doc in populated_results:
                    if sample_count >= 3:
                        break
                    valor = doc.get(campo, '')
                    if valor and str(valor).strip():
                        print(f"      - {valor[:80]}{'...' if len(valor) > 80 else ''}")
                        sample_count += 1
        
        finally:
            await search_client.close()

async def main():
    await verificar_progreso()

if __name__ == "__main__":
    asyncio.run(main())