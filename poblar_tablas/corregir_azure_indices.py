#!/usr/bin/env python3
"""
Script unificado para corregir metadatos faltantes en ambos índices de Azure Search:
- exhaustive-legal-index (documentos completos)  
- exhaustive-legal-chunks-v2 (chunks con trazabilidad)

Usa datos de PostgreSQL para poblar campos vacíos.
"""

import asyncio
import os
import json
import sys
import re
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv
import psycopg2
from azure.search.documents.aio import SearchClient
from azure.core.credentials import AzureKeyCredential
from datetime import datetime

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

class CorrectorAzureIndices:
    """Corrige metadatos faltantes en ambos índices de Azure Search"""
    
    def __init__(self):
        self.endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
        self.key = os.getenv('AZURE_SEARCH_KEY')
        
        self.indices = {
            'exhaustive-legal-index': 'Documentos Completos',
            'exhaustive-legal-chunks-v2': 'Chunks con Trazabilidad'
        }
        
        self.datos_bd = {}
        self.estadisticas = {
            'exhaustive-legal-index': {'procesados': 0, 'actualizados': 0, 'errores': 0},
            'exhaustive-legal-chunks-v2': {'procesados': 0, 'actualizados': 0, 'errores': 0}
        }

    def conectar_bd(self):
        """Conecta a PostgreSQL"""
        try:
            return psycopg2.connect(**DB_CONFIG)
        except Exception as e:
            print(f"❌ Error conectando a PostgreSQL: {e}")
            sys.exit(1)

    def cargar_datos_bd(self):
        """Carga datos completos desde PostgreSQL"""
        print("📊 Cargando datos desde PostgreSQL...")
        
        conn = self.conectar_bd()
        cursor = conn.cursor()
        
        try:
            query = """
            SELECT 
                d.archivo,
                d.id,
                d.ruta,
                d.analisis,
                d.texto_extraido,
                -- Metadatos básicos
                COALESCE(TRIM(m.nuc), '') as nuc,
                COALESCE(TRIM(m.cuaderno), '') as cuaderno,
                COALESCE(TRIM(m.codigo), '') as codigo,
                COALESCE(TRIM(m.despacho), '') as despacho,
                COALESCE(TRIM(m.detalle), '') as detalle,
                COALESCE(TRIM(m.entidad_productora), '') as entidad_productora,
                COALESCE(TRIM(m.serie), '') as serie,
                COALESCE(TRIM(m.subserie), '') as subserie,
                m.folio_inicial,
                m.folio_final,
                m.fecha_creacion,
                -- Personas extraídas
                COALESCE(string_agg(DISTINCT 
                    CASE WHEN p.tipo = 'victima' THEN p.nombre END, ', '), '') as victimas,
                COALESCE(string_agg(DISTINCT 
                    CASE WHEN p.tipo = 'victimario' THEN p.nombre END, ', '), '') as victimarios,
                COALESCE(string_agg(DISTINCT 
                    CASE WHEN p.tipo = 'defensa' THEN p.nombre END, ', '), '') as defensa,
                COALESCE(string_agg(DISTINCT p.nombre, ', '), '') as todas_personas,
                -- Organizaciones extraídas
                COALESCE(string_agg(DISTINCT 
                    CASE WHEN o.tipo = 'fuerzas_legitimas' THEN o.nombre END, ', '), '') as org_legitimas,
                COALESCE(string_agg(DISTINCT 
                    CASE WHEN o.tipo = 'fuerzas_ilegales' THEN o.nombre END, ', '), '') as org_ilegales,
                COALESCE(string_agg(DISTINCT o.nombre, ', '), '') as todas_organizaciones
            FROM documentos d
            LEFT JOIN metadatos m ON d.id = m.documento_id
            LEFT JOIN personas p ON d.id = p.documento_id
            LEFT JOIN organizaciones o ON d.id = o.documento_id
            WHERE d.archivo IS NOT NULL
            GROUP BY d.id, d.archivo, d.ruta, d.analisis, d.texto_extraido,
                     m.nuc, m.cuaderno, m.codigo, m.despacho, m.detalle, 
                     m.entidad_productora, m.serie, m.subserie, 
                     m.folio_inicial, m.folio_final, m.fecha_creacion
            ORDER BY d.id
            """
            
            cursor.execute(query)
            resultados = cursor.fetchall()
            
            print(f"✅ {len(resultados)} documentos cargados desde PostgreSQL")
            
            # Procesar resultados
            for row in resultados:
                archivo = row[0]
                if archivo:
                    # Generar variaciones del nombre de archivo para mapeo
                    nombre_base = os.path.basename(archivo)
                    nombre_sin_ext = nombre_base.replace('.pdf', '')
                    
                    datos = {
                        'archivo': archivo,
                        'id_db': row[1],
                        'ruta': row[2],
                        'analisis': row[3],
                        'texto_extraido': row[4],
                        # Metadatos
                        'metadatos_nuc': self.limpiar_valor(row[5]),
                        'metadatos_cuaderno': self.limpiar_valor(row[6]),
                        'metadatos_codigo': self.limpiar_valor(row[7]),
                        'metadatos_despacho': self.limpiar_valor(row[8]),
                        'metadatos_detalle': self.limpiar_valor(row[9]),
                        'metadatos_entidad_productora': self.limpiar_valor(row[10]),
                        'metadatos_serie': self.limpiar_valor(row[11]),
                        'metadatos_subserie': self.limpiar_valor(row[12]),
                        'metadatos_folio_inicial': row[13],
                        'metadatos_folio_final': row[14],
                        'metadatos_fecha_creacion': str(row[15]) if row[15] else None,
                        # Personas y organizaciones
                        'personas_victimas': self.limpiar_valor(row[16]),
                        'personas_victimarios': self.limpiar_valor(row[17]),
                        'personas_defensa': self.limpiar_valor(row[18]),
                        'personas_todas': self.limpiar_valor(row[19]),
                        'organizaciones_fuerzas_legitimas': self.limpiar_valor(row[20]),
                        'organizaciones_fuerzas_ilegales': self.limpiar_valor(row[21]),
                        'organizaciones_todas': self.limpiar_valor(row[22])
                    }
                    
                    # Múltiples claves para mapeo robusto
                    self.datos_bd[nombre_base] = datos
                    self.datos_bd[nombre_sin_ext] = datos
                    if '_batch_resultado_' in nombre_sin_ext:
                        nombre_limpio = nombre_sin_ext.split('_batch_resultado_')[0] + '.pdf'
                        self.datos_bd[nombre_limpio] = datos
            
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

    def extraer_nombre_archivo_azure(self, documento_azure: Dict) -> Optional[str]:
        """Extrae nombre de archivo limpio desde documento de Azure Search"""
        # Intentar diferentes campos
        campos_archivo = ['archivo', 'nombre_archivo', 'documento_id', 'id']
        
        for campo in campos_archivo:
            valor = documento_azure.get(campo)
            if valor:
                # Limpiar rutas y extraer nombre base
                nombre = os.path.basename(str(valor))
                if nombre and nombre != 'N/A':
                    # Remover extensiones .json y agregar .pdf si es necesario
                    if nombre.endswith('.json'):
                        nombre = nombre.replace('.json', '.pdf')
                    return nombre
        
        return None

    def buscar_datos_bd(self, nombre_archivo: str) -> Optional[Dict]:
        """Busca datos en BD usando nombre de archivo con múltiples estrategias"""
        if not nombre_archivo:
            return None
        
        # Búsqueda directa
        if nombre_archivo in self.datos_bd:
            return self.datos_bd[nombre_archivo]
        
        # Búsqueda por patrón similar
        nombre_base = nombre_archivo.replace('.pdf', '').replace('.json', '')
        
        for clave_bd, datos in self.datos_bd.items():
            if nombre_base in clave_bd or clave_bd.replace('.pdf', '') in nombre_base:
                return datos
        
        return None

    async def actualizar_documento_completo(self, documento: Dict, datos_bd: Dict) -> bool:
        """Actualiza documento en exhaustive-legal-index"""
        try:
            search_client = SearchClient(
                endpoint=self.endpoint,
                index_name='exhaustive-legal-index',
                credential=AzureKeyCredential(self.key)
            )
            
            # Campos a actualizar (solo si están vacíos en Azure)
            campos_actualizar = {}
            
            # Mapeo de campos
            mapeo_campos = {
                'metadatos_nuc': 'metadatos_nuc',
                'metadatos_cuaderno': 'metadatos_cuaderno', 
                'metadatos_codigo': 'metadatos_codigo',
                'metadatos_despacho': 'metadatos_despacho',
                'metadatos_detalle': 'metadatos_detalle',
                'metadatos_entidad_productora': 'metadatos_entidad_productora',
                'metadatos_serie': 'metadatos_serie',
                'metadatos_subserie': 'metadatos_subserie',
                'personas_todas': 'personas_todas',
                'personas_victimas': 'personas_victimas',
                'personas_victimarios': 'personas_victimarios', 
                'personas_defensa': 'personas_defensa',
                'organizaciones_todas': 'organizaciones_todas',
                'organizaciones_fuerzas_legitimas': 'organizaciones_fuerzas_legitimas',
                'organizaciones_fuerzas_ilegales': 'organizaciones_fuerzas_ilegales'
            }
            
            for campo_bd, campo_azure in mapeo_campos.items():
                valor_bd = datos_bd.get(campo_bd)
                valor_azure = documento.get(campo_azure)
                
                if valor_bd and (valor_azure is None or valor_azure == ''):
                    campos_actualizar[campo_azure] = valor_bd
            
            if campos_actualizar:
                documento_update = {
                    "id": documento['id'],
                    **campos_actualizar
                }
                
                result = await search_client.merge_or_upload_documents([documento_update])
                await search_client.close()
                return result[0].succeeded
            
            await search_client.close()
            return True
            
        except Exception as e:
            print(f"❌ Error actualizando documento completo: {e}")
            return False

    async def actualizar_chunk(self, chunk: Dict, datos_bd: Dict) -> bool:
        """Actualiza chunk en exhaustive-legal-chunks-v2"""
        try:
            search_client = SearchClient(
                endpoint=self.endpoint,
                index_name='exhaustive-legal-chunks-v2',
                credential=AzureKeyCredential(self.key)
            )
            
            # Campos específicos para chunks
            campos_actualizar = {}
            
            # Metadatos básicos
            if datos_bd.get('metadatos_nuc') and not chunk.get('nuc'):
                campos_actualizar['nuc'] = datos_bd['metadatos_nuc']
            
            if datos_bd.get('metadatos_entidad_productora') and not chunk.get('entidad_productora'):
                campos_actualizar['entidad_productora'] = datos_bd['metadatos_entidad_productora']
            
            # Extraer información específica del chunk desde el análisis
            if datos_bd.get('analisis'):
                analisis = datos_bd['analisis']
                
                # Intentar extraer tipo de documento del análisis
                if not chunk.get('tipo_documento'):
                    tipo_doc = self.extraer_tipo_documento(analisis)
                    if tipo_doc:
                        campos_actualizar['tipo_documento'] = tipo_doc
                
                # Para chunks, podríamos intentar extraer información contextual
                # del texto del chunk específico vs el análisis completo
            
            if campos_actualizar:
                documento_update = {
                    "chunk_id": chunk['chunk_id'],
                    **campos_actualizar
                }
                
                result = await search_client.merge_or_upload_documents([documento_update])
                await search_client.close()
                return result[0].succeeded
            
            await search_client.close()
            return True
            
        except Exception as e:
            print(f"❌ Error actualizando chunk: {e}")
            return False

    def extraer_tipo_documento(self, analisis: str) -> Optional[str]:
        """Extrae tipo de documento del análisis usando patrones"""
        if not analisis:
            return None
        
        # Patrones comunes en análisis
        patrones = [
            r'(?i)tipo.*?documento[:\s]*([^\n\r\.]+)',
            r'(?i)especificación[:\s]*([^\n\r\.]+)',
            r'(?i)documento.*?tipo[:\s]*([^\n\r\.]+)'
        ]
        
        for patron in patrones:
            match = re.search(patron, analisis)
            if match:
                tipo = match.group(1).strip()
                if len(tipo) < 100:  # Filtrar extracciones muy largas
                    return tipo
        
        return None

    async def procesar_indice(self, index_name: str) -> Dict:
        """Procesa un índice específico"""
        print(f"\n📋 PROCESANDO ÍNDICE: {self.indices[index_name]}")
        print("=" * 60)
        
        search_client = SearchClient(
            endpoint=self.endpoint,
            index_name=index_name,
            credential=AzureKeyCredential(self.key)
        )
        
        stats = {'procesados': 0, 'actualizados': 0, 'errores': 0}
        
        try:
            # Procesar TODOS los documentos disponibles
            lote_size = 1000  # Lotes más grandes para eficiencia
            
            results = await search_client.search(
                search_text="*",
                top=lote_size
            )
            
            async for documento in results:
                try:
                    stats['procesados'] += 1
                    
                    # Extraer nombre de archivo
                    nombre_archivo = self.extraer_nombre_archivo_azure(documento)
                    
                    if not nombre_archivo:
                        continue
                    
                    # Buscar datos en BD
                    datos_bd = self.buscar_datos_bd(nombre_archivo)
                    
                    if not datos_bd:
                        continue
                    
                    # Actualizar según tipo de índice
                    if index_name == 'exhaustive-legal-index':
                        exito = await self.actualizar_documento_completo(documento, datos_bd)
                    else:  # exhaustive-legal-chunks-v2
                        exito = await self.actualizar_chunk(documento, datos_bd)
                    
                    if exito:
                        stats['actualizados'] += 1
                        if stats['actualizados'] % 10 == 0:
                            print(f"   ✅ {stats['actualizados']} actualizados / {stats['procesados']} procesados")
                    else:
                        stats['errores'] += 1
                
                except Exception as e:
                    stats['errores'] += 1
                    if stats['errores'] <= 5:
                        print(f"   ❌ Error procesando documento: {e}")
                
                # Progreso cada 100 documentos
                if stats['procesados'] % 100 == 0:
                    print(f"   📊 Progreso: {stats['procesados']} procesados | {stats['actualizados']} actualizados | {stats['errores']} errores")
        
        finally:
            await search_client.close()
        
        return stats

    async def ejecutar_correccion(self):
        """Proceso principal de corrección"""
        print("🚀 INICIANDO CORRECCIÓN MASIVA DE AMBOS ÍNDICES")
        print("=" * 80)
        
        # 1. Cargar datos de PostgreSQL
        total_bd = self.cargar_datos_bd()
        print(f"📊 Total documentos disponibles en BD: {total_bd}")
        
        # 2. Procesar cada índice
        for index_name in self.indices.keys():
            stats = await self.procesar_indice(index_name)
            self.estadisticas[index_name] = stats
        
        # 3. Reporte final
        print(f"\n{'='*80}")
        print("📊 REPORTE FINAL DE CORRECCIÓN")
        print(f"{'='*80}")
        
        for index_name, descripcion in self.indices.items():
            stats = self.estadisticas[index_name]
            print(f"\n📋 {descripcion} ({index_name}):")
            print(f"   Documentos procesados: {stats['procesados']}")
            print(f"   Actualizaciones exitosas: {stats['actualizados']}")
            print(f"   Errores: {stats['errores']}")
        
        print(f"\n{'='*80}")

async def main():
    """Función principal"""
    corrector = CorrectorAzureIndices()
    
    print("⚠️  CORRECCIÓN DE ÍNDICES AZURE SEARCH")
    print("Este script actualizará metadatos faltantes en:")
    print("- exhaustive-legal-index (documentos completos)")
    print("- exhaustive-legal-chunks-v2 (chunks con trazabilidad)")
    print("\nUsando datos de PostgreSQL (documentos_juridicos_gpt4)")
    
    # Ejecutar automáticamente para prueba
    print("Iniciando corrección automática...")
    
    # respuesta = input("\n¿Desea continuar? (y/n): ")
    # if respuesta.lower() != 'y':
    #     print("Operación cancelada.")
    #     return
    
    await corrector.ejecutar_correccion()

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