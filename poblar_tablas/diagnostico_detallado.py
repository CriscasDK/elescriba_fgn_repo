#!/usr/bin/env python3
"""
Diagnóstico detallado del estado actual para entender qué poblar
"""

import asyncio
import os
import sys
from dotenv import load_dotenv
from azure.search.documents.aio import SearchClient
from azure.core.credentials import AzureKeyCredential

# Cargar configuración
load_dotenv('config/.env')

async def diagnostico_detallado():
    """Diagnóstico detallado del estado actual"""
    print("🔍 DIAGNÓSTICO DETALLADO DE CAMPOS")
    print("=" * 60)
    
    endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
    key = os.getenv('AZURE_SEARCH_KEY')
    
    # Analizar chunks-v2
    print(f"\n📋 CHUNKS-V2 - ANÁLISIS DETALLADO")
    print("-" * 40)
    
    search_client = SearchClient(
        endpoint=endpoint,
        index_name='exhaustive-legal-chunks-v2',
        credential=AzureKeyCredential(key)
    )
    
    try:
        # Total chunks
        count_result = await search_client.search(search_text="*", top=0, include_total_count=True)
        total = await count_result.get_count()
        print(f"📊 Total chunks: {total:,}")
        
        # Sin tipo_documento
        filter_sin_tipo = "tipo_documento eq null or tipo_documento eq ''"
        results_sin_tipo = await search_client.search(
            search_text="*",
            filter=filter_sin_tipo,
            top=0,
            include_total_count=True
        )
        sin_tipo = await results_sin_tipo.get_count()
        print(f"❌ Sin tipo_documento: {sin_tipo:,} ({sin_tipo/total*100:.1f}%)")
        
        # Sin NUC
        filter_sin_nuc = "nuc eq null or nuc eq ''"
        results_sin_nuc = await search_client.search(
            search_text="*",
            filter=filter_sin_nuc,
            top=0,
            include_total_count=True
        )
        sin_nuc = await results_sin_nuc.get_count()
        print(f"❌ Sin NUC: {sin_nuc:,} ({sin_nuc/total*100:.1f}%)")
        
        # Ejemplos de chunks sin tipo
        print(f"\n🔍 Ejemplos de chunks sin tipo_documento:")
        sample_sin_tipo = await search_client.search(
            search_text="*",
            filter=filter_sin_tipo,
            top=5,
            select="chunk_id,nombre_archivo,tipo_documento"
        )
        
        count = 0
        async for doc in sample_sin_tipo:
            count += 1
            chunk_id = doc.get('chunk_id', 'N/A')
            nombre_archivo = doc.get('nombre_archivo', 'N/A')
            tipo = doc.get('tipo_documento', 'NULL')
            print(f"   {count}. Chunk: {chunk_id[:30]}...")
            print(f"      Archivo: {nombre_archivo}")
            print(f"      Tipo actual: {tipo}")
            
            # Verificar si el archivo tiene extensión json
            if nombre_archivo and '.json' in nombre_archivo:
                nombre_pdf = nombre_archivo.replace('.json', '.pdf')
                print(f"      Nombre PDF equivalente: {nombre_pdf}")
            print()
        
        # Ejemplos de chunks CON tipo (para comparar)
        print(f"\n✅ Ejemplos de chunks CON tipo_documento:")
        filter_con_tipo = "tipo_documento ne null and tipo_documento ne ''"
        sample_con_tipo = await search_client.search(
            search_text="*",
            filter=filter_con_tipo,
            top=3,
            select="chunk_id,nombre_archivo,tipo_documento"
        )
        
        count = 0
        async for doc in sample_con_tipo:
            count += 1
            chunk_id = doc.get('chunk_id', 'N/A')
            nombre_archivo = doc.get('nombre_archivo', 'N/A')
            tipo = doc.get('tipo_documento', 'N/A')
            print(f"   {count}. Chunk: {chunk_id[:30]}...")
            print(f"      Archivo: {nombre_archivo}")  
            print(f"      Tipo: {tipo}")
            print()
    
    finally:
        await search_client.close()
    
    # Verificar correspondencia con BD
    print(f"\n📊 VERIFICACIÓN DE CORRESPONDENCIA BD")
    print("-" * 40)
    
    import psycopg2
    DB_CONFIG = {
        'host': 'localhost',
        'port': 5432,
        'database': 'documentos_juridicos_gpt4',
        'user': 'docs_user',
        'password': 'docs_password_2025'
    }
    
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Contar archivos en BD
    cursor.execute("SELECT COUNT(*) FROM documentos WHERE archivo IS NOT NULL")
    docs_bd = cursor.fetchone()[0]
    print(f"📊 Documentos en BD: {docs_bd:,}")
    
    # Verificar algunos archivos específicos de chunks sin tipo
    print(f"\n🔍 Verificando archivos específicos en BD:")
    archivos_test = [
        "2015005204_20H_7688C1_batch_resultado_20250618_172823.json",
        "2015005204_32.1B_6978_C1_batch_resultado_20250619_074725.json"
    ]
    
    for archivo in archivos_test:
        # Buscar archivo original
        cursor.execute("""
            SELECT d.archivo, m.detalle, m.nuc 
            FROM documentos d 
            LEFT JOIN metadatos m ON d.id = m.documento_id 
            WHERE d.archivo LIKE %s
        """, (f'%{archivo}%',))
        
        result = cursor.fetchone()
        if result:
            print(f"   ✅ {archivo[:40]}...")
            print(f"      BD archivo: {result[0]}")
            print(f"      BD tipo: {result[1]}")
            print(f"      BD NUC: {result[2]}")
        else:
            # Probar variaciones
            archivo_base = archivo.replace('.json', '').split('_batch_resultado_')[0]
            cursor.execute("""
                SELECT d.archivo, m.detalle, m.nuc 
                FROM documentos d 
                LEFT JOIN metadatos m ON d.id = m.documento_id 
                WHERE d.archivo LIKE %s
            """, (f'%{archivo_base}%',))
            
            results = cursor.fetchall()
            print(f"   🔍 {archivo[:40]}...")
            print(f"      Búsqueda por base '{archivo_base}': {len(results)} resultados")
            for r in results[:2]:
                print(f"         - {r[0]} | {r[1]} | {r[2]}")
        print()
    
    cursor.close()
    conn.close()
    
    print(f"{'='*60}")
    print("🎯 CONCLUSIONES:")
    print("• Verificar mapeo de nombres archivo Azure ↔ PostgreSQL")
    print("• Los chunks usan nombres con .json, BD puede tener .pdf")  
    print("• Necesitamos mapeo más robusto para encontrar correspondencias")
    print(f"{'='*60}")

async def main():
    await diagnostico_detallado()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()