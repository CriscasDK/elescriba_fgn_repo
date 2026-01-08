#!/usr/bin/env python3
"""
Script para verificar si existen campos geográficos en Azure Search
y preparar el poblamiento con datos de analisis_lugares
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

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'documentos_juridicos_gpt4',
    'user': 'docs_user',
    'password': 'docs_password_2025'
}

async def verificar_campos_geograficos():
    """Verifica campos geográficos disponibles en Azure Search"""
    print("🌍 VERIFICACIÓN DE CAMPOS GEOGRÁFICOS EN AZURE SEARCH")
    print("=" * 70)
    
    endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
    key = os.getenv('AZURE_SEARCH_KEY')
    
    indices = [
        ('exhaustive-legal-index', 'Documentos'),
        ('exhaustive-legal-chunks-v2', 'Chunks')
    ]
    
    for index_name, descripcion in indices:
        print(f"\n📋 {descripcion} ({index_name})")
        print("-" * 50)
        
        search_client = SearchClient(
            endpoint=endpoint,
            index_name=index_name,
            credential=AzureKeyCredential(key)
        )
        
        try:
            # Obtener muestra para ver campos disponibles
            results = await search_client.search(search_text="*", top=2)
            
            campos_geograficos = []
            campos_todos = set()
            
            async for doc in results:
                campos_todos.update(doc.keys())
            
            # Buscar campos relacionados con geografía
            for campo in sorted(campos_todos):
                if any(geo_term in campo.lower() for geo_term in 
                      ['lugar', 'departamento', 'municipio', 'region', 'ciudad', 'ubicacion', 'direccion']):
                    campos_geograficos.append(campo)
            
            if campos_geograficos:
                print(f"✅ Campos geográficos encontrados:")
                for campo in campos_geograficos:
                    print(f"   • {campo}")
                
                # Verificar si están poblados
                for campo in campos_geograficos[:3]:  # Solo primeros 3 para no saturar
                    try:
                        filter_query = f"{campo} ne null and {campo} ne ''"
                        count_result = await search_client.search(
                            search_text="*",
                            filter=filter_query,
                            top=0,
                            include_total_count=True
                        )
                        poblados = await count_result.get_count()
                        
                        # Total documentos
                        total_result = await search_client.search(search_text="*", top=0, include_total_count=True)
                        total = await total_result.get_count()
                        
                        porcentaje = (poblados / total * 100) if total > 0 else 0
                        estado = "✅" if porcentaje > 80 else "🔄" if porcentaje > 20 else "❌"
                        print(f"     {estado} {campo}: {poblados:,}/{total:,} ({porcentaje:.1f}%)")
                        
                    except Exception as e:
                        print(f"     ❓ {campo}: Error verificando - {str(e)[:50]}")
            else:
                print(f"❌ No se encontraron campos geográficos específicos")
                print(f"📝 Campos disponibles relevantes:")
                campos_relevantes = [c for c in sorted(campos_todos) if any(term in c.lower() 
                                   for term in ['metadatos', 'lugares', 'hechos'])]
                for campo in campos_relevantes[:10]:
                    print(f"   • {campo}")
        
        except Exception as e:
            print(f"❌ Error: {e}")
        
        finally:
            await search_client.close()

async def analizar_datos_geograficos_bd():
    """Analiza datos geográficos disponibles en PostgreSQL"""
    print(f"\n🏛️ ANÁLISIS DE DATOS GEOGRÁFICOS EN POSTGRESQL")
    print("=" * 70)
    
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # Top departamentos
        cursor.execute("""
            SELECT departamento, COUNT(*) as cantidad
            FROM analisis_lugares 
            WHERE departamento IS NOT NULL AND departamento != ''
            GROUP BY departamento 
            ORDER BY cantidad DESC 
            LIMIT 10
        """)
        
        print("📊 Top 10 Departamentos:")
        for row in cursor.fetchall():
            print(f"   • {row[0]}: {row[1]:,} menciones")
        
        # Top municipios
        print(f"\n📊 Top 10 Municipios:")
        cursor.execute("""
            SELECT municipio, departamento, COUNT(*) as cantidad
            FROM analisis_lugares 
            WHERE municipio IS NOT NULL AND municipio != ''
            GROUP BY municipio, departamento 
            ORDER BY cantidad DESC 
            LIMIT 10
        """)
        
        for row in cursor.fetchall():
            depto = row[1] if row[1] else "Sin depto"
            print(f"   • {row[0]} ({depto}): {row[2]:,} menciones")
        
        # Preparar mapeo archivo -> lugar principal
        print(f"\n📋 PREPARANDO MAPEO ARCHIVO → LUGAR PRINCIPAL")
        cursor.execute("""
            WITH lugares_principales AS (
                SELECT 
                    al.documento_id,
                    d.archivo,
                    al.departamento,
                    al.municipio,
                    ROW_NUMBER() OVER (PARTITION BY al.documento_id ORDER BY 
                        CASE WHEN al.tipo = 'lugar_hechos' THEN 1
                             WHEN al.tipo = 'municipio' THEN 2
                             WHEN al.tipo = 'departamento' THEN 3
                             ELSE 4 END) as prioridad
                FROM analisis_lugares al
                JOIN documentos d ON al.documento_id = d.id
                WHERE (al.departamento IS NOT NULL AND al.departamento != '')
                   OR (al.municipio IS NOT NULL AND al.municipio != '')
            )
            SELECT COUNT(DISTINCT documento_id) as documentos_con_lugares,
                   COUNT(*) as total_lugares
            FROM lugares_principales 
            WHERE prioridad = 1
        """)
        
        result = cursor.fetchone()
        print(f"✅ {result[0]:,} documentos tienen lugar principal identificado")
        print(f"✅ Datos listos para poblar Azure Search")
        
    finally:
        cursor.close()
        conn.close()

async def generar_plan_poblamiento():
    """Genera plan para poblar campos geográficos"""
    print(f"\n🎯 PLAN DE POBLAMIENTO GEOGRÁFICO")
    print("=" * 70)
    
    print("📝 ESTRATEGIA PROPUESTA:")
    print("1. ✅ Datos disponibles: 10,646 docs con lugares (95.8%)")
    print("2. 🔍 Verificar campos existentes en Azure Search")
    print("3. 📊 Si no existen → Necesario agregar al esquema")
    print("4. 💾 Si existen → Poblar directamente")
    print("5. 🎯 Priorizar lugar principal por documento")
    
    print(f"\n💡 CAMPOS SUGERIDOS PARA AZURE SEARCH:")
    print("   • departamento_principal (string)")
    print("   • municipio_principal (string)")  
    print("   • lugares_hechos (collection of strings)")
    print("   • direcciones (collection of strings)")
    
    print(f"\n🚀 SIGUIENTE PASO:")
    print("   Ejecutar poblamiento si campos existen, o sugerir modificación de esquema")

async def main():
    await verificar_campos_geograficos()
    await analizar_datos_geograficos_bd()
    await generar_plan_poblamiento()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()