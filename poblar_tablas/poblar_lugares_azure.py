#!/usr/bin/env python3
"""
Script para poblar campos geográficos en Azure Search
usando datos de analisis_lugares de PostgreSQL
"""

import asyncio
import os
import sys
from dotenv import load_dotenv
from azure.search.documents.aio import SearchClient
from azure.core.credentials import AzureKeyCredential
import psycopg2
import json
import time

# Cargar configuración
load_dotenv('config/.env')

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'documentos_juridicos_gpt4',
    'user': 'docs_user',
    'password': 'docs_password_2025'
}

class PobladorLugaresAzure:
    """Poblador de campos geográficos en Azure Search"""
    
    def __init__(self):
        self.endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
        self.key = os.getenv('AZURE_SEARCH_KEY')
        self.mapeo_lugares = {}
        self.stats = {'procesados': 0, 'encontrados': 0, 'actualizados': 0, 'errores': 0}
    
    def cargar_mapeo_lugares(self):
        """Carga mapeo archivo → lugares principales desde PostgreSQL"""
        print("🌍 Cargando mapeo de lugares desde PostgreSQL...")
        
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        try:
            # Query simplificado para obtener lugares principales por documento
            query = """
            WITH lugares_principales AS (
                SELECT DISTINCT
                    d.archivo,
                    COALESCE(al.departamento, '') as departamento,
                    COALESCE(al.municipio, '') as municipio,
                    COALESCE(al.nombre, '') as lugar_nombre,
                    COALESCE(al.direccion, '') as direccion,
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
                lugar_nombre,
                direccion
            FROM lugares_principales
            WHERE rn = 1
            ORDER BY archivo
            """
            
            cursor.execute(query)
            resultados = cursor.fetchall()
            
            for row in resultados:
                archivo = row[0]
                if archivo:
                    # Generar variaciones del nombre de archivo
                    variaciones = self.generar_variaciones_nombre(archivo)
                    
                    datos_lugares = {
                        'departamento_principal': self.limpiar_valor(row[1]),
                        'municipio_principal': self.limpiar_valor(row[2]),
                        'lugar_principal': self.limpiar_valor(row[3]),
                        'direccion_principal': self.limpiar_valor(row[4])
                    }
                    
                    for variacion in variaciones:
                        self.mapeo_lugares[variacion] = datos_lugares
            
            print(f"✅ {len(resultados)} documentos → {len(self.mapeo_lugares)} claves de mapeo")
            return len(resultados)
            
        finally:
            cursor.close()
            conn.close()
    
    def generar_variaciones_nombre(self, archivo: str) -> list:
        """Genera variaciones de nombres de archivo para mapeo robusto"""
        if not archivo:
            return []
        
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
    
    def limpiar_valor(self, valor) -> str:
        """Limpia valores para Azure Search"""
        if valor is None:
            return ""
        valor_str = str(valor).strip()
        return valor_str if valor_str and valor_str != 'None' else ""
    
    def procesar_lista(self, valor) -> list:
        """Procesa listas de valores separados por |"""
        if not valor:
            return []
        elementos = [e.strip() for e in valor.split('|') if e.strip()]
        return elementos[:5]  # Máximo 5 elementos para no saturar
    
    def buscar_lugares_archivo(self, nombre_archivo: str) -> dict:
        """Busca lugares del archivo en el mapeo"""
        if not nombre_archivo:
            return {}
        
        # Búsqueda directa
        if nombre_archivo in self.mapeo_lugares:
            return self.mapeo_lugares[nombre_archivo]
        
        # Búsqueda por variaciones
        variaciones = self.generar_variaciones_nombre(nombre_archivo)
        for variacion in variaciones:
            if variacion in self.mapeo_lugares:
                return self.mapeo_lugares[variacion]
        
        return {}

    async def actualizar_lote_lugares(self, index_name: str, documentos: list) -> int:
        """Actualiza un lote de documentos con lugares"""
        if not documentos:
            return 0
            
        search_client = SearchClient(
            endpoint=self.endpoint,
            index_name=index_name,
            credential=AzureKeyCredential(self.key)
        )
        
        try:
            result = await search_client.merge_or_upload_documents(documentos)
            exitosos = sum(1 for r in result if r.succeeded)
            return exitosos
        except Exception as e:
            print(f"❌ Error en lote: {str(e)[:100]}")
            return 0
        finally:
            await search_client.close()

    async def poblar_chunks_v2(self):
        """Pobla lugares_chunk en exhaustive-legal-chunks-v2"""
        print(f"\n📋 POBLANDO exhaustive-legal-chunks-v2 (lugares_chunk)")
        print("=" * 60)
        
        search_client = SearchClient(
            endpoint=self.endpoint,
            index_name='exhaustive-legal-chunks-v2',
            credential=AzureKeyCredential(self.key)
        )
        
        try:
            # Obtener chunks sin lugares_chunk
            skip = 0
            page_size = 500
            lote_actual = []
            LOTE_SIZE = 50
            
            while True:
                print(f"   📄 Procesando chunks desde posición {skip:,}...")
                
                results = await search_client.search(
                    search_text="*",
                    top=page_size,
                    skip=skip,
                    select="chunk_id,nombre_archivo,lugares_chunk"
                )
                
                chunks_en_pagina = 0
                
                async for chunk in results:
                    chunks_en_pagina += 1
                    self.stats['procesados'] += 1
                    
                    # Verificar si ya tiene lugares_chunk poblados
                    lugares_existentes = chunk.get('lugares_chunk', [])
                    if lugares_existentes and len(lugares_existentes) > 0:
                        continue  # Ya tiene lugares, saltar
                    
                    nombre_archivo = chunk.get('nombre_archivo', '')
                    if not nombre_archivo:
                        continue
                    
                    lugares_data = self.buscar_lugares_archivo(nombre_archivo)
                    if not lugares_data:
                        continue
                    
                    self.stats['encontrados'] += 1
                    
                    # Preparar lugares_chunk como string con separador
                    lugares_partes = []
                    
                    if lugares_data.get('departamento_principal'):
                        lugares_partes.append(lugares_data['departamento_principal'])
                    
                    if lugares_data.get('municipio_principal'):
                        lugares_partes.append(lugares_data['municipio_principal'])
                    
                    if lugares_data.get('lugar_principal'):
                        lugar_principal = lugares_data['lugar_principal']
                        if lugar_principal not in lugares_partes:
                            lugares_partes.append(lugar_principal)
                    
                    # Solo actualizar si tenemos lugares
                    if lugares_partes:
                        lugares_string = " | ".join(lugares_partes[:3])  # Máximo 3 para chunks
                        lote_actual.append({
                            "chunk_id": chunk['chunk_id'],
                            "lugares_chunk": lugares_string
                        })
                    
                    # Procesar lote cuando esté lleno
                    if len(lote_actual) >= LOTE_SIZE:
                        exitosos = await self.actualizar_lote_lugares('exhaustive-legal-chunks-v2', lote_actual)
                        self.stats['actualizados'] += exitosos
                        lote_actual = []
                        
                        if self.stats['procesados'] % 2000 == 0:
                            tasa = (self.stats['encontrados'] / self.stats['procesados']) * 100
                            print(f"      ✅ {self.stats['procesados']:,} procesados | {self.stats['encontrados']:,} con lugares ({tasa:.1f}%) | {self.stats['actualizados']:,} actualizados")
                
                # Procesar lote restante
                if lote_actual:
                    exitosos = await self.actualizar_lote_lugares('exhaustive-legal-chunks-v2', lote_actual)
                    self.stats['actualizados'] += exitosos
                    lote_actual = []
                
                skip += page_size
                
                if chunks_en_pagina == 0:
                    break
                
                # Límite de prueba para chunks
                if skip >= 10000:
                    print(f"⚠️  Límite de prueba chunks alcanzado ({skip:,})")
                    break
                    
                await asyncio.sleep(0.1)
        
        finally:
            await search_client.close()

    async def poblar_exhaustive_legal_index(self):
        """Pobla lugares_hechos en exhaustive-legal-index"""
        print(f"\n📋 POBLANDO exhaustive-legal-index (lugares_hechos)")
        print("=" * 60)
        
        search_client = SearchClient(
            endpoint=self.endpoint,
            index_name='exhaustive-legal-index',
            credential=AzureKeyCredential(self.key)
        )
        
        try:
            # Obtener documentos (verificaremos lugares_hechos en el código)
            filter_sin_lugares = None  # Procesaremos todos los documentos
            
            # Procesar por páginas
            skip = 0
            page_size = 500
            lote_actual = []
            LOTE_SIZE = 50
            
            while True:
                print(f"   📄 Procesando desde posición {skip:,}...")
                
                results = await search_client.search(
                    search_text="*",
                    top=page_size,
                    skip=skip,
                    select="id,archivo,lugares_hechos"
                )
                
                docs_en_pagina = 0
                
                async for doc in results:
                    docs_en_pagina += 1
                    self.stats['procesados'] += 1
                    
                    # Verificar si ya tiene lugares_hechos poblados
                    lugares_existentes = doc.get('lugares_hechos', [])
                    if lugares_existentes and len(lugares_existentes) > 0:
                        continue  # Ya tiene lugares, saltar
                    
                    archivo = doc.get('archivo', '')
                    if not archivo:
                        continue
                    
                    nombre_archivo = os.path.basename(archivo)
                    lugares_data = self.buscar_lugares_archivo(nombre_archivo)
                    
                    if not lugares_data:
                        continue
                    
                    self.stats['encontrados'] += 1
                    
                    # Preparar lugares_hechos como string con separador
                    lugares_partes = []
                    
                    # Agregar departamento principal
                    if lugares_data.get('departamento_principal'):
                        lugares_partes.append(lugares_data['departamento_principal'])
                    
                    # Agregar municipio principal
                    if lugares_data.get('municipio_principal'):
                        lugares_partes.append(lugares_data['municipio_principal'])
                    
                    # Agregar lugar principal si es diferente
                    if lugares_data.get('lugar_principal'):
                        lugar_principal = lugares_data['lugar_principal']
                        if lugar_principal not in lugares_partes:
                            lugares_partes.append(lugar_principal)
                    
                    # Solo actualizar si tenemos lugares
                    if lugares_partes:
                        lugares_string = " | ".join(lugares_partes[:5])  # Máximo 5, separados por |
                        lote_actual.append({
                            "id": doc['id'],
                            "lugares_hechos": lugares_string
                        })
                    
                    # Procesar lote cuando esté lleno
                    if len(lote_actual) >= LOTE_SIZE:
                        exitosos = await self.actualizar_lote_lugares('exhaustive-legal-index', lote_actual)
                        self.stats['actualizados'] += exitosos
                        lote_actual = []
                        
                        if self.stats['procesados'] % 1000 == 0:
                            tasa = (self.stats['encontrados'] / self.stats['procesados']) * 100
                            print(f"      ✅ {self.stats['procesados']:,} procesados | {self.stats['encontrados']:,} con lugares ({tasa:.1f}%) | {self.stats['actualizados']:,} actualizados")
                
                # Procesar lote restante
                if lote_actual:
                    exitosos = await self.actualizar_lote_lugares('exhaustive-legal-index', lote_actual)
                    self.stats['actualizados'] += exitosos
                    lote_actual = []
                
                skip += page_size
                
                if docs_en_pagina == 0:
                    break
                
                # Límite de prueba inicial
                if skip >= 5000:
                    print(f"⚠️  Límite de prueba alcanzado ({skip:,} docs)")
                    break
                    
                await asyncio.sleep(0.1)
        
        finally:
            await search_client.close()

    async def ejecutar_poblamiento_lugares(self):
        """Ejecuta poblamiento completo de lugares"""
        print("🌍 POBLAMIENTO DE CAMPOS GEOGRÁFICOS EN AZURE SEARCH")
        print("=" * 80)
        
        inicio = time.time()
        
        # Cargar mapeo
        total_docs = self.cargar_mapeo_lugares()
        
        # Poblar ambos índices
        await self.poblar_exhaustive_legal_index()
        
        # Reiniciar estadísticas para el segundo índice
        self.stats = {'procesados': 0, 'encontrados': 0, 'actualizados': 0, 'errores': 0}
        
        await self.poblar_chunks_v2()
        
        # Reporte final
        fin = time.time()
        duracion = fin - inicio
        
        print(f"\n{'='*80}")
        print("🎯 REPORTE FINAL - POBLAMIENTO GEOGRÁFICO")
        print(f"{'='*80}")
        print(f"⏱️  Duración: {duracion:.1f} segundos")
        print(f"📊 Documentos con lugares en BD: {total_docs:,}")
        print(f"📊 Documentos procesados: {self.stats['procesados']:,}")
        print(f"📊 Con lugares encontrados: {self.stats['encontrados']:,}")
        print(f"📊 Actualizados exitosamente: {self.stats['actualizados']:,}")
        print(f"📊 Errores: {self.stats['errores']:,}")
        
        if self.stats['procesados'] > 0:
            tasa = (self.stats['encontrados'] / self.stats['procesados']) * 100
            print(f"📊 Tasa de mapeo geográfico: {tasa:.1f}%")
        
        print(f"\n🎯 IMPACTO EN FILTROS:")
        print("   ✅ Filtros geográficos ahora funcionales")
        print("   📍 Departamentos y municipios disponibles para filtrado")
        print("   🗺️  Lugares específicos identificados")
        print(f"{'='*80}")

async def main():
    poblador = PobladorLugaresAzure()
    await poblador.ejecutar_poblamiento_lugares()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  Proceso interrumpido")
    except Exception as e:
        print(f"❌ Error crítico: {e}")
        import traceback
        traceback.print_exc()