#!/usr/bin/env python3
"""
Poblamiento geográfico MEJORADO - Mapeo por contenido, no solo por nombre de archivo
Estrategia: usar múltiples métodos de mapeo para maximizar cobertura
"""

import asyncio
import os
import time
from dotenv import load_dotenv
from azure.search.documents.aio import SearchClient
from azure.core.credentials import AzureKeyCredential
import psycopg2

load_dotenv('config/.env')

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'documentos_juridicos_gpt4',
    'user': 'docs_user',
    'password': 'docs_password_2025'
}

class PobladorGeograficoMejorado:
    """Poblador geográfico con mapeo mejorado"""
    
    def __init__(self):
        self.endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
        self.key = os.getenv('AZURE_SEARCH_KEY')
        self.mapeo_por_nombre = {}
        self.mapeo_por_nuc = {}
        self.mapeo_por_contenido = {}
        
    def cargar_mapeos_completos(self):
        """Carga múltiples tipos de mapeo desde PostgreSQL"""
        print("🌍 Cargando mapeos inteligentes desde PostgreSQL...")
        
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        try:
            # 1. Mapeo por nombre de archivo (método original)
            query_nombres = """
            WITH lugares_por_doc AS (
                SELECT DISTINCT
                    d.archivo,
                    d.id as doc_id,
                    COALESCE(TRIM(al.departamento), '') as departamento,
                    COALESCE(TRIM(al.municipio), '') as municipio,
                    COALESCE(TRIM(al.nombre), '') as lugar_nombre,
                    ROW_NUMBER() OVER (PARTITION BY d.archivo ORDER BY al.id) as rn
                FROM documentos d
                JOIN analisis_lugares al ON d.id = al.documento_id
                WHERE d.archivo IS NOT NULL
            )
            SELECT archivo, departamento, municipio, lugar_nombre
            FROM lugares_por_doc WHERE rn = 1
            """
            
            cursor.execute(query_nombres)
            for row in cursor.fetchall():
                archivo = row[0]
                if archivo:
                    lugares_partes = []
                    if row[1]: lugares_partes.append(row[1])
                    if row[2]: lugares_partes.append(row[2])
                    if row[3] and row[3] not in lugares_partes: lugares_partes.append(row[3])
                    
                    lugares_string = " | ".join(lugares_partes[:5]) if lugares_partes else ""
                    if lugares_string:
                        # Generar múltiples variaciones de nombre
                        variaciones = self.generar_variaciones_nombre(archivo)
                        for variacion in variaciones:
                            self.mapeo_por_nombre[variacion] = lugares_string
            
            # 2. Mapeo por NUC (más robusto)
            query_nuc = """
            SELECT DISTINCT
                m.nuc,
                COALESCE(TRIM(al.departamento), '') as departamento,
                COALESCE(TRIM(al.municipio), '') as municipio,
                COALESCE(TRIM(al.nombre), '') as lugar_nombre
            FROM metadatos m
            JOIN documentos d ON m.documento_id = d.id
            JOIN analisis_lugares al ON d.id = al.documento_id
            WHERE m.nuc IS NOT NULL 
              AND m.nuc != ''
              AND (al.departamento IS NOT NULL OR al.municipio IS NOT NULL)
            """
            
            cursor.execute(query_nuc)
            for row in cursor.fetchall():
                nuc = row[0].strip() if row[0] else ""
                if nuc:
                    lugares_partes = []
                    if row[1]: lugares_partes.append(row[1])
                    if row[2]: lugares_partes.append(row[2])
                    if row[3] and row[3] not in lugares_partes: lugares_partes.append(row[3])
                    
                    lugares_string = " | ".join(lugares_partes[:5]) if lugares_partes else ""
                    if lugares_string:
                        self.mapeo_por_nuc[nuc] = lugares_string
            
            # 3. Mapeo por contenido (palabras clave)
            query_contenido = """
            SELECT DISTINCT
                COALESCE(TRIM(al.departamento), '') as departamento,
                COALESCE(TRIM(al.municipio), '') as municipio,
                COUNT(*) as freq
            FROM analisis_lugares al
            WHERE al.departamento IS NOT NULL
            GROUP BY al.departamento, al.municipio
            HAVING COUNT(*) >= 5
            ORDER BY freq DESC
            LIMIT 500
            """
            
            cursor.execute(query_contenido)
            for row in cursor.fetchall():
                if row[0] and row[1]:
                    lugar_key = f"{row[0]}_{row[1]}".lower().replace(" ", "_")
                    self.mapeo_por_contenido[lugar_key] = f"{row[0]} | {row[1]}"
            
            print(f"✅ Mapeo por nombres: {len(self.mapeo_por_nombre)} claves")
            print(f"✅ Mapeo por NUC: {len(self.mapeo_por_nuc)} claves")
            print(f"✅ Mapeo por contenido: {len(self.mapeo_por_contenido)} claves")
            
        finally:
            cursor.close()
            conn.close()
    
    def generar_variaciones_nombre(self, archivo: str) -> list:
        """Genera múltiples variaciones de nombres de archivo"""
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
        
        # Variaciones para batch_resultado
        if '_batch_resultado_' in nombre_base:
            nombre_limpio = nombre_base.split('_batch_resultado_')[0]
            variaciones.extend([
                nombre_limpio,
                nombre_limpio + '.pdf',
                nombre_limpio + '.json'
            ])
        
        # Variaciones adicionales para casos complejos
        partes = nombre_base.replace('.json', '').replace('.pdf', '').split('_')
        if len(partes) >= 3:
            # Probar con las primeras 3 partes
            base_3_partes = "_".join(partes[:3])
            variaciones.extend([
                base_3_partes,
                base_3_partes + '.pdf',
                base_3_partes + '.json'
            ])
        
        return list(set(variaciones))
    
    def buscar_lugares_inteligente(self, documento: dict) -> str:
        """Búsqueda inteligente de lugares usando múltiples métodos"""
        
        # Método 1: Por nombre de archivo
        archivo = documento.get('archivo', '') or documento.get('nombre_archivo', '')
        if archivo:
            nombre_base = os.path.basename(archivo)
            variaciones = self.generar_variaciones_nombre(nombre_base)
            
            for variacion in variaciones:
                if variacion in self.mapeo_por_nombre:
                    return self.mapeo_por_nombre[variacion]
        
        # Método 2: Por NUC
        nuc = documento.get('metadatos_nuc', '') or documento.get('nuc', '')
        if nuc and nuc.strip():
            nuc_limpio = nuc.strip()
            if nuc_limpio in self.mapeo_por_nuc:
                return self.mapeo_por_nuc[nuc_limpio]
        
        # Método 3: Por contenido del documento
        contenido = documento.get('texto_extraido', '') or documento.get('texto_chunk', '')
        if contenido:
            contenido_lower = contenido.lower()
            
            # Buscar departamentos conocidos en el contenido
            for lugar_key, lugar_valor in self.mapeo_por_contenido.items():
                if lugar_key.replace("_", " ") in contenido_lower:
                    return lugar_valor
        
        return ""
    
    async def actualizar_lote(self, search_client, documentos: list) -> int:
        """Actualización de lote con manejo de errores"""
        try:
            result = await search_client.merge_or_upload_documents(documentos)
            exitosos = sum(1 for r in result if r.succeeded)
            return exitosos
        except Exception as e:
            print(f"❌ Error en lote: {str(e)[:100]}")
            return 0
    
    async def poblar_indice_mejorado(self, index_name: str, campo_lugares: str):
        """Poblamiento mejorado con múltiples estrategias de mapeo"""
        print(f"\n🚀 POBLAMIENTO MEJORADO {index_name}")
        print("=" * 80)
        
        search_client = SearchClient(self.endpoint, index_name, AzureKeyCredential(self.key))
        stats = {'procesados': 0, 'actualizados': 0, 'mapeados': 0}
        
        try:
            LOTE_SIZE = 50
            skip = 0
            page_size = 500
            
            while skip < 100000:  # Límite de Azure Search
                # Seleccionar campos según índice
                if index_name == 'exhaustive-legal-chunks-v2':
                    select_fields = f"chunk_id,nombre_archivo,nuc,texto_chunk,{campo_lugares}"
                    id_field = "chunk_id"
                else:
                    select_fields = f"id,archivo,metadatos_nuc,texto_extraido,{campo_lugares}"
                    id_field = "id"
                
                results = await search_client.search(
                    search_text="*",
                    top=page_size,
                    skip=skip,
                    select=select_fields
                )
                
                lote_actual = []
                documentos_en_pagina = 0
                
                async for documento in results:
                    documentos_en_pagina += 1
                    stats['procesados'] += 1
                    
                    # Verificar si ya tiene lugares
                    valor_actual = documento.get(campo_lugares)
                    if valor_actual and str(valor_actual).strip():
                        continue  # Ya poblado
                    
                    # Buscar lugares usando métodos inteligentes
                    lugares_encontrados = self.buscar_lugares_inteligente(documento)
                    
                    if lugares_encontrados:
                        stats['mapeados'] += 1
                        lote_actual.append({
                            id_field: documento[id_field],
                            campo_lugares: lugares_encontrados
                        })
                    
                    # Procesar lote
                    if len(lote_actual) >= LOTE_SIZE:
                        exitosos = await self.actualizar_lote(search_client, lote_actual)
                        stats['actualizados'] += exitosos
                        lote_actual = []
                
                # Procesar lote restante
                if lote_actual:
                    exitosos = await self.actualizar_lote(search_client, lote_actual)
                    stats['actualizados'] += exitosos
                
                # Progreso cada 2000
                if stats['procesados'] % 2000 == 0:
                    tasa_mapeo = (stats['mapeados'] / stats['procesados'] * 100) if stats['procesados'] > 0 else 0
                    tasa_actualizacion = (stats['actualizados'] / stats['procesados'] * 100) if stats['procesados'] > 0 else 0
                    print(f"📊 {stats['procesados']:,} procesados | {stats['mapeados']:,} mapeados ({tasa_mapeo:.1f}%) | {stats['actualizados']:,} actualizados ({tasa_actualizacion:.1f}%)")
                
                skip += page_size
                if documentos_en_pagina == 0:
                    break
                    
                await asyncio.sleep(0.1)
            
            return stats
            
        finally:
            await search_client.close()
    
    async def ejecutar_poblamiento_mejorado(self):
        """Ejecuta poblamiento completo mejorado"""
        print("🌍 POBLAMIENTO GEOGRÁFICO MEJORADO - MAPEO INTELIGENTE")
        print("=" * 80)
        
        inicio = time.time()
        
        # Cargar todos los mapeos
        self.cargar_mapeos_completos()
        
        # Poblar ambos índices
        print("\n" + "="*50)
        stats_index = await self.poblar_indice_mejorado('exhaustive-legal-index', 'lugares_hechos')
        
        print("\n" + "="*50)
        stats_chunks = await self.poblar_indice_mejorado('exhaustive-legal-chunks-v2', 'lugares_chunk')
        
        # Reporte final
        fin = time.time()
        duracion = fin - inicio
        
        print(f"\n{'='*80}")
        print("🎯 REPORTE FINAL - POBLAMIENTO MEJORADO")
        print(f"{'='*80}")
        print(f"📊 exhaustive-legal-index:")
        print(f"   - Procesados: {stats_index['procesados']:,}")
        print(f"   - Mapeados: {stats_index['mapeados']:,}")
        print(f"   - Actualizados: {stats_index['actualizados']:,}")
        
        print(f"📊 exhaustive-legal-chunks-v2:")
        print(f"   - Procesados: {stats_chunks['procesados']:,}")
        print(f"   - Mapeados: {stats_chunks['mapeados']:,}")
        print(f"   - Actualizados: {stats_chunks['actualizados']:,}")
        
        total_procesados = stats_index['procesados'] + stats_chunks['procesados']
        total_actualizados = stats_index['actualizados'] + stats_chunks['actualizados']
        
        print(f"\n📊 TOTALES:")
        print(f"   - Total procesados: {total_procesados:,}")
        print(f"   - Total actualizados: {total_actualizados:,}")
        print(f"   - Duración: {duracion:.1f} segundos")
        
        if total_procesados > 0:
            tasa = (total_actualizados / total_procesados * 100)
            print(f"   - Tasa de éxito: {tasa:.1f}%")
        
        print(f"{'='*80}")

async def main():
    poblador = PobladorGeograficoMejorado()
    await poblador.ejecutar_poblamiento_mejorado()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ Error crítico: {e}")
        import traceback
        traceback.print_exc()