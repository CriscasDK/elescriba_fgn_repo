#!/usr/bin/env python3
"""
Script robusto para corrección masiva de Azure Search
Procesa documentos por lotes pequeños y maneja errores graciosamente
"""

import asyncio
import os
import json
import sys
from typing import Dict, List, Optional
from dotenv import load_dotenv
import psycopg2
from azure.search.documents.aio import SearchClient
from azure.core.credentials import AzureKeyCredential
from datetime import datetime
import time

# Cargar configuración
load_dotenv('config/.env')

# Configuración de base de datos
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'documentos_juridicos_gpt4',
    'user': 'docs_user',
    'password': 'docs_password_2025'
}

class CorrectorMasivo:
    """Corrector masivo optimizado para Azure Search"""
    
    def __init__(self):
        self.endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
        self.key = os.getenv('AZURE_SEARCH_KEY')
        self.datos_bd = {}
        
    def cargar_datos_bd_optimizado(self):
        """Carga datos esenciales desde PostgreSQL de forma optimizada"""
        print("📊 Cargando datos desde PostgreSQL...")
        
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        try:
            # Query simplificada para mayor velocidad
            query = """
            SELECT 
                d.archivo,
                COALESCE(TRIM(m.nuc), '') as nuc,
                COALESCE(TRIM(m.cuaderno), '') as cuaderno,
                COALESCE(TRIM(m.codigo), '') as codigo,
                COALESCE(TRIM(m.despacho), '') as despacho,
                COALESCE(TRIM(m.entidad_productora), '') as entidad_productora
            FROM documentos d
            LEFT JOIN metadatos m ON d.id = m.documento_id
            WHERE d.archivo IS NOT NULL AND m.nuc IS NOT NULL
            """
            
            cursor.execute(query)
            resultados = cursor.fetchall()
            
            for row in resultados:
                archivo = row[0]
                if archivo:
                    nombre_base = os.path.basename(archivo)
                    datos = {
                        'nuc': self.limpiar_valor(row[1]),
                        'cuaderno': self.limpiar_valor(row[2]),
                        'codigo': self.limpiar_valor(row[3]),
                        'despacho': self.limpiar_valor(row[4]),
                        'entidad_productora': self.limpiar_valor(row[5])
                    }
                    
                    # Múltiples claves para mapeo
                    self.datos_bd[nombre_base] = datos
                    nombre_sin_ext = nombre_base.replace('.pdf', '')
                    self.datos_bd[nombre_sin_ext] = datos
                    
                    if '_batch_resultado_' in nombre_sin_ext:
                        nombre_limpio = nombre_sin_ext.split('_batch_resultado_')[0] + '.pdf'
                        self.datos_bd[nombre_limpio] = datos
            
            print(f"✅ {len(resultados)} documentos cargados desde PostgreSQL")
            return len(resultados)
            
        finally:
            cursor.close()
            conn.close()

    def limpiar_valor(self, valor) -> Optional[str]:
        """Limpia valores para Azure Search"""
        if valor is None:
            return None
        valor_str = str(valor).strip()
        return valor_str if valor_str and valor_str != '' and valor_str != 'None' else None

    def extraer_nombre_archivo(self, doc: Dict) -> Optional[str]:
        """Extrae nombre de archivo del documento Azure"""
        campos = ['archivo', 'nombre_archivo', 'documento_id']
        
        for campo in campos:
            valor = doc.get(campo)
            if valor:
                nombre = os.path.basename(str(valor))
                if nombre.endswith('.json'):
                    nombre = nombre.replace('.json', '.pdf')
                return nombre
        return None

    def buscar_datos(self, nombre_archivo: str) -> Optional[Dict]:
        """Busca datos en BD"""
        if not nombre_archivo:
            return None
        
        if nombre_archivo in self.datos_bd:
            return self.datos_bd[nombre_archivo]
        
        # Búsqueda por patrón
        nombre_base = nombre_archivo.replace('.pdf', '').replace('.json', '')
        for clave_bd, datos in self.datos_bd.items():
            if nombre_base in clave_bd or clave_bd.replace('.pdf', '') in nombre_base:
                return datos
        
        return None

    async def actualizar_lote_documentos(self, index_name: str, documentos: List[Dict]) -> int:
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
            print(f"❌ Error en lote: {e}")
            return 0
        finally:
            await search_client.close()

    async def procesar_indice_optimizado(self, index_name: str, descripcion: str):
        """Procesa un índice de forma optimizada"""
        print(f"\n📋 PROCESANDO: {descripcion}")
        print("=" * 60)
        
        search_client = SearchClient(
            endpoint=self.endpoint,
            index_name=index_name,
            credential=AzureKeyCredential(self.key)
        )
        
        stats = {'procesados': 0, 'actualizados': 0, 'errores': 0, 'sin_datos': 0}
        lote_actualizacion = []
        LOTE_SIZE = 50  # Lotes pequeños para evitar timeouts
        
        try:
            # Obtener total aproximado
            count_result = await search_client.search(search_text="*", top=0, include_total_count=True)
            total_docs = await count_result.get_count()
            print(f"📊 Total documentos en índice: {total_docs:,}")
            
            # Procesar por páginas
            skip = 0
            page_size = 200
            
            while skip < total_docs:
                print(f"   📄 Procesando desde posición {skip:,}...")
                
                # Obtener página de documentos
                results = await search_client.search(
                    search_text="*",
                    top=page_size,
                    skip=skip
                )
                
                documentos_en_pagina = 0
                
                async for documento in results:
                    documentos_en_pagina += 1
                    stats['procesados'] += 1
                    
                    try:
                        # Extraer nombre de archivo
                        nombre_archivo = self.extraer_nombre_archivo(documento)
                        if not nombre_archivo:
                            continue
                        
                        # Buscar datos en BD
                        datos_bd = self.buscar_datos(nombre_archivo)
                        if not datos_bd:
                            stats['sin_datos'] += 1
                            continue
                        
                        # Preparar actualización
                        doc_update = self.preparar_actualizacion(documento, datos_bd, index_name)
                        
                        if doc_update:
                            lote_actualizacion.append(doc_update)
                        
                        # Procesar lote cuando esté lleno
                        if len(lote_actualizacion) >= LOTE_SIZE:
                            exitosos = await self.actualizar_lote_documentos(index_name, lote_actualizacion)
                            stats['actualizados'] += exitosos
                            lote_actualizacion = []
                            
                            # Mostrar progreso
                            if stats['procesados'] % 500 == 0:
                                print(f"   ✅ {stats['procesados']:,} procesados | {stats['actualizados']:,} actualizados")
                    
                    except Exception as e:
                        stats['errores'] += 1
                        if stats['errores'] <= 5:
                            print(f"   ❌ Error: {e}")
                
                # Procesar lote restante
                if lote_actualizacion:
                    exitosos = await self.actualizar_lote_documentos(index_name, lote_actualizacion)
                    stats['actualizados'] += exitosos
                    lote_actualizacion = []
                
                skip += page_size
                
                # Si no obtuvimos documentos, salir
                if documentos_en_pagina == 0:
                    break
                
                # Pequeña pausa para no sobrecargar el servicio
                await asyncio.sleep(0.1)
                
        finally:
            await search_client.close()
        
        return stats

    def preparar_actualizacion(self, documento: Dict, datos_bd: Dict, index_name: str) -> Optional[Dict]:
        """Prepara documento para actualización"""
        campos_actualizar = {}
        
        if index_name == 'exhaustive-legal-index':
            # Campos para documentos completos
            mapeo = {
                'nuc': 'metadatos_nuc',
                'cuaderno': 'metadatos_cuaderno',
                'codigo': 'metadatos_codigo',
                'despacho': 'metadatos_despacho',
                'entidad_productora': 'metadatos_entidad_productora'
            }
            
            for campo_bd, campo_azure in mapeo.items():
                valor_bd = datos_bd.get(campo_bd)
                valor_azure = documento.get(campo_azure)
                
                if valor_bd and (valor_azure is None or valor_azure == ''):
                    campos_actualizar[campo_azure] = valor_bd
            
            if campos_actualizar:
                return {"id": documento['id'], **campos_actualizar}
                
        else:  # chunks-v2
            # Campos para chunks
            if datos_bd.get('nuc') and not documento.get('nuc'):
                campos_actualizar['nuc'] = datos_bd['nuc']
            
            if datos_bd.get('entidad_productora') and not documento.get('entidad_productora'):
                campos_actualizar['entidad_productora'] = datos_bd['entidad_productora']
            
            if campos_actualizar:
                return {"chunk_id": documento['chunk_id'], **campos_actualizar}
        
        return None

    async def ejecutar_correccion_masiva(self):
        """Ejecuta corrección masiva optimizada"""
        print("🚀 CORRECCIÓN MASIVA DE AZURE SEARCH")
        print("=" * 80)
        
        inicio = time.time()
        
        # Cargar datos
        total_bd = self.cargar_datos_bd_optimizado()
        
        # Procesar índices
        indices = [
            ('exhaustive-legal-index', 'Documentos Completos'),
            ('exhaustive-legal-chunks-v2', 'Chunks con Trazabilidad')
        ]
        
        estadisticas_totales = {}
        
        for index_name, descripcion in indices:
            try:
                stats = await self.procesar_indice_optimizado(index_name, descripcion)
                estadisticas_totales[index_name] = stats
            except Exception as e:
                print(f"❌ Error procesando {index_name}: {e}")
                estadisticas_totales[index_name] = {'procesados': 0, 'actualizados': 0, 'errores': 1}
        
        # Reporte final
        fin = time.time()
        duracion = fin - inicio
        
        print(f"\n{'='*80}")
        print("📊 REPORTE FINAL - CORRECCIÓN MASIVA")
        print(f"{'='*80}")
        print(f"⏱️  Duración total: {duracion:.1f} segundos")
        print(f"📊 Documentos en BD: {total_bd:,}")
        
        for index_name, descripcion in indices:
            stats = estadisticas_totales.get(index_name, {})
            print(f"\n📋 {descripcion}:")
            print(f"   Procesados: {stats.get('procesados', 0):,}")
            print(f"   Actualizados: {stats.get('actualizados', 0):,}")
            print(f"   Sin datos BD: {stats.get('sin_datos', 0):,}")
            print(f"   Errores: {stats.get('errores', 0):,}")
        
        print(f"\n{'='*80}")

async def main():
    corrector = CorrectorMasivo()
    await corrector.ejecutar_correccion_masiva()

if __name__ == "__main__":
    # Configurar entorno
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