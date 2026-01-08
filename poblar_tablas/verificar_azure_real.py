#!/usr/bin/env python3
"""
Verificación REAL del estado de campos geográficos en Azure Search
Verificación directa contra los índices para confirmar poblamiento
"""

import asyncio
import os
from dotenv import load_dotenv
from azure.search.documents.aio import SearchClient
from azure.core.credentials import AzureKeyCredential

load_dotenv('config/.env')

async def verificar_azure_real():
    """Verificación directa y real del estado en Azure Search"""
    print("🔍 VERIFICACIÓN REAL - ESTADO AZURE SEARCH")
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
            # 1. Obtener muestra de documentos con TODOS los campos
            print("🔍 Obteniendo muestra de documentos...")
            
            # Seleccionar campos según el índice
            if index_name == 'exhaustive-legal-chunks-v2':
                select_fields = f"{id_field},nombre_archivo,{campo_lugares}"
            else:
                select_fields = f"{id_field},archivo,{campo_lugares}"
            
            results = await search_client.search(
                search_text="*",
                top=20,  # Muestra más grande
                select=select_fields
            )
            
            total_revisados = 0
            con_lugares_poblados = 0
            sin_lugares = 0
            ejemplos_poblados = []
            ejemplos_sin_poblar = []
            
            async for doc in results:
                total_revisados += 1
                
                valor_lugares = doc.get(campo_lugares)
                archivo = doc.get('archivo', '') or doc.get('nombre_archivo', '')
                id_doc = doc.get(id_field, 'Sin ID')
                
                print(f"\n   📄 Doc {total_revisados}:")
                print(f"      ID: {str(id_doc)[:50]}...")
                print(f"      Archivo: {os.path.basename(archivo)[:50]}..." if archivo else "      Archivo: No disponible")
                print(f"      {campo_lugares}: {valor_lugares}")
                
                if valor_lugares and str(valor_lugares).strip():
                    con_lugares_poblados += 1
                    if len(ejemplos_poblados) < 3:
                        ejemplos_poblados.append({
                            'archivo': os.path.basename(archivo) if archivo else 'Sin archivo',
                            'lugares': str(valor_lugares)
                        })
                    print(f"      ✅ POBLADO")
                else:
                    sin_lugares += 1
                    if len(ejemplos_sin_poblar) < 3:
                        ejemplos_sin_poblar.append({
                            'archivo': os.path.basename(archivo) if archivo else 'Sin archivo',
                            'id': str(id_doc)[:30]
                        })
                    print(f"      ❌ SIN POBLAR")
            
            # Resumen
            porcentaje = (con_lugares_poblados / total_revisados * 100) if total_revisados > 0 else 0
            
            print(f"\n📊 RESUMEN MUESTRA ({total_revisados} documentos):")
            print(f"   ✅ Con {campo_lugares} poblado: {con_lugares_poblados}")
            print(f"   ❌ Sin {campo_lugares}: {sin_lugares}")
            print(f"   📈 Porcentaje poblado: {porcentaje:.1f}%")
            
            if ejemplos_poblados:
                print(f"\n🌍 EJEMPLOS POBLADOS:")
                for i, ejemplo in enumerate(ejemplos_poblados, 1):
                    print(f"   {i}. {ejemplo['archivo'][:40]} → {ejemplo['lugares'][:60]}")
            
            if ejemplos_sin_poblar:
                print(f"\n❌ EJEMPLOS SIN POBLAR:")
                for i, ejemplo in enumerate(ejemplos_sin_poblar, 1):
                    print(f"   {i}. {ejemplo['archivo'][:40]} (ID: {ejemplo['id']})")
            
            # 2. Intentar búsqueda específica por lugares conocidos
            print(f"\n🔍 BÚSQUEDA ESPECÍFICA POR 'Antioquia':")
            try:
                antioquia_results = await search_client.search(
                    search_text="Antioquia",
                    top=5,
                    select=f"{id_field},{campo_lugares}"
                )
                
                encontrados = 0
                async for doc in antioquia_results:
                    lugares = doc.get(campo_lugares, '')
                    if lugares and 'Antioquia' in str(lugares):
                        encontrados += 1
                        print(f"   ✅ Encontrado: {lugares}")
                        if encontrados >= 3:
                            break
                
                if encontrados == 0:
                    print("   ❌ No se encontraron documentos con 'Antioquia' en lugares")
                else:
                    print(f"   📊 Total con Antioquia encontrados: {encontrados}")
                    
            except Exception as e:
                print(f"   ❌ Error en búsqueda: {e}")
        
        finally:
            await search_client.close()
    
    print(f"\n{'='*80}")
    print("🎯 CONCLUSIÓN VERIFICACIÓN REAL:")
    print("   Si ves muchos campos ❌ SIN POBLAR, el poblamiento no fue efectivo")
    print("   Si ves ✅ POBLADO con lugares reales, el poblamiento fue exitoso")
    print(f"{'='*80}")

async def main():
    await verificar_azure_real()

if __name__ == "__main__":
    asyncio.run(main())