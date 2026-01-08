#!/usr/bin/env python3
"""
Resumen final del estado de campos para filtros de interfaz
"""

import asyncio
import os
import sys
from dotenv import load_dotenv
from azure.search.documents.aio import SearchClient
from azure.core.credentials import AzureKeyCredential

# Cargar configuración
load_dotenv('config/.env')

async def generar_resumen_filtros():
    """Genera resumen final de campos para filtros"""
    print("🎯 RESUMEN FINAL: CAMPOS PARA FILTROS DE INTERFAZ")
    print("=" * 80)
    
    endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
    key = os.getenv('AZURE_SEARCH_KEY')
    
    # Mapeo correcto basado en análisis
    mapeo_filtros = {
        'exhaustive-legal-index': {
            'NUC (multiselect)': 'metadatos_nuc',
            'Fecha inicio/fin (date)': 'metadatos_fecha_creacion', 
            'Despacho (selectbox)': 'metadatos_despacho',
            'Tipo documento (selectbox)': 'tipo_documento',
            'Departamento (selectbox)': '❌ No existe',
            'Municipio (selectbox)': '❌ No existe'
        },
        'exhaustive-legal-chunks-v2': {
            'NUC (multiselect)': 'nuc',
            'Fecha inicio/fin (date)': '❌ No existe',
            'Tipo documento (selectbox)': 'tipo_documento',
            'Departamento (selectbox)': '❌ No existe', 
            'Municipio (selectbox)': '❌ No existe'
        }
    }
    
    # Verificar estado de cada campo
    indices = [
        ('exhaustive-legal-index', 'Documentos Completos'),
        ('exhaustive-legal-chunks-v2', 'Chunks con Trazabilidad')
    ]
    
    estadisticas_finales = {}
    
    for index_name, descripcion in indices:
        print(f"\n📋 {descripcion} ({index_name})")
        print("-" * 60)
        
        search_client = SearchClient(
            endpoint=endpoint,
            index_name=index_name,
            credential=AzureKeyCredential(key)
        )
        
        try:
            # Total documentos
            count_result = await search_client.search(search_text="*", top=0, include_total_count=True)
            total = await count_result.get_count()
            print(f"📊 Total documentos: {total:,}")
            
            stats_indice = {'total': total, 'campos': {}}
            
            # Verificar cada campo del mapeo
            mapeo_indice = mapeo_filtros[index_name]
            
            for filtro_interfaz, campo_azure in mapeo_indice.items():
                if campo_azure == '❌ No existe':
                    print(f"   ❌ {filtro_interfaz}: Campo no existe en esquema")
                    stats_indice['campos'][filtro_interfaz] = {'estado': 'no_existe', 'porcentaje': 0}
                else:
                    try:
                        # Contar documentos con campo poblado
                        if 'fecha' in campo_azure:
                            # Para fechas, verificar que no sean null y no estén vacías
                            filter_query = f"{campo_azure} ne null"
                        else:
                            # Para otros campos
                            filter_query = f"{campo_azure} ne null and {campo_azure} ne ''"
                        
                        results = await search_client.search(
                            search_text="*",
                            filter=filter_query,
                            top=0,
                            include_total_count=True
                        )
                        poblados = await results.get_count()
                        porcentaje = (poblados / total * 100) if total > 0 else 0
                        
                        estado = "✅" if porcentaje >= 80 else "🔄" if porcentaje >= 50 else "❌"
                        print(f"   {estado} {filtro_interfaz}: {poblados:,}/{total:,} ({porcentaje:.1f}%)")
                        
                        stats_indice['campos'][filtro_interfaz] = {
                            'campo_azure': campo_azure,
                            'poblados': poblados,
                            'porcentaje': porcentaje,
                            'estado': 'ok' if porcentaje >= 80 else 'parcial' if porcentaje >= 50 else 'faltante'
                        }
                        
                    except Exception as e:
                        print(f"   ❓ {filtro_interfaz}: Error - {str(e)[:50]}...")
                        stats_indice['campos'][filtro_interfaz] = {'estado': 'error', 'error': str(e)}
            
            estadisticas_finales[index_name] = stats_indice
            
        except Exception as e:
            print(f"   ❌ Error general: {e}")
        
        finally:
            await search_client.close()
    
    # Generar plan de acción
    print(f"\n{'='*80}")
    print("🎯 PLAN DE ACCIÓN PARA FILTROS FUNCIONALES")
    print(f"{'='*80}")
    
    acciones_prioritarias = []
    
    for index_name, stats in estadisticas_finales.items():
        for filtro, datos in stats['campos'].items():
            estado = datos.get('estado')
            porcentaje = datos.get('porcentaje', 0)
            
            if estado == 'faltante' and porcentaje < 50:
                acciones_prioritarias.append({
                    'indice': index_name,
                    'filtro': filtro,
                    'campo': datos.get('campo_azure'),
                    'porcentaje': porcentaje,
                    'prioridad': 'ALTA'
                })
            elif estado == 'parcial':
                acciones_prioritarias.append({
                    'indice': index_name,
                    'filtro': filtro,
                    'campo': datos.get('campo_azure'),
                    'porcentaje': porcentaje,
                    'prioridad': 'MEDIA'
                })
            elif estado == 'no_existe':
                acciones_prioritarias.append({
                    'indice': index_name,
                    'filtro': filtro,
                    'campo': 'NUEVO CAMPO REQUERIDO',
                    'porcentaje': 0,
                    'prioridad': 'ESQUEMA'
                })
    
    print("\n🔴 ACCIONES PRIORITARIAS:")
    for accion in sorted(acciones_prioritarias, key=lambda x: (x['prioridad'], -x['porcentaje'])):
        print(f"   • {accion['filtro']} en {accion['indice']}")
        print(f"     Campo: {accion['campo']} | Actual: {accion['porcentaje']:.1f}% | Prioridad: {accion['prioridad']}")
        
        if accion['prioridad'] == 'ESQUEMA':
            print(f"     📝 Acción: Agregar campo al esquema de Azure Search")
        elif accion['prioridad'] == 'ALTA':
            print(f"     📝 Acción: Poblar campo desde PostgreSQL")
        else:
            print(f"     📝 Acción: Completar poblamiento existente")
        print()
    
    print(f"\n✅ FILTROS FUNCIONALES (>80% poblados):")
    for index_name, stats in estadisticas_finales.items():
        filtros_ok = [f for f, d in stats['campos'].items() if d.get('porcentaje', 0) >= 80]
        if filtros_ok:
            print(f"   {index_name}: {', '.join(filtros_ok)}")
    
    print(f"\n{'='*80}")

async def main():
    await generar_resumen_filtros()

if __name__ == "__main__":
    sys.path.append(os.path.dirname(__file__))
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
    
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()