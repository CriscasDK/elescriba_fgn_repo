


#!/usr/bin/env python3
"""
Script robusto para poblar chunks-v2 con mapeo mejorado de nombres
Basado en diagnóstico: Azure tiene .json con _batch_resultado_, BD tiene .pdf sin eso
"""

import asyncio
import os
import sys
import re
from dotenv import load_dotenv
from azure.search.documents.aio import SearchClient
from azure.core.credentials import AzureKeyCredential
import psycopg2
import time

# Cargar configuración
load_dotenv('config/.env')

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'documentos_juridicos_gpt4',
    'user': 'docs_user',
    'password': 'docs_password_2025'
}

class PobladorChunksRobusto:
    def obtener_todos_los_chunks(self, carpeta_jsons='chunks_semanticos_mel_json'):
        """Obtiene todos los chunks de todos los archivos JSON en la carpeta indicada"""
        import glob
        import json
        documentos = []
        archivos_json = glob.glob(os.path.join(carpeta_jsons, '*.json'))
        print(f"📁 Buscando archivos JSON en: {carpeta_jsons}")
        print(f"📊 Total archivos JSON encontrados: {len(archivos_json):,}")
        for archivo_json in archivos_json:
            try:
                with open(archivo_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                # Cada archivo puede tener varios chunks
                chunks = data.get('chunks', [])
                for chunk in chunks:
                    # Normalizar chunk_id: solo letras, dígitos, guion bajo, guion y signo igual
                    import re
                    raw_chunk_id = chunk.get('chunk_id')
                    safe_chunk_id = re.sub(r'[^a-zA-Z0-9_\-=]', '_', raw_chunk_id) if raw_chunk_id else None
                    doc = {
                        'chunk_id': safe_chunk_id,
                        'texto_chunk': chunk.get('texto_chunk'),
                        'documento_id': data.get('documento_id'),
                        'archivo': data.get('archivo'),
                        'posicion': chunk.get('posicion'),
                        'num_oraciones': chunk.get('num_oraciones'),
                        'longitud': chunk.get('longitud'),
                        'mel_emedding': chunk.get('mel_embedding') if chunk.get('mel_embedding') is not None else [],
                        # Puedes agregar más campos si existen en el chunk/data
                    }
                    documentos.append(doc)
            except Exception as e:
                print(f"❌ Error leyendo {archivo_json}: {e}")
        print(f"🔎 Total de chunks a poblar: {len(documentos):,}")
        vacios = sum(1 for doc in documentos if not doc.get('mel_emedding'))
        print(f"⚠️ Chunks con mel_emedding vacío: {vacios:,}")
        return documentos
    """Poblador robusto para chunks-v2 con mapeo inteligente"""
    
    def __init__(self):
        self.endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
        self.key = os.getenv('AZURE_SEARCH_KEY')
        self.mapeo_base = {}  # Mapeo por nombre base
        self.stats = {'procesados': 0, 'encontrados': 0, 'actualizados': 0, 'errores': 0}
    
    def cargar_mapeo_inteligente(self):
        print("\n🔎 Nombres base en metadatos (primeros 20):")
        for i, nombre in enumerate(self.mapeo_base.keys()):
            if i < 20:
                print(f"  {nombre}")
            elif i == 20:
                print("  ...")
        """Carga mapeo inteligente desde BD"""
        print("📊 Cargando mapeo inteligente desde PostgreSQL...")
        
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        try:
            # Cargar todos los documentos con sus metadatos
            cursor.execute("""
                SELECT 
                    d.archivo,
                    COALESCE(TRIM(m.detalle), 'Documento') as tipo_documento,
                    COALESCE(TRIM(m.nuc), '') as nuc,
                    COALESCE(TRIM(m.despacho), '') as despacho
                FROM documentos d
                LEFT JOIN metadatos m ON d.id = m.documento_id
                WHERE d.archivo IS NOT NULL
                ORDER BY d.archivo
            """)
            
            resultados = cursor.fetchall()
            
            for row in resultados:
                archivo = row[0]
                datos = {
                    'tipo_documento': row[1] or 'Documento',
                    'nuc': row[2] if row[2] and row[2].strip() else None,
                    'despacho': row[3] if row[3] and row[3].strip() else None
                }
                # Eliminar extensión .pdf del nombre de archivo en metadatos
                nombre_base = os.path.splitext(os.path.basename(archivo))[0]
                # Normalizar: minúsculas y sin espacios
                nombre_base = nombre_base.strip().lower().replace(' ', '')
                if nombre_base:
                    self.mapeo_base[nombre_base] = datos
            
            print(f"✅ {len(resultados)} documentos → {len(self.mapeo_base)} nombres base")
            return len(resultados)
        
        finally:
            cursor.close()
            conn.close()
    
    def extraer_nombre_base(self, archivo: str) -> str:
        """Extrae nombre base del archivo para mapeo y normaliza (minúsculas, sin espacios)"""
        if not archivo:
            return ""
        nombre = os.path.basename(archivo)
        nombre_sin_ext = os.path.splitext(nombre)[0]
        nombre_base = re.sub(r'_batch_resultado_\d+_\d+$', '', nombre_sin_ext)
        nombre_base = nombre_base.strip().lower().replace(' ', '')
        return nombre_base
    
    def buscar_datos_por_nombre_azure(self, nombre_archivo_azure: str) -> dict:
        """Busca datos por nombre de archivo de Azure, normalizando el nombre base"""
        if not nombre_archivo_azure:
            return {}
        nombre_base = self.extraer_nombre_base(nombre_archivo_azure)
        return self.mapeo_base.get(nombre_base, {})
    
    async def procesar_lote_chunks(self, lote: list) -> int:
        """Procesa un lote de chunks con reintentos y backoff exponencial"""
        if not lote:
            return 0

        max_reintentos = 5
        espera_base = 1.0  # segundos
        reintento = 0
        while reintento < max_reintentos:
            search_client = SearchClient(
                endpoint=self.endpoint,
                index_name='chunks-mel-index',
                credential=AzureKeyCredential(self.key)
            )
            try:
                result = await search_client.merge_or_upload_documents(lote)
                exitosos = sum(1 for r in result if r.succeeded)
                # Pausa breve entre lotes para evitar saturar la red
                await asyncio.sleep(0.5)
                return exitosos
            except Exception as e:
                print(f"❌ Error en lote (intento {reintento+1}/{max_reintentos}): {str(e)[:100]}")
                # Backoff exponencial
                espera = espera_base * (2 ** reintento)
                print(f"⏳ Esperando {espera:.1f}s antes de reintentar...")
                await asyncio.sleep(espera)
                reintento += 1
            finally:
                await search_client.close()
        print(f"❌ Lote fallido tras {max_reintentos} intentos. Se omite este lote.")
        self.stats['errores'] += len(lote)
        return 0
    
    async def poblar_chunks_masivo(self):
        print(f"\n🚀 POBLAMIENTO MASIVO chunks-v2")
        print("=" * 60)
        search_client = SearchClient(
            endpoint=self.endpoint,
            index_name='chunks-mel-index',
            credential=AzureKeyCredential(self.key)
        )
        try:
            documentos = self.obtener_todos_los_chunks()
            print("\nProgreso:")
            print("Procesados | Actualizados | Errores | % Avance")
            LOTE_SIZE = 100
            total_chunks = len(documentos)
            procesados = 0
            actualizados = 0
            errores = 0
            lote_actual = []
            for doc in documentos:
                lote_actual.append(doc)
                procesados += 1
                if len(lote_actual) >= LOTE_SIZE:
                    exitosos = 0
                    reintentos = 0
                    while reintentos < 5:
                        try:
                            exitosos = await self.procesar_lote_chunks(lote_actual)
                            break
                        except Exception as e:
                            reintentos += 1
                            print(f"❌ Error en lote (intento {reintentos}/5): {e}")
                            import asyncio
                            await asyncio.sleep(2 ** reintentos)
                    actualizados += exitosos
                    if exitosos < len(lote_actual):
                        errores += (len(lote_actual) - exitosos)
                    lote_actual = []
                    porcentaje = (procesados / total_chunks) * 100 if total_chunks > 0 else 0
                    print(f"{procesados:,} | {actualizados:,} | {errores:,} | {porcentaje:.2f}%")
            # Procesar lote restante
            if lote_actual:
                exitosos = 0
                reintentos = 0
                while reintentos < 5:
                    try:
                        exitosos = await self.procesar_lote_chunks(lote_actual)
                        break
                    except Exception as e:
                        reintentos += 1
                        print(f"❌ Error en lote (intento {reintentos}/5): {e}")
                        import asyncio
                        await asyncio.sleep(2 ** reintentos)
                actualizados += exitosos
                if exitosos < len(lote_actual):
                    errores += (len(lote_actual) - exitosos)
                porcentaje = (procesados / total_chunks) * 100 if total_chunks > 0 else 0
                print(f"{procesados:,} | {actualizados:,} | {errores:,} | {porcentaje:.2f}%")
            print(f"\n🔎 Poblamiento masivo finalizado. Chunks procesados: {procesados:,}, actualizados: {actualizados:,}, errores: {errores:,}")
        except Exception as e:
            print(f"❌ Error general en poblamiento masivo: {e}")




if __name__ == "__main__":
    import sys
    print("\n=== PRUEBA DE OBTENCIÓN DE CHUNKS ===")
    poblador = PobladorChunksRobusto()
    if len(sys.argv) > 1 and sys.argv[1] == "--masivo":
        import asyncio
        asyncio.run(poblador.poblar_chunks_masivo())
    else:
        documentos = poblador.obtener_todos_los_chunks('chunks_semanticos_mel_json')
        import os
        print(f"\nTotal de archivos JSON procesados: {len(os.listdir('chunks_semanticos_mel_json')):,}")
        print(f"Total de chunks detectados: {len(documentos):,}")