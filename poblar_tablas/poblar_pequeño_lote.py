#!/usr/bin/env python3
"""
Script para poblar un lote pequeño y verificar que funciona
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

async def poblar_lote_pequeño():
    """Pobla solo un lote pequeño para probar"""
    print("🧪 POBLAMIENTO DE LOTE PEQUEÑO (PRUEBA)")
    print("=" * 50)
    
    endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
    key = os.getenv('AZURE_SEARCH_KEY')
    
    # 1. Cargar algunos datos de ejemplo
    print("📊 Cargando muestra de datos...")
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
        LIMIT 50
    """)
    
    mapeo = {}
    for row in cursor.fetchall():
        archivo = row[0]
        if archivo:
            nombre = os.path.basename(archivo)
            mapeo[nombre] = {
                'tipo': row[1] or 'Documento',
                'nuc': row[2]
            }
    
    cursor.close()
    conn.close()
    print(f"✅ {len(mapeo)} archivos en mapeo")
    
    # 2. Probar chunks-v2 (más necesario)
    print("\n📋 Probando exhaustive-legal-chunks-v2...")
    
    search_client = SearchClient(
        endpoint=endpoint,
        index_name='exhaustive-legal-chunks-v2',
        credential=AzureKeyCredential(key)
    )
    
    try:
        # Obtener pocos chunks sin tipo
        filter_query = "tipo_documento eq null or tipo_documento eq ''"
        results = await search_client.search(
            search_text="*",
            filter=filter_query,
            top=20,
            select="chunk_id,nombre_archivo,tipo_documento,nuc"
        )
        
        lote = []
        actualizados = 0
        
        async for doc in results:
            nombre_archivo = doc.get('nombre_archivo', '')
            if nombre_archivo in mapeo:
                datos = mapeo[nombre_archivo]
                
                update_doc = {"chunk_id": doc['chunk_id']}
                
                # Agregar tipo si falta
                if not doc.get('tipo_documento') and datos.get('tipo'):
                    update_doc["tipo_documento"] = datos['tipo']
                
                # Agregar NUC si falta  
                if not doc.get('nuc') and datos.get('nuc'):
                    update_doc["nuc"] = datos['nuc']
                
                if len(update_doc) > 1:  # Más que solo chunk_id
                    lote.append(update_doc)
                    print(f"   📝 Preparado: {nombre_archivo} → {datos['tipo']}")
        
        # Actualizar lote
        if lote:
            print(f"\n🔄 Actualizando {len(lote)} chunks...")
            result = await search_client.merge_or_upload_documents(lote)
            actualizados = sum(1 for r in result if r.succeeded)
            print(f"✅ {actualizados} chunks actualizados exitosamente")
        else:
            print("ℹ️  No se encontraron chunks para actualizar")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        await search_client.close()
    
    print(f"\n{'='*50}")
    print("✅ PRUEBA COMPLETADA")
    if actualizados > 0:
        print("🎯 El poblamiento funciona correctamente")
        print("💡 Se puede proceder con el script completo")
    print(f"{'='*50}")

async def main():
    await poblar_lote_pequeño()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ Error: {e}")