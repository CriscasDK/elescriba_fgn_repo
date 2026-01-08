
import json
import os
import psycopg2
import pandas as pd
from datetime import datetime
import re

def conectar():
    return psycopg2.connect(
        host="localhost",
        database="documentos_judiciales",
        user="admin_docs",
        password="admin_docs2024",
        port="5432"
    )

def fix_encoding_correcto(text):
    if not text or text.strip() == "":
        return ""

    # Manejar casos None
    if text is None:
        return ""

    # Convertir a string si no lo es
    text = str(text).strip()

    # Casos específicos observados
    replacements = {
        'Ã±': 'ñ',
        'Ã³': 'ó',
        'Ã¡': 'á',
        'Ã©': 'é',
        'Ã­': 'í',
        'Ãº': 'ú',
        'Ã': 'Ñ',
        'Ã"': 'Ó',
        'Ã\x81': 'Á',
        'Ã\x89': 'É',
        'Ã\x8d': 'Í',
        'Ãš': 'Ú',
        'Ã¼': 'ü',
        'Ã\x9c': 'Ü'
    }

    for wrong, correct in replacements.items():
        text = text.replace(wrong, correct)

    return text

def main():
    print("🔥 INICIANDO ACTUALIZACIÓN MASIVA CORREGIDA")
    print("=" * 60)

    # Directorio de archivos JSON
    json_dir = '/home/lab4/scripts/documentos_judiciales/json_files/'

    # Obtener todos los archivos JSON
    json_files = [f for f in os.listdir(json_dir) if f.endswith('.json')]
    print(f"📁 Archivos JSON encontrados: {len(json_files)}")

    # Contadores
    actualizados = 0
    errores = 0
    no_encontrados = 0

    inicio = datetime.now()

    with conectar() as conn:
        cur = conn.cursor()

        for i, json_file in enumerate(json_files):
            try:
                # Progreso cada 1000 archivos
                if i % 1000 == 0:
                    elapsed = datetime.now() - inicio
                    print(f"📊 Procesando archivo {i+1}/{len(json_files)} - {elapsed}")

                # Extraer nombre base del JSON
                json_base = json_file.split('_batch_resultado_')[0]
                pdf_name = json_base + '.pdf'

                # Buscar el documento en la BD usando el campo CORRECTO 'archivo'
                cur.execute("SELECT id FROM documentos WHERE archivo = %s", (pdf_name,))
                result = cur.fetchone()

                if not result:
                    no_encontrados += 1
                    continue

                documento_id = result[0]

                # Cargar el JSON
                json_path = os.path.join(json_dir, json_file)
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Extraer metadatos
                if 'metadatos' not in data:
                    continue

                metadatos = data['metadatos']

                # Extraer y limpiar campos
                nuc = fix_encoding_correcto(metadatos.get('NUC', ''))
                serie = fix_encoding_correcto(metadatos.get('Serie', ''))
                detalle = fix_encoding_correcto(metadatos.get('Detalle', ''))
                despacho = fix_encoding_correcto(metadatos.get('Despacho', ''))
                codigo = fix_encoding_correcto(metadatos.get('Código', ''))

                # Actualizar metadatos
                update_query = """
                    UPDATE metadatos 
                    SET nuc = %s, serie = %s, detalle = %s, despacho = %s, codigo = %s
                    WHERE documento_id = %s
                """

                cur.execute(update_query, (nuc, serie, detalle, despacho, codigo, documento_id))

                if cur.rowcount > 0:
                    actualizados += 1

                # Commit cada 100 actualizaciones
                if actualizados % 100 == 0:
                    conn.commit()

            except Exception as e:
                errores += 1
                if errores <= 10:  # Solo mostrar primeros 10 errores
                    print(f"❌ Error en {json_file}: {e}")

        # Commit final
        conn.commit()

    # Estadísticas finales
    fin = datetime.now()
    duracion = fin - inicio

    print(f"\n🏆 ACTUALIZACIÓN MASIVA COMPLETADA")
    print(f"=" * 60)
    print(f"⏱️ Duración total: {duracion}")
    print(f"📁 Archivos procesados: {len(json_files)}")
    print(f"✅ Documentos actualizados: {actualizados}")
    print(f"❌ Errores: {errores}")
    print(f"🔍 No encontrados en BD: {no_encontrados}")
    print(f"📊 Tasa de éxito: {actualizados/len(json_files)*100:.1f}%")

    return actualizados, errores, no_encontrados

if __name__ == "__main__":
    main()
