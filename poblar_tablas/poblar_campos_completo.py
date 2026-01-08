#!/usr/bin/env python3
"""
Script completo para poblar todos los campos faltantes identificados
- tipo_documento en chunks-v2 (1.6% → 100%)
- NUC en chunks-v2 (51.5% → 100%)  
- tipo_documento en exhaustive-legal-index (66.6% → 100%)
"""

import asyncio
import os
import sys
from dotenv import load_dotenv
from azure.search.documents.aio import SearchClient
from azure.core.credentials import AzureKeyCredential
import psycopg2
import time
from typing import Dict, List, Optional

# Cargar configuración
load_dotenv('config/.env')

# Configuración de BD
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'documentos_juridicos_gpt4',
    'user': 'docs_user',
    'password': 'docs_password_2025'
}

class PobladorCamposCompleto:
    """Pobla todos los campos faltantes para filtros"""
    
    def __init__(self):
        self.endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
        self.key = os.getenv('AZURE_SEARCH_KEY')
        self.mapeo_archivos = {}
        
    def cargar_mapeo_completo(self):
        """Carga mapeo completo archivo → datos desde PostgreSQL"""
        print("📊 Cargando mapeo completo desde PostgreSQL...")
        
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        try:
            # Query optimizada para obtener todos los datos necesarios
            query = """
            SELECT DISTINCT
                d.archivo,
                COALESCE(TRIM(m.detalle), 'Documento') as tipo_documento,
                COALESCE(TRIM(m.nuc), '') as nuc,
                COALESCE(TRIM(m.despacho), '') as despacho,
                COALESCE(TRIM(m.entidad_productora), '') as entidad_productora
            FROM documentos d
            LEFT JOIN metadatos m ON d.id = m.documento_id
            WHERE d.archivo IS NOT NULL
            """
            
            cursor.execute(query)
            resultados = cursor.fetchall()
            
            for row in resultados:
                archivo = row[0]
                if archivo:
                    # Generar múltiples claves de mapeo para encontrar archivos
                    datos = {
                        'tipo_documento': self.limpiar_valor(row[1]) or 'Documento',
                        'nuc': self.limpiar_valor(row[2]),
                        'despacho': self.limpiar_valor(row[3]),
                        'entidad_productora': self.limpiar_valor(row[4])
                    }
                    
                    # Múltiples variaciones del nombre de archivo
                    variaciones = self.generar_variaciones_nombre(archivo)
                    for variacion in variaciones:
                        self.mapeo_archivos[variacion] = datos
            
            print(f"✅ {len(resultados)} registros cargados → {len(self.mapeo_archivos)} claves de mapeo")
            return len(resultados)
            
        finally:
            cursor.close()
            conn.close()

    def generar_variaciones_nombre(self, archivo: str) -> List[str]:
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
            variaciones.append(nombre_limpio)
            variaciones.append(nombre_limpio + '.pdf')
            variaciones.append(nombre_limpio + '.json')
        
        return list(set(variaciones))  # Eliminar duplicados

    def limpiar_valor(self, valor) -> Optional[str]:
        """Limpia valores para Azure Search"""
        if valor is None:
            return None
        valor_str = str(valor).strip()
        return valor_str if valor_str and valor_str != '' and valor_str != 'None' else None

    def buscar_datos_archivo(self, nombre_archivo: str) -> Optional[Dict]:
        """Busca datos del archivo en el mapeo"""
        if not nombre_archivo:
            return None
        
        # Búsqueda directa
        if nombre_archivo in self.mapeo_archivos:
            return self.mapeo_archivos[nombre_archivo]
        
        # Búsqueda por variaciones
        variaciones = self.generar_variaciones_nombre(nombre_archivo)
        for variacion in variaciones:
            if variacion in self.mapeo_archivos:
                return self.mapeo_archivos[variacion]
        
        # Búsqueda parcial
        nombre_base = nombre_archivo.replace('.pdf', '').replace('.json', '')
        for clave, datos in self.mapeo_archivos.items():
            clave_base = clave.replace('.pdf', '').replace('.json', '')
            if nombre_base in clave_base or clave_base in nombre_base:
                return datos
        
        return None

    async def actualizar_lote(self, index_name: str, documentos: List[Dict]) -> int:
        """Actualiza un lote de documentos"""
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
            print(f"❌ Error en lote: {str(e)[:100]}...")
            return 0
        finally:
            await search_client.close()

    async def poblar_exhaustive_legal_index(self):
        """Pobla campos faltantes en exhaustive-legal-index"""
        print(f"\n📋 POBLANDO exhaustive-legal-index")
        print("=" * 60)
        
        search_client = SearchClient(
            endpoint=self.endpoint,
            index_name='exhaustive-legal-index',
            credential=AzureKeyCredential(self.key)
        )
        
        stats = {'procesados': 0, 'actualizados': 0, 'errores': 0}
        
        try:
            # Buscar documentos sin tipo_documento
            filter_query = "tipo_documento eq null or tipo_documento eq ''"
            results = await search_client.search(
                search_text="*",
                filter=filter_query,
                top=1000,  # Procesar en lotes más grandes
                select="id,archivo,tipo_documento"
            )
            
            lote = []
            LOTE_SIZE = 50
            
            async for doc in results:
                stats['procesados'] += 1
                
                try:
                    archivo = doc.get('archivo')
                    if not archivo:
                        continue
                    
                    nombre_archivo = os.path.basename(archivo)
                    datos = self.buscar_datos_archivo(nombre_archivo)
                    
                    if datos and datos.get('tipo_documento'):
                        lote.append({
                            "id": doc['id'],
                            "tipo_documento": datos['tipo_documento']
                        })
                    
                    # Procesar lote cuando esté lleno
                    if len(lote) >= LOTE_SIZE:
                        exitosos = await self.actualizar_lote('exhaustive-legal-index', lote)
                        stats['actualizados'] += exitosos
                        lote = []
                        
                        if stats['procesados'] % 200 == 0:
                            print(f"   📄 Procesados: {stats['procesados']:,} | Actualizados: {stats['actualizados']:,}")
                
                except Exception as e:
                    stats['errores'] += 1
                    if stats['errores'] <= 3:
                        print(f"   ❌ Error: {e}")
            
            # Procesar lote restante
            if lote:
                exitosos = await self.actualizar_lote('exhaustive-legal-index', lote)
                stats['actualizados'] += exitosos
            
            print(f"✅ exhaustive-legal-index completado:")
            print(f"   Procesados: {stats['procesados']:,}")
            print(f"   Actualizados: {stats['actualizados']:,}")
            print(f"   Errores: {stats['errores']:,}")
            
        finally:
            await search_client.close()
        
        return stats

    async def poblar_chunks_v2(self):
        """Pobla campos faltantes en exhaustive-legal-chunks-v2"""
        print(f"\n📋 POBLANDO exhaustive-legal-chunks-v2")
        print("=" * 60)
        
        search_client = SearchClient(
            endpoint=self.endpoint,
            index_name='exhaustive-legal-chunks-v2',
            credential=AzureKeyCredential(self.key)
        )
        
        stats = {'procesados': 0, 'actualizados': 0, 'errores': 0, 'nuc_agregado': 0, 'tipo_agregado': 0}
        
        try:
            # Buscar chunks que necesitan tipo_documento o NUC
            filter_query = "(tipo_documento eq null or tipo_documento eq '') or (nuc eq null or nuc eq '')"
            
            # Procesar por páginas para manejar el gran volumen
            skip = 0
            page_size = 500
            
            while True:
                print(f"   📄 Procesando desde posición {skip:,}...")
                
                results = await search_client.search(
                    search_text="*",
                    filter=filter_query,
                    top=page_size,
                    skip=skip,
                    select="chunk_id,nombre_archivo,tipo_documento,nuc"
                )
                
                lote = []
                LOTE_SIZE = 50
                documentos_en_pagina = 0
                
                async for doc in results:
                    documentos_en_pagina += 1
                    stats['procesados'] += 1
                    
                    try:
                        nombre_archivo = doc.get('nombre_archivo')
                        if not nombre_archivo:
                            continue
                        
                        datos = self.buscar_datos_archivo(nombre_archivo)
                        if not datos:
                            continue
                        
                        # Preparar actualización
                        update_doc = {"chunk_id": doc['chunk_id']}
                        actualizado = False
                        
                        # Agregar tipo_documento si falta
                        if not doc.get('tipo_documento') and datos.get('tipo_documento'):
                            update_doc["tipo_documento"] = datos['tipo_documento']
                            stats['tipo_agregado'] += 1
                            actualizado = True
                        
                        # Agregar NUC si falta
                        if not doc.get('nuc') and datos.get('nuc'):
                            update_doc["nuc"] = datos['nuc']
                            stats['nuc_agregado'] += 1
                            actualizado = True
                        
                        if actualizado:
                            lote.append(update_doc)
                        
                        # Procesar lote cuando esté lleno
                        if len(lote) >= LOTE_SIZE:
                            exitosos = await self.actualizar_lote('exhaustive-legal-chunks-v2', lote)
                            stats['actualizados'] += exitosos
                            lote = []
                            
                            if stats['procesados'] % 1000 == 0:
                                print(f"      ✅ {stats['procesados']:,} procesados | {stats['actualizados']:,} actualizados")
                    
                    except Exception as e:
                        stats['errores'] += 1
                        if stats['errores'] <= 3:
                            print(f"   ❌ Error: {e}")
                
                # Procesar lote restante
                if lote:
                    exitosos = await self.actualizar_lote('exhaustive-legal-chunks-v2', lote)
                    stats['actualizados'] += exitosos
                
                # Continuar o terminar
                skip += page_size
                if documentos_en_pagina == 0 or skip > 50000:  # Límite de seguridad
                    break
                
                await asyncio.sleep(0.1)  # Pausa breve
            
            print(f"✅ exhaustive-legal-chunks-v2 completado:")
            print(f"   Procesados: {stats['procesados']:,}")
            print(f"   Actualizados: {stats['actualizados']:,}")
            print(f"   NUC agregado: {stats['nuc_agregado']:,}")
            print(f"   Tipo agregado: {stats['tipo_agregado']:,}")
            print(f"   Errores: {stats['errores']:,}")
            
        finally:
            await search_client.close()
        
        return stats

    async def ejecutar_poblamiento_completo(self):
        """Ejecuta poblamiento completo de todos los campos"""
        print("🚀 POBLAMIENTO COMPLETO DE CAMPOS PARA FILTROS")
        print("=" * 80)
        
        inicio = time.time()
        
        # Cargar datos
        total_datos = self.cargar_mapeo_completo()
        
        # Poblar índices
        stats_index = await self.poblar_exhaustive_legal_index()
        stats_chunks = await self.poblar_chunks_v2()
        
        # Reporte final
        fin = time.time()
        duracion = fin - inicio
        
        print(f"\n{'='*80}")
        print("🎯 REPORTE FINAL - POBLAMIENTO COMPLETO")
        print(f"{'='*80}")
        print(f"⏱️  Duración total: {duracion:.1f} segundos")
        print(f"📊 Datos disponibles en BD: {total_datos:,}")
        print(f"📊 Claves de mapeo generadas: {len(self.mapeo_archivos):,}")
        
        print(f"\n📋 exhaustive-legal-index:")
        print(f"   Documentos actualizados: {stats_index['actualizados']:,}")
        
        print(f"\n📋 exhaustive-legal-chunks-v2:")
        print(f"   Chunks actualizados: {stats_chunks['actualizados']:,}")
        print(f"   NUC agregado: {stats_chunks['nuc_agregado']:,}")
        print(f"   Tipo documento agregado: {stats_chunks['tipo_agregado']:,}")
        
        print(f"\n🎯 SIGUIENTE PASO:")
        print("   Ejecutar verificación final para confirmar porcentajes mejorados")
        print(f"{'='*80}")

async def main():
    poblador = PobladorCamposCompleto()
    await poblador.ejecutar_poblamiento_completo()

if __name__ == "__main__":
    sys.path.append(os.path.dirname(__file__))
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  Proceso interrumpido por el usuario")
    except Exception as e:
        print(f"❌ Error crítico: {e}")
        import traceback
        traceback.print_exc()