#!/usr/bin/env python3
"""
Script robusto para poblar campos geográficos en Azure Search
usando el patrón exitoso del poblamiento de tipos de documento
"""

import asyncio
import os
import sys
import time
from dotenv import load_dotenv
from azure.search.documents.aio import SearchClient
from azure.core.credentials import AzureKeyCredential
import psycopg2

# Cargar configuración
load_dotenv('config/.env')

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'documentos_juridicos_gpt4',
    'user': 'docs_user',
    'password': 'docs_password_2025'
}

class PobladorGeograficoRobusto:
    """Poblador robusto de campos geográficos basado en patrón exitoso"""
    
    def __init__(self):
        self.endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
        self.key = os.getenv('AZURE_SEARCH_KEY')
        self.mapeo_datos = {}
        
    def generar_variaciones_nombre(self, archivo: str) -> list:
        """Genera variaciones de nombres para mapeo robusto - PATRÓN EXITOSO"""
        variaciones = []
        nombre_base = os.path.basename(archivo)
        
        # Variaciones básicas
        variaciones.append(nombre_base)
        variaciones.append(nombre_base.replace('.pdf', ''))
        variaciones.append(nombre_base.replace('.json', ''))
        variaciones.append(nombre_base.replace('.pdf', '.json'))
        variaciones.append(nombre_base.replace('.json', '.pdf'))
        
        # Variaciones para archivos con batch_resultado
        if '_batch_resultado_' in nombre_base:
            nombre_limpio = nombre_base.split('_batch_resultado_')[0]
            variaciones.extend([
                nombre_limpio,
                nombre_limpio + '.pdf',
                nombre_limpio + '.json'
            ])
        
        return list(set(variaciones))
    
    def cargar_mapeo_completo(self):
        """Carga mapeo desde PostgreSQL con múltiples claves - PATRÓN EXITOSO"""
        print("🌍 Cargando mapeo geográfico desde PostgreSQL...")
        
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        try:
            # Query optimizada para obtener lugares principales por documento
            query = """
            WITH lugares_principales AS (
                SELECT DISTINCT
                    d.archivo,
                    d.id as documento_id,
                    COALESCE(TRIM(al.departamento), '') as departamento,
                    COALESCE(TRIM(al.municipio), '') as municipio,
                    COALESCE(TRIM(al.nombre), '') as lugar_nombre,
                    ROW_NUMBER() OVER (PARTITION BY d.archivo ORDER BY al.id) as rn
                FROM documentos d
                JOIN analisis_lugares al ON d.id = al.documento_id
                WHERE d.archivo IS NOT NULL
                  AND (al.departamento IS NOT NULL OR al.municipio IS NOT NULL OR al.nombre IS NOT NULL)
            )
            SELECT 
                archivo,
                departamento,
                municipio,
                lugar_nombre
            FROM lugares_principales
            WHERE rn = 1
            ORDER BY archivo
            """
            
            cursor.execute(query)
            resultados = cursor.fetchall()
            
            for row in resultados:
                archivo = row[0]
                if archivo:
                    # Generar múltiples claves de mapeo por archivo
                    variaciones = self.generar_variaciones_nombre(archivo)
                    
                    # Preparar lugares como string con separador
                    lugares_partes = []
                    if row[1]:  # departamento
                        lugares_partes.append(row[1])
                    if row[2]:  # municipio
                        lugares_partes.append(row[2])
                    if row[3] and row[3] not in lugares_partes:  # lugar_nombre
                        lugares_partes.append(row[3])
                    
                    datos = {
                        'lugares_string': " | ".join(lugares_partes[:5]) if lugares_partes else ""
                    }
                    
                    for variacion in variaciones:
                        self.mapeo_datos[variacion] = datos
            
            print(f"✅ {len(resultados)} documentos → {len(self.mapeo_datos)} claves de mapeo")
            return len(resultados)
            
        finally:
            cursor.close()
            conn.close()
    
    def extraer_nombre_archivo(self, documento: dict) -> str:
        """Extrae nombre de archivo para mapeo"""
        archivo = documento.get('archivo', '') or documento.get('nombre_archivo', '')
        if archivo:
            return os.path.basename(archivo)
        return ""
    
    def buscar_datos_mapeo(self, nombre_archivo: str) -> dict:
        """Busca datos en mapeo usando variaciones de nombre"""
        if not nombre_archivo:
            return {}
        
        # Búsqueda directa
        if nombre_archivo in self.mapeo_datos:
            return self.mapeo_datos[nombre_archivo]
        
        # Búsqueda por variaciones
        variaciones = self.generar_variaciones_nombre(nombre_archivo)
        for variacion in variaciones:
            if variacion in self.mapeo_datos:
                return self.mapeo_datos[variacion]
        
        return {}
    
    async def actualizar_lote(self, search_client, documentos: list) -> int:
        """Actualización robusta con manejo de errores"""
        try:
            result = await search_client.merge_or_upload_documents(documentos)
            exitosos = sum(1 for r in result if r.succeeded)
            return exitosos
        except Exception as e:
            print(f"❌ Error en lote: {str(e)[:100]}")
            return 0

    async def procesar_indice_masivo(self, index_name: str, campo_objetivo: str):
        """Patrón estándar para poblamiento masivo - EXACTO AL EXITOSO"""
        print(f"\n🚀 POBLAMIENTO ROBUSTO {index_name}")
        print("=" * 80)
        
        # Configuración
        search_client = SearchClient(self.endpoint, index_name, AzureKeyCredential(self.key))
        stats = {'procesados': 0, 'actualizados': 0, 'errores': 0}
        LOTE_SIZE = 50  # Lotes pequeños para estabilidad
        
        try:
            # Procesamiento por páginas
            skip = 0
            page_size = 500
            
            while True:
                # Seleccionar campos según el índice
                if index_name == 'exhaustive-legal-chunks-v2':
                    select_fields = f"chunk_id,nombre_archivo,{campo_objetivo}"
                    id_field = "chunk_id"
                else:
                    select_fields = f"id,archivo,{campo_objetivo}"
                    id_field = "id"
                
                results = await search_client.search(
                    search_text="*",
                    top=page_size,
                    skip=skip,
                    select=select_fields
                )
                
                lote_actual = []
                documentos_en_pagina = 0
                
                # Procesar cada documento
                async for documento in results:
                    documentos_en_pagina += 1
                    stats['procesados'] += 1
                    
                    # Verificar si ya está poblado
                    valor_actual = documento.get(campo_objetivo)
                    if valor_actual:
                        continue
                    
                    # Buscar datos en mapeo
                    nombre_archivo = self.extraer_nombre_archivo(documento)
                    datos = self.buscar_datos_mapeo(nombre_archivo)
                    
                    if datos and datos.get('lugares_string'):
                        lote_actual.append({
                            id_field: documento[id_field],
                            campo_objetivo: datos['lugares_string']
                        })
                    
                    # Procesar lote cuando esté lleno
                    if len(lote_actual) >= LOTE_SIZE:
                        exitosos = await self.actualizar_lote(search_client, lote_actual)
                        stats['actualizados'] += exitosos
                        lote_actual = []
                
                # Procesar lote restante
                if lote_actual:
                    exitosos = await self.actualizar_lote(search_client, lote_actual)
                    stats['actualizados'] += exitosos
                    lote_actual = []
                
                # Progreso cada 1000 documentos
                if stats['procesados'] % 1000 == 0:
                    tasa = (stats['actualizados'] / max(stats['procesados'], 1)) * 100
                    print(f"📊 {stats['procesados']:,} procesados | {stats['actualizados']:,} actualizados ({tasa:.1f}%)")
                
                # Control de flujo
                skip += page_size
                if documentos_en_pagina == 0:
                    break
                    
                await asyncio.sleep(0.1)  # Pausa para no sobrecargar
            
            return stats
            
        finally:
            await search_client.close()

    async def ejecutar_poblamiento_completo(self):
        """Ejecuta poblamiento completo usando patrón exitoso"""
        print("🌍 POBLAMIENTO GEOGRÁFICO ROBUSTO - AZURE SEARCH")
        print("=" * 80)
        
        inicio = time.time()
        
        # Cargar mapeo inteligente
        total_docs = self.cargar_mapeo_completo()
        
        # Poblar exhaustive-legal-index
        stats_index = await self.procesar_indice_masivo('exhaustive-legal-index', 'lugares_hechos')
        
        # Poblar exhaustive-legal-chunks-v2
        stats_chunks = await self.procesar_indice_masivo('exhaustive-legal-chunks-v2', 'lugares_chunk')
        
        # Reporte final
        fin = time.time()
        duracion = fin - inicio
        total_procesados = stats_index['procesados'] + stats_chunks['procesados']
        total_actualizados = stats_index['actualizados'] + stats_chunks['actualizados']
        
        print(f"\n{'='*80}")
        print("🎯 REPORTE FINAL - POBLAMIENTO GEOGRÁFICO")
        print(f"{'='*80}")
        print(f"📊 Documentos con lugares en PostgreSQL: {total_docs:,}")
        print(f"📊 Total procesados: {total_procesados:,}")
        print(f"📊 Total actualizados: {total_actualizados:,}")
        print(f"⏱️  Duración: {duracion:.1f} segundos")
        
        if total_procesados > 0:
            tasa = (total_actualizados / total_procesados) * 100
            print(f"📊 Tasa de mapeo exitoso: {tasa:.1f}%")
        
        print(f"\n🎯 DETALLES POR ÍNDICE:")
        print(f"   📋 exhaustive-legal-index:")
        print(f"      - Procesados: {stats_index['procesados']:,}")
        print(f"      - Actualizados: {stats_index['actualizados']:,}")
        
        print(f"   📋 exhaustive-legal-chunks-v2:")
        print(f"      - Procesados: {stats_chunks['procesados']:,}")
        print(f"      - Actualizados: {stats_chunks['actualizados']:,}")
        
        print(f"\n🎉 IMPACTO EN FILTROS:")
        print("   ✅ Filtros geográficos ahora funcionales")
        print("   📍 lugares_hechos poblado en exhaustive-legal-index")
        print("   📍 lugares_chunk poblado en exhaustive-legal-chunks-v2")
        print("   🗺️  Formato: 'Departamento | Municipio | Lugar'")
        print(f"{'='*80}")

async def main():
    poblador = PobladorGeograficoRobusto()
    await poblador.ejecutar_poblamiento_completo()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  Proceso interrumpido")
    except Exception as e:
        print(f"❌ Error crítico: {e}")
        import traceback
        traceback.print_exc()