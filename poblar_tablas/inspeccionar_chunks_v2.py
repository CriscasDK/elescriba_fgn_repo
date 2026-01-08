#!/usr/bin/env python3
"""
Script para inspeccionar el índice exhaustive-legal-chunks-v2
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

async def inspeccionar_chunks_v2():
    """Inspecciona el índice exhaustive-legal-chunks-v2"""
    print("🔍 INSPECCIÓN DE CAMPOS - exhaustive-legal-chunks-v2")
    print("=" * 80)
    
    # Configuración Azure Search
    endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
    key = os.getenv('AZURE_SEARCH_KEY')
    index_name = "exhaustive-legal-chunks-v2"
    
    try:
        # Crear cliente Azure Search
        search_client = SearchClient(
            endpoint=endpoint,
            index_name=index_name,
            credential=AzureKeyCredential(key)
        )
        
        print(f"✅ Conectado a: {endpoint}")
        print(f"📂 Índice: {index_name}")
        print("-" * 80)
        
        # Realizar búsqueda para obtener un documento de muestra
        print("📋 PASO 1: Obteniendo chunk de muestra...")
        
        results = await search_client.search(
            search_text="*",
            top=1,
            include_total_count=True
        )
        
        total_count = await results.get_count()
        print(f"📊 Total chunks en índice: {total_count}")
        print("-" * 80)
        
        documento_muestra = None
        async for result in results:
            documento_muestra = dict(result)
            break
        
        if documento_muestra:
            print("✅ Chunk de muestra obtenido")
            print(f"📄 ID: {documento_muestra.get('chunk_id', 'N/A')}")
            print()
            print("📊 CAMPOS DISPONIBLES EN EL ÍNDICE:")
            print("-" * 40)
            
            for i, (campo, valor) in enumerate(documento_muestra.items(), 1):
                tipo_valor = type(valor).__name__
                if isinstance(valor, str):
                    valor_muestra = valor[:100] + "..." if len(valor) > 100 else valor
                elif isinstance(valor, list):
                    valor_muestra = f"Lista con {len(valor)} elementos"
                else:
                    valor_muestra = str(valor)
                
                print(f"{i:2d}. {campo:30} ({tipo_valor:10}) = {valor_muestra}")
            
            # Analizar campos vacíos
            print("\n" + "=" * 80)
            print("🎯 ANÁLISIS DE CAMPOS CRÍTICOS:")
            print("-" * 40)
            
            campos_criticos = {
                'nuc': 'NUC del expediente',
                'tipo_documento': 'Tipo de documento',
                'entidad_productora': 'Entidad que produce el documento', 
                'personas_chunk': 'Personas mencionadas en el chunk',
                'lugares_chunk': 'Lugares mencionados en el chunk',
                'fechas_chunk': 'Fechas mencionadas en el chunk'
            }
            
            for campo, descripcion in campos_criticos.items():
                valor = documento_muestra.get(campo)
                estado = "✅ LLENO" if valor and str(valor).strip() else "❌ VACÍO"
                print(f"  {campo:20} -> {estado:10} | {descripcion}")
        
        else:
            print("❌ No se pudo obtener documento de muestra")
        
        # Analizar muestra más grande
        print(f"\n{'='*80}")
        print("📊 ANÁLISIS DE MUESTRA (50 chunks):")
        print("-" * 40)
        
        results_sample = await search_client.search(
            search_text="*",
            top=50
        )
        
        campo_stats = {}
        total_muestra = 0
        
        async for result in results_sample:
            total_muestra += 1
            for campo, valor in result.items():
                if campo not in campo_stats:
                    campo_stats[campo] = {'vacios': 0, 'llenos': 0}
                
                if valor is None or valor == '' or (isinstance(valor, list) and len(valor) == 0):
                    campo_stats[campo]['vacios'] += 1
                else:
                    campo_stats[campo]['llenos'] += 1
        
        print(f"Muestra analizada: {total_muestra} chunks")
        print()
        
        # Campos problemáticos
        print("❌ CAMPOS CON PROBLEMAS (>70% vacíos):")
        for campo, stats in campo_stats.items():
            porcentaje_vacio = (stats['vacios'] / total_muestra) * 100
            if porcentaje_vacio > 70:
                print(f"   {campo:25} -> {porcentaje_vacio:5.1f}% vacío")
        
        print()
        print("✅ CAMPOS BIEN POBLADOS (<30% vacíos):")
        for campo, stats in campo_stats.items():
            porcentaje_lleno = (stats['llenos'] / total_muestra) * 100
            if porcentaje_lleno > 70:
                print(f"   {campo:25} -> {porcentaje_lleno:5.1f}% lleno")
    
    except Exception as e:
        print(f"❌ Error durante la inspección: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await search_client.close()

async def main():
    await inspeccionar_chunks_v2()

if __name__ == "__main__":
    asyncio.run(main())