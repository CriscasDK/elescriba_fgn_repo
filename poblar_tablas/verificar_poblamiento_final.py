#!/usr/bin/env python3
"""
Verificación final completa del poblamiento geográfico
"""

import asyncio
import os
import random
from dotenv import load_dotenv
from azure.search.documents.aio import SearchClient
from azure.core.credentials import AzureKeyCredential

load_dotenv('config/.env')

async def verificar_poblamiento_final():
    """Verificación final del poblamiento con muestras aleatorias"""
    print("🎯 VERIFICACIÓN FINAL - POBLAMIENTO GEOGRÁFICO")
    print("=" * 80)
    
    endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
    key = os.getenv('AZURE_SEARCH_KEY')
    
    indices = [
        ('exhaustive-legal-index', 'lugares_hechos', 'id'),
        ('exhaustive-legal-chunks-v2', 'lugares_chunk', 'chunk_id')
    ]
    
    for index_name, campo_lugares, id_field in indices:
        print(f"\n📋 {index_name.upper()}:")
        print("-" * 60)
        
        search_client = SearchClient(endpoint, index_name, AzureKeyCredential(key))
        
        try:
            # 1. Estadística general por muestreo
            print("📊 ESTADÍSTICA GENERAL (muestra aleatoria):")
            
            total_muestreado = 0
            total_poblado = 0
            ejemplos_poblados = []
            
            # Muestrear desde diferentes posiciones
            posiciones = [0, 5000, 15000, 25000, 35000, 45000, 55000, 65000, 75000, 85000]
            
            for skip_pos in posiciones:
                try:
                    results = await search_client.search(
                        search_text="*",
                        top=100,
                        skip=skip_pos,
                        select=f"{id_field},{campo_lugares}"
                    )
                    
                    async for doc in results:
                        total_muestreado += 1
                        valor_lugares = doc.get(campo_lugares)
                        
                        if valor_lugares and str(valor_lugares).strip():
                            total_poblado += 1
                            if len(ejemplos_poblados) < 5 and len(str(valor_lugares)) > 3:
                                ejemplos_poblados.append(str(valor_lugares)[:80])
                        
                        if total_muestreado % 200 == 0:
                            porcentaje = (total_poblado / total_muestreado * 100) if total_muestreado > 0 else 0
                            print(f"      Procesados: {total_muestreado:,} | Poblados: {total_poblado:,} ({porcentaje:.1f}%)")
                            
                        if total_muestreado >= 1000:
                            break
                    
                    if total_muestreado >= 1000:
                        break
                        
                except Exception as e:
                    if "skip" in str(e).lower():
                        continue  # Posición fuera de rango
                    break
            
            # Resultado final de la muestra
            porcentaje_final = (total_poblado / total_muestreado * 100) if total_muestreado > 0 else 0
            print(f"\n   📊 RESULTADO MUESTREO:")
            print(f"      Total muestreado: {total_muestreado:,}")
            print(f"      Con {campo_lugares}: {total_poblado:,}")
            print(f"      Porcentaje poblado: {porcentaje_final:.1f}%")
            
            if ejemplos_poblados:
                print(f"\n   🌍 EJEMPLOS DE LUGARES ENCONTRADOS:")
                for i, ejemplo in enumerate(ejemplos_poblados, 1):
                    print(f"      {i}. {ejemplo}{'...' if len(ejemplo) >= 80 else ''}")
            
            # 2. Verificación por búsqueda específica
            print(f"\n🔍 VERIFICACIÓN POR BÚSQUEDA ESPECÍFICA:")
            
            departamentos_test = ['Antioquia', 'Meta', 'Bogotá', 'Tolima']
            
            for dept in departamentos_test:
                try:
                    results = await search_client.search(
                        search_text=dept,
                        top=0,
                        include_total_count=True
                    )
                    count = await results.get_count()
                    print(f"      📍 Documentos con '{dept}': {count:,}")
                except Exception as e:
                    print(f"      ❌ Error buscando '{dept}': {str(e)[:50]}")
            
            # 3. Estimación extrapolada
            if total_muestreado > 0:
                try:
                    # Obtener total aproximado de documentos
                    total_results = await search_client.search(
                        search_text="*",
                        top=0,
                        include_total_count=True
                    )
                    total_docs = await total_results.get_count()
                    
                    estimacion_poblados = int((total_poblado / total_muestreado) * total_docs)
                    
                    print(f"\n   📈 ESTIMACIÓN EXTRAPOLADA:")
                    print(f"      Total documentos en índice: {total_docs:,}")
                    print(f"      Estimación de poblados: {estimacion_poblados:,}")
                    print(f"      Porcentaje estimado: {porcentaje_final:.1f}%")
                    
                except Exception as e:
                    print(f"      ❌ Error en estimación: {str(e)[:50]}")
        
        finally:
            await search_client.close()
    
    print(f"\n{'='*80}")
    print("🎯 CONCLUSIÓN FINAL:")
    print("   Si ves porcentajes > 0% y ejemplos de lugares, el poblamiento fue exitoso")
    print("   Los primeros documentos pueden seguir sin poblar por el orden de procesamiento")
    print(f"{'='*80}")

async def main():
    await verificar_poblamiento_final()

if __name__ == "__main__":
    asyncio.run(main())