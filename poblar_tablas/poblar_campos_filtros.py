#!/usr/bin/env python3
"""
Script para poblar campos específicos de filtros en Azure Search
Basado en análisis de mapeo filtros → Azure Search fields
"""

import asyncio
import os
import sys
from dotenv import load_dotenv
from azure.search.documents.aio import SearchClient
from azure.core.credentials import AzureKeyCredential
import psycopg2
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

class PobladorCamposFiltros:
    """Pobla campos específicos necesarios para filtros de interfaz"""
    
    def __init__(self):
        self.endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
        self.key = os.getenv('AZURE_SEARCH_KEY')
        self.datos_bd = {}
        self.datos_tipos = {}
        self.datos_fechas = {}
        self.datos_lugares = {}

    def cargar_datos_tipos_desde_metadatos(self):
        """Carga tipos de documento desde metadatos (detalle)"""
        print("📊 Cargando tipos de documento desde metadatos...")
        
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        try:
            # Usar campo detalle de metadatos como tipo de documento
            query = """
            SELECT 
                d.archivo,
                COALESCE(TRIM(m.detalle), 'Documento') as tipo_documento,
                COALESCE(TRIM(m.nuc), '') as nuc
            FROM documentos d
            LEFT JOIN metadatos m ON d.id = m.documento_id
            WHERE d.archivo IS NOT NULL
            """
            
            cursor.execute(query)
            resultados = cursor.fetchall()
            
            for row in resultados:
                archivo = row[0]
                if archivo:
                    nombre_base = os.path.basename(archivo)
                    datos = {
                        'tipo_documento': self.limpiar_valor(row[1]) or 'Documento',
                        'nuc': self.limpiar_valor(row[2])
                    }
                    
                    # Múltiples claves para mapeo
                    self.datos_tipos[nombre_base] = datos
                    nombre_sin_ext = nombre_base.replace('.pdf', '')
                    self.datos_tipos[nombre_sin_ext] = datos
                    
                    if '_batch_resultado_' in nombre_sin_ext:
                        nombre_limpio = nombre_sin_ext.split('_batch_resultado_')[0] + '.pdf'
                        self.datos_tipos[nombre_limpio] = datos
            
            print(f"✅ {len(resultados)} tipos de documento cargados")
            return len(resultados)
            
        finally:
            cursor.close()
            conn.close()

    def cargar_datos_fechas_lugares(self):
        """Carga fechas y lugares desde tablas de análisis"""
        print("📊 Cargando fechas y lugares desde análisis...")
        
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        try:
            # Fechas principales por documento
            cursor.execute("""
                SELECT 
                    d.archivo,
                    af.fecha
                FROM documentos d
                JOIN analisis_fechas af ON d.id = af.documento_id
                WHERE af.fecha IS NOT NULL
                ORDER BY d.archivo, af.fecha
            """)
            
            for row in cursor.fetchall():
                archivo = row[0]
                if archivo:
                    nombre_base = os.path.basename(archivo)
                    if nombre_base not in self.datos_fechas:
                        self.datos_fechas[nombre_base] = str(row[1])
            
            # Lugares principales por documento
            cursor.execute("""
                SELECT 
                    d.archivo,
                    al.departamento,
                    al.municipio
                FROM documentos d
                JOIN analisis_lugares al ON d.id = al.documento_id
                WHERE al.departamento IS NOT NULL OR al.municipio IS NOT NULL
                ORDER BY d.archivo
            """)
            
            for row in cursor.fetchall():
                archivo = row[0]
                if archivo:
                    nombre_base = os.path.basename(archivo)
                    if nombre_base not in self.datos_lugares:
                        self.datos_lugares[nombre_base] = {
                            'departamento': self.limpiar_valor(row[1]),
                            'municipio': self.limpiar_valor(row[2])
                        }
            
            print(f"✅ {len(self.datos_fechas)} fechas y {len(self.datos_lugares)} lugares cargados")
            
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

    def buscar_tipo_documento(self, nombre_archivo: str) -> Optional[str]:
        """Busca tipo de documento"""
        if not nombre_archivo:
            return None
            
        if nombre_archivo in self.datos_tipos:
            return self.datos_tipos[nombre_archivo].get('tipo_documento')
        
        # Búsqueda por patrón
        nombre_base = nombre_archivo.replace('.pdf', '').replace('.json', '')
        for clave_bd, datos in self.datos_tipos.items():
            if nombre_base in clave_bd or clave_bd.replace('.pdf', '') in nombre_base:
                return datos.get('tipo_documento')
        
        return 'Documento'  # Valor por defecto

    def buscar_nuc(self, nombre_archivo: str) -> Optional[str]:
        """Busca NUC del documento"""
        if not nombre_archivo:
            return None
            
        if nombre_archivo in self.datos_tipos:
            return self.datos_tipos[nombre_archivo].get('nuc')
        
        # Búsqueda por patrón
        nombre_base = nombre_archivo.replace('.pdf', '').replace('.json', '')
        for clave_bd, datos in self.datos_tipos.items():
            if nombre_base in clave_bd or clave_bd.replace('.pdf', '') in nombre_base:
                return datos.get('nuc')
        
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

    async def poblar_tipos_documento(self, index_name: str, descripcion: str):
        """Pobla campo tipo_documento"""
        print(f"\n📋 POBLANDO TIPOS DE DOCUMENTO: {descripcion}")
        print("=" * 60)
        
        search_client = SearchClient(
            endpoint=self.endpoint,
            index_name=index_name,
            credential=AzureKeyCredential(self.key)
        )
        
        stats = {'procesados': 0, 'actualizados': 0, 'errores': 0}
        lote_actualizacion = []
        LOTE_SIZE = 50
        
        try:
            # Total documentos sin tipo_documento
            filter_query = "tipo_documento eq null or tipo_documento eq ''"
            results = await search_client.search(
                search_text="*",
                filter=filter_query,
                top=0,
                include_total_count=True
            )
            total_sin_tipo = await results.get_count()
            print(f"📊 Documentos sin tipo_documento: {total_sin_tipo:,}")
            
            if total_sin_tipo == 0:
                print("✅ Todos los documentos ya tienen tipo_documento")
                return stats
            
            # Procesar documentos sin tipo
            skip = 0
            page_size = 200
            
            while skip < total_sin_tipo:
                print(f"   📄 Procesando desde posición {skip:,}...")
                
                results = await search_client.search(
                    search_text="*",
                    filter=filter_query,
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
                        
                        # Buscar tipo de documento
                        tipo_documento = self.buscar_tipo_documento(nombre_archivo)
                        if not tipo_documento:
                            continue
                        
                        # Preparar actualización según el índice
                        if index_name == 'exhaustive-legal-index':
                            doc_update = {
                                "id": documento['id'], 
                                "tipo_documento": tipo_documento
                            }
                        else:  # chunks-v2
                            doc_update = {
                                "chunk_id": documento['chunk_id'], 
                                "tipo_documento": tipo_documento
                            }
                            
                            # También poblar NUC si falta
                            if not documento.get('nuc'):
                                nuc = self.buscar_nuc(nombre_archivo)
                                if nuc:
                                    doc_update["nuc"] = nuc
                        
                        lote_actualizacion.append(doc_update)
                        
                        # Procesar lote cuando esté lleno
                        if len(lote_actualizacion) >= LOTE_SIZE:
                            exitosos = await self.actualizar_lote_documentos(index_name, lote_actualizacion)
                            stats['actualizados'] += exitosos
                            lote_actualizacion = []
                            
                            # Mostrar progreso
                            if stats['procesados'] % 1000 == 0:
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
                
                if documentos_en_pagina == 0:
                    break
                
                await asyncio.sleep(0.1)
                
        finally:
            await search_client.close()
        
        return stats

    async def ejecutar_poblamiento_filtros(self):
        """Ejecuta poblamiento de campos para filtros"""
        print("🚀 POBLAMIENTO DE CAMPOS PARA FILTROS DE INTERFAZ")
        print("=" * 80)
        
        inicio = time.time() if 'time' in globals() else 0
        
        # Cargar datos
        total_tipos = self.cargar_datos_tipos_desde_metadatos()
        self.cargar_datos_fechas_lugares()
        
        # Procesar índices para tipo_documento
        indices = [
            ('exhaustive-legal-index', 'Documentos Completos'),
            ('exhaustive-legal-chunks-v2', 'Chunks con Trazabilidad')
        ]
        
        estadisticas_totales = {}
        
        for index_name, descripcion in indices:
            try:
                stats = await self.poblar_tipos_documento(index_name, descripcion)
                estadisticas_totales[index_name] = stats
            except Exception as e:
                print(f"❌ Error procesando {index_name}: {e}")
                estadisticas_totales[index_name] = {'procesados': 0, 'actualizados': 0, 'errores': 1}
        
        # Reporte final
        print(f"\n{'='*80}")
        print("📊 REPORTE FINAL - POBLAMIENTO CAMPOS FILTROS")
        print(f"{'='*80}")
        print(f"📊 Tipos disponibles en BD: {total_tipos:,}")
        print(f"📊 Fechas disponibles: {len(self.datos_fechas):,}")
        print(f"📊 Lugares disponibles: {len(self.datos_lugares):,}")
        
        for index_name, descripcion in indices:
            stats = estadisticas_totales.get(index_name, {})
            print(f"\n📋 {descripcion}:")
            print(f"   Procesados: {stats.get('procesados', 0):,}")
            print(f"   Actualizados: {stats.get('actualizados', 0):,}")
            print(f"   Errores: {stats.get('errores', 0):,}")
        
        print(f"\n✅ CAMPOS PRIORITARIOS POBLADOS:")
        print(f"   • tipo_documento: Agregado desde metadatos.detalle")
        print(f"   • NUC en chunks-v2: Complementado donde faltaba")
        
        print(f"\n📝 NOTA: Para fechas, departamentos y municipios se requiere:")
        print(f"   • Agregar campos fecha_documento, departamento, municipio al esquema de Azure Search")
        print(f"   • Datos disponibles en PostgreSQL: {len(self.datos_fechas):,} fechas, {len(self.datos_lugares):,} lugares")
        
        print(f"\n{'='*80}")

import time

async def main():
    poblador = PobladorCamposFiltros()
    await poblador.ejecutar_poblamiento_filtros()

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