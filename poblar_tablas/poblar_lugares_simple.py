#!/usr/bin/env python3
"""
Script simple para poblar algunos campos de lugares como prueba
"""

import asyncio
import os
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

async def poblar_lugares_simple():
    """Poblamiento simple de lugares - solo los primeros 50 documentos"""
    print("🌍 POBLAMIENTO SIMPLE DE LUGARES - PRUEBA")
    print("=" * 60)
    
    # 1. Cargar algunos lugares desde BD
    print("📊 Cargando muestra de lugares desde PostgreSQL...")
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT DISTINCT
            d.archivo,
            COALESCE(al.departamento, '') as departamento,
            COALESCE(al.municipio, '') as municipio,
            COALESCE(al.nombre, '') as lugar_nombre
        FROM documentos d
        JOIN analisis_lugares al ON d.id = al.documento_id
        WHERE d.archivo IS NOT NULL
          AND al.departamento IS NOT NULL
        LIMIT 100
    """)
    
    mapeo_lugares = {}
    for row in cursor.fetchall():
        archivo = row[0]
        if archivo:
            nombre_base = os.path.basename(archivo)
            datos = {
                'departamento': row[1],
                'municipio': row[2], 
                'lugar_nombre': row[3]
            }
            mapeo_lugares[nombre_base] = datos
            # También mapear versión sin .pdf
            nombre_sin_ext = nombre_base.replace('.pdf', '')
            mapeo_lugares[nombre_sin_ext] = datos
    
    cursor.close()
    conn.close()
    
    print(f"✅ {len(mapeo_lugares)} archivos en mapeo")
    
    # 2. Poblar exhaustive-legal-index
    print("\n📋 Poblando exhaustive-legal-index...")
    
    endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
    key = os.getenv('AZURE_SEARCH_KEY')
    
    search_client = SearchClient(
        endpoint=endpoint,
        index_name='exhaustive-legal-index',
        credential=AzureKeyCredential(key)
    )
    
    try:
        # Obtener algunos documentos
        results = await search_client.search(
            search_text="*",
            top=50,
            select="id,archivo,lugares_hechos"
        )
        
        lote = []
        actualizados = 0
        procesados = 0
        
        async for doc in results:
            procesados += 1
            
            # Verificar si ya tiene lugares_hechos
            if doc.get('lugares_hechos'):
                continue
            
            archivo = doc.get('archivo', '')
            if not archivo:
                continue
            
            nombre_archivo = os.path.basename(archivo)
            if nombre_archivo in mapeo_lugares:
                datos = mapeo_lugares[nombre_archivo]
                
                # Crear string de lugares
                lugares_partes = []
                if datos['departamento']:
                    lugares_partes.append(datos['departamento'])
                if datos['municipio']:
                    lugares_partes.append(datos['municipio'])
                if datos['lugar_nombre'] and datos['lugar_nombre'] not in lugares_partes:
                    lugares_partes.append(datos['lugar_nombre'])
                
                if lugares_partes:
                    lugares_string = " | ".join(lugares_partes[:3])
                    lote.append({
                        "id": doc['id'],
                        "lugares_hechos": lugares_string
                    })
                    
                    print(f"   📍 {nombre_archivo[:40]}... → {lugares_string}")
                    
                    if len(lote) >= 10:  # Procesar en lotes pequeños
                        try:
                            result = await search_client.merge_or_upload_documents(lote)
                            exitosos = sum(1 for r in result if r.succeeded)
                            actualizados += exitosos
                            print(f"   ✅ Lote procesado: {exitosos} exitosos")
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
                print(f"   ✅ Lote final: {exitosos} exitosos")
            except Exception as e:
                print(f"   ❌ Error en lote final: {e}")
        
        print(f"\n✅ RESUMEN:")
        print(f"   Documentos procesados: {procesados}")
        print(f"   Documentos actualizados: {actualizados}")
        
        if actualizados > 0:
            print(f"🎉 ¡Poblamiento exitoso! Formato correcto funcionando.")
        
    finally:
        await search_client.close()

async def main():
    await poblar_lugares_simple()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()