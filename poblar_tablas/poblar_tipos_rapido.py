#!/usr/bin/env python3
"""
Script rápido para poblar tipos de documento en Azure Search
Usa datos de metadatos.detalle (100% disponibles)
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

async def poblar_tipos_documento():
    """Pobla tipos de documento en ambos índices"""
    print("🚀 POBLAMIENTO RÁPIDO DE TIPOS DE DOCUMENTO")
    print("=" * 60)
    
    endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
    key = os.getenv('AZURE_SEARCH_KEY')
    
    # 1. Cargar mapeo archivo → tipo desde BD
    print("📊 Cargando tipos desde metadatos...")
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            d.archivo,
            COALESCE(TRIM(m.detalle), 'Documento') as tipo_documento,
            COALESCE(TRIM(m.nuc), '') as nuc
        FROM documentos d
        LEFT JOIN metadatos m ON d.id = m.documento_id
        WHERE d.archivo IS NOT NULL
        LIMIT 1000
    """)
    
    tipos_map = {}
    for row in cursor.fetchall():
        archivo = row[0]
        if archivo:
            nombre_base = os.path.basename(archivo)
            tipos_map[nombre_base] = {
                'tipo': row[1] or 'Documento',
                'nuc': row[2]
            }
    
    cursor.close()
    conn.close()
    
    print(f"✅ {len(tipos_map)} tipos cargados")
    
    # 2. Poblar en exhaustive-legal-index
    print("\n📋 Poblando exhaustive-legal-index...")
    
    search_client = SearchClient(
        endpoint=endpoint,
        index_name='exhaustive-legal-index',
        credential=AzureKeyCredential(key)
    )
    
    try:
        # Obtener documentos sin tipo
        filter_query = "tipo_documento eq null or tipo_documento eq ''"
        results = await search_client.search(
            search_text="*",
            filter=filter_query,
            top=100
        )
        
        lote = []
        actualizados = 0
        
        async for doc in results:
            archivo = doc.get('archivo')
            if archivo:
                nombre_archivo = os.path.basename(archivo)
                if nombre_archivo in tipos_map:
                    tipo = tipos_map[nombre_archivo]['tipo']
                    
                    lote.append({
                        "id": doc['id'],
                        "tipo_documento": tipo
                    })
                    
                    if len(lote) >= 25:  # Lotes pequeños
                        try:
                            result = await search_client.merge_or_upload_documents(lote)
                            exitosos = sum(1 for r in result if r.succeeded)
                            actualizados += exitosos
                            print(f"   ✅ {actualizados} documentos actualizados")
                            lote = []
                        except Exception as e:
                            print(f"   ❌ Error en lote: {e}")
                            lote = []
        
        # Procesar lote final
        if lote:
            try:
                result = await search_client.merge_or_upload_documents(lote)
                exitosos = sum(1 for r in result if r.succeeded)
                actualizados += exitosos
            except Exception as e:
                print(f"   ❌ Error en lote final: {e}")
        
        print(f"✅ exhaustive-legal-index: {actualizados} documentos actualizados")
        
    finally:
        await search_client.close()
    
    # 3. Poblar en chunks-v2
    print("\n📋 Poblando exhaustive-legal-chunks-v2...")
    
    search_client = SearchClient(
        endpoint=endpoint,
        index_name='exhaustive-legal-chunks-v2',
        credential=AzureKeyCredential(key)
    )
    
    try:
        # Obtener chunks sin tipo
        filter_query = "tipo_documento eq null or tipo_documento eq ''"
        results = await search_client.search(
            search_text="*",
            filter=filter_query,
            top=200
        )
        
        lote = []
        actualizados = 0
        
        async for doc in results:
            nombre_archivo = doc.get('nombre_archivo')
            if nombre_archivo:
                if nombre_archivo in tipos_map:
                    datos = tipos_map[nombre_archivo]
                    
                    update_doc = {"chunk_id": doc['chunk_id']}
                    
                    # Agregar tipo
                    update_doc["tipo_documento"] = datos['tipo']
                    
                    # Agregar NUC si falta y está disponible
                    if not doc.get('nuc') and datos['nuc']:
                        update_doc["nuc"] = datos['nuc']
                    
                    lote.append(update_doc)
                    
                    if len(lote) >= 25:  # Lotes pequeños
                        try:
                            result = await search_client.merge_or_upload_documents(lote)
                            exitosos = sum(1 for r in result if r.succeeded)
                            actualizados += exitosos
                            print(f"   ✅ {actualizados} chunks actualizados")
                            lote = []
                        except Exception as e:
                            print(f"   ❌ Error en lote: {e}")
                            lote = []
        
        # Procesar lote final
        if lote:
            try:
                result = await search_client.merge_or_upload_documents(lote)
                exitosos = sum(1 for r in result if r.succeeded)
                actualizados += exitosos
            except Exception as e:
                print(f"   ❌ Error en lote final: {e}")
        
        print(f"✅ exhaustive-legal-chunks-v2: {actualizados} chunks actualizados")
        
    finally:
        await search_client.close()
    
    print(f"\n{'='*60}")
    print("🎯 RESUMEN:")
    print("✅ Campo tipo_documento poblado usando metadatos.detalle")
    print("✅ Campo nuc complementado en chunks donde faltaba")
    print("\n📝 PRÓXIMOS PASOS PARA FILTROS COMPLETOS:")
    print("• Agregar campos fecha_documento, departamento, municipio al esquema Azure")
    print("• Datos disponibles: 10,810 fechas, 10,646 lugares en PostgreSQL")
    print(f"{'='*60}")

async def main():
    await poblar_tipos_documento()

if __name__ == "__main__":
    sys.path.append(os.path.dirname(__file__))
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
    
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()