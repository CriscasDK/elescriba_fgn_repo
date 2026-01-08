#!/usr/bin/env python3
"""
Script para analizar mapeo entre filtros de interfaz y campos Azure Search
Identifica qué campos necesitan poblarse para soportar filtros de la interfaz
"""

import asyncio
import os
import sys
from dotenv import load_dotenv
from azure.search.documents.aio import SearchClient
from azure.core.credentials import AzureKeyCredential
import psycopg2

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

class AnalizadorMapeoFiltros:
    """Analiza mapeo entre filtros interfaz y Azure Search"""
    
    def __init__(self):
        self.endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
        self.key = os.getenv('AZURE_SEARCH_KEY')
        
        # Mapeo de filtros de interfaz a campos Azure Search
        self.mapeo_filtros = {
            'exhaustive-legal-index': {
                'nuc': 'metadatos_nuc',           # ✅ Ya poblado
                'fechas': 'fecha_documento',       # ❌ Necesita poblar
                'despacho': 'metadatos_despacho', # ✅ Ya poblado  
                'tipo_documento': 'tipo_documento', # ❌ Necesita poblar
                'departamento': 'departamento',    # ❌ Necesita poblar
                'municipio': 'municipio'          # ❌ Necesita poblar
            },
            'exhaustive-legal-chunks-v2': {
                'nuc': 'nuc',                     # ✅ Ya poblado
                'fechas': 'fecha_documento',       # ❌ Necesita poblar
                'departamento': 'departamento',    # ❌ Necesita poblar
                'municipio': 'municipio',         # ❌ Necesita poblar
                'tipo_documento': 'tipo_documento' # ❌ Necesita poblar
            }
        }

    async def inspeccionar_campos_azure(self, index_name):
        """Inspecciona campos disponibles en Azure Search"""
        print(f"\n🔍 INSPECCIONANDO CAMPOS: {index_name}")
        print("=" * 60)
        
        search_client = SearchClient(
            endpoint=self.endpoint,
            index_name=index_name,
            credential=AzureKeyCredential(self.key)
        )
        
        try:
            # Obtener muestra de documentos
            results = await search_client.search(search_text="*", top=5)
            
            campos_encontrados = set()
            
            async for doc in results:
                campos_encontrados.update(doc.keys())
            
            print(f"📋 Campos disponibles en {index_name}:")
            for campo in sorted(campos_encontrados):
                print(f"   - {campo}")
            
            return campos_encontrados
            
        finally:
            await search_client.close()

    def analizar_disponibilidad_datos_bd(self):
        """Analiza qué datos están disponibles en PostgreSQL"""
        print(f"\n📊 ANALIZANDO DISPONIBILIDAD DE DATOS EN BD")
        print("=" * 60)
        
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        disponibilidad = {}
        
        try:
            # Fechas
            cursor.execute("""
                SELECT COUNT(DISTINCT documento_id) as docs_con_fechas
                FROM analisis_fechas 
                WHERE fecha IS NOT NULL
            """)
            docs_con_fechas = cursor.fetchone()[0]
            disponibilidad['fechas'] = docs_con_fechas
            
            # Lugares (departamentos/municipios)
            cursor.execute("""
                SELECT COUNT(DISTINCT documento_id) as docs_con_lugares
                FROM analisis_lugares 
                WHERE departamento IS NOT NULL OR municipio IS NOT NULL
            """)
            docs_con_lugares = cursor.fetchone()[0]
            disponibilidad['lugares'] = docs_con_lugares
            
            # Tipos de documento
            cursor.execute("""
                SELECT COUNT(DISTINCT documento_id) as docs_con_tipos
                FROM analisis_tipo_documento 
                WHERE tipo_especifico IS NOT NULL
            """)
            docs_con_tipos = cursor.fetchone()[0]
            disponibilidad['tipos'] = docs_con_tipos
            
            # Total documentos
            cursor.execute("SELECT COUNT(*) FROM documentos")
            total_docs = cursor.fetchone()[0]
            disponibilidad['total'] = total_docs
            
            print(f"📊 Disponibilidad de datos:")
            print(f"   Total documentos: {total_docs:,}")
            print(f"   Docs con fechas: {docs_con_fechas:,} ({docs_con_fechas/total_docs*100:.1f}%)")
            print(f"   Docs con lugares: {docs_con_lugares:,} ({docs_con_lugares/total_docs*100:.1f}%)")
            print(f"   Docs con tipos: {docs_con_tipos:,} ({docs_con_tipos/total_docs*100:.1f}%)")
            
            return disponibilidad
            
        finally:
            cursor.close()
            conn.close()

    async def verificar_estado_actual_campos(self, index_name):
        """Verifica estado actual de campos específicos"""
        print(f"\n🔍 VERIFICANDO ESTADO ACTUAL: {index_name}")
        print("=" * 60)
        
        search_client = SearchClient(
            endpoint=self.endpoint,
            index_name=index_name,
            credential=AzureKeyCredential(self.key)
        )
        
        campos_verificar = self.mapeo_filtros.get(index_name, {})
        estadisticas = {}
        
        try:
            # Total documentos
            count_result = await search_client.search(search_text="*", top=0, include_total_count=True)
            total = await count_result.get_count()
            
            print(f"📊 Total documentos: {total:,}")
            
            for filtro, campo_azure in campos_verificar.items():
                try:
                    # Contar documentos con campo poblado
                    filter_query = f"{campo_azure} ne null and {campo_azure} ne ''"
                    results = await search_client.search(
                        search_text="*",
                        filter=filter_query,
                        top=0,
                        include_total_count=True
                    )
                    poblados = await results.get_count()
                    porcentaje = (poblados / total * 100) if total > 0 else 0
                    
                    estadisticas[filtro] = {
                        'campo_azure': campo_azure,
                        'poblados': poblados,
                        'porcentaje': porcentaje
                    }
                    
                    estado = "✅" if porcentaje > 50 else "❌"
                    print(f"   {estado} {filtro} ({campo_azure}): {poblados:,}/{total:,} ({porcentaje:.1f}%)")
                    
                except Exception as e:
                    print(f"   ❓ {filtro} ({campo_azure}): Error - {e}")
                    estadisticas[filtro] = {'error': str(e)}
            
            return estadisticas
            
        finally:
            await search_client.close()

    def generar_plan_poblamiento(self, estadisticas_indices, disponibilidad_bd):
        """Genera plan de poblamiento basado en análisis"""
        print(f"\n📋 PLAN DE POBLAMIENTO RECOMENDADO")
        print("=" * 80)
        
        campos_prioritarios = []
        
        for index_name, stats in estadisticas_indices.items():
            print(f"\n🎯 {index_name}:")
            
            for filtro, datos in stats.items():
                if isinstance(datos, dict) and 'porcentaje' in datos:
                    porcentaje = datos['porcentaje']
                    campo_azure = datos['campo_azure']
                    
                    if porcentaje < 50:  # Menos del 50% poblado
                        prioridad = "ALTA" if porcentaje < 10 else "MEDIA"
                        
                        # Determinar fuente de datos
                        fuente_datos = self.determinar_fuente_datos(filtro)
                        
                        campos_prioritarios.append({
                            'indice': index_name,
                            'filtro': filtro,
                            'campo_azure': campo_azure,
                            'porcentaje_actual': porcentaje,
                            'prioridad': prioridad,
                            'fuente_datos': fuente_datos
                        })
                        
                        print(f"   🔴 {filtro}: {porcentaje:.1f}% - Prioridad {prioridad}")
                        print(f"      Campo Azure: {campo_azure}")
                        print(f"      Fuente datos: {fuente_datos}")
                    else:
                        print(f"   ✅ {filtro}: {porcentaje:.1f}% - OK")
        
        return campos_prioritarios

    def determinar_fuente_datos(self, filtro):
        """Determina la fuente de datos PostgreSQL para cada filtro"""
        mapeo_fuentes = {
            'fechas': 'analisis_fechas.fecha',
            'departamento': 'analisis_lugares.departamento', 
            'municipio': 'analisis_lugares.municipio',
            'tipo_documento': 'analisis_tipo_documento.tipo_especifico'
        }
        return mapeo_fuentes.get(filtro, 'metadatos (ya disponible)')

    async def ejecutar_analisis_completo(self):
        """Ejecuta análisis completo"""
        print("🚀 ANÁLISIS DE MAPEO FILTROS → AZURE SEARCH")
        print("=" * 80)
        
        # Análizar disponibilidad en BD
        disponibilidad_bd = self.analizar_disponibilidad_datos_bd()
        
        # Analizar estados actuales
        indices = ['exhaustive-legal-index', 'exhaustive-legal-chunks-v2']
        estadisticas_indices = {}
        
        for index_name in indices:
            # Inspeccionar campos
            await self.inspeccionar_campos_azure(index_name)
            
            # Verificar estado actual
            stats = await self.verificar_estado_actual_campos(index_name)
            estadisticas_indices[index_name] = stats
        
        # Generar plan
        plan = self.generar_plan_poblamiento(estadisticas_indices, disponibilidad_bd)
        
        # Resumen final
        print(f"\n{'='*80}")
        print("📊 RESUMEN EJECUTIVO")
        print(f"{'='*80}")
        
        print(f"\n🎯 CAMPOS PRIORITARIOS PARA POBLAR:")
        for item in plan:
            print(f"   • {item['filtro']} en {item['indice']}")
            print(f"     Campo: {item['campo_azure']} | Actual: {item['porcentaje_actual']:.1f}%")
            print(f"     Fuente: {item['fuente_datos']} | Prioridad: {item['prioridad']}")
            print()

async def main():
    analizador = AnalizadorMapeoFiltros()
    await analizador.ejecutar_analisis_completo()

if __name__ == "__main__":
    sys.path.append(os.path.dirname(__file__))
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
    
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()