#!/usr/bin/env python3
"""
🚀 POBLADO COMPLETO DE METADATOS - VERSIÓN SEGURA
Poblar TODOS los metadatos sin tocar análisis/texto_extraído
"""

import os
import json
import psycopg2
from dotenv import load_dotenv
from datetime import datetime
import glob
import time

load_dotenv('.env.gpt41')

def corregir_encoding(texto):
    """Corregir caracteres mal codificados en español"""
    if not texto:
        return texto
    
    # Correcciones más comunes en documentos jurídicos
    correcciones = {
        'Ã¡': 'á', 'Ã©': 'é', 'Ã­': 'í', 'Ã³': 'ó', 'Ãº': 'ú',
        'Ã±': 'ñ', 'Ã§': 'ç', 'Ã¢': 'â', 'Ãª': 'ê', 'Ã®': 'î', 
        'Ã´': 'ô', 'Ã»': 'û', 'Ã¤': 'ä', 'Ã«': 'ë', 'Ã¯': 'ï', 
        'Ã¶': 'ö', 'Ã¼': 'ü'
    }
    
    texto_corregido = texto
    for mal_codificado, correcto in correcciones.items():
        texto_corregido = texto_corregido.replace(mal_codificado, correcto)
    
    return texto_corregido

def parsear_fecha(fecha_str):
    """Convertir fecha del JSON a timestamp"""
    if not fecha_str or fecha_str == "0001-01-01":
        return None
    
    try:
        # Intentar diferentes formatos
        formatos = [
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f"
        ]
        
        for formato in formatos:
            try:
                fecha_clean = fecha_str.split('.')[0] if '.' in fecha_str else fecha_str
                return datetime.strptime(fecha_clean, formato)
            except ValueError:
                continue
        
        return None
    except Exception:
        return None

def get_db_connection():
    """Conexión a base de datos"""
    return {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': os.getenv('POSTGRES_PORT', '5432'),
        'database': os.getenv('POSTGRES_DB', 'documentos_juridicos_gpt4'),
        'user': os.getenv('POSTGRES_USER', 'docs_user'),
        'password': os.getenv('POSTGRES_PASSWORD', 'docs_password_2024')
    }

def mapear_nombre_archivo_a_json(nombre_archivo):
    """Encontrar archivo JSON correspondiente al nombre del archivo"""
    if not nombre_archivo:
        return None
    
    # Extraer nombre base sin extensión
    nombre_base = os.path.splitext(os.path.basename(nombre_archivo))[0]
    
    # Buscar JSON que contenga este nombre
    patrones = [
        f"json_files/*{nombre_base}*.json",
        f"json_files/{nombre_base}*.json",
        f"json_files/*{nombre_base.split('_')[0]}*.json"
    ]
    
    for patron in patrones:
        archivos = glob.glob(patron)
        if archivos:
            return archivos[0]
    
    return None

def poblar_todos_metadatos():
    """Poblar todos los metadatos de forma segura"""
    
    print("🚀 POBLADO COMPLETO DE METADATOS")
    print("=" * 60)
    
    db_config = get_db_connection()
    
    try:
        with psycopg2.connect(**db_config) as conn:
            with conn.cursor() as cur:
                
                # 1. Verificación inicial
                print("🔍 1. VERIFICACIÓN INICIAL:")
                
                cur.execute("SELECT COUNT(*) FROM documentos")
                total_docs = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM personas WHERE tipo ILIKE '%victima%' AND tipo NOT ILIKE '%victimario%'")
                total_victimas = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM metadatos WHERE nuc IS NOT NULL AND nuc != ''")
                metadatos_poblados = cur.fetchone()[0]
                
                print(f"   📄 Total documentos: {total_docs}")
                print(f"   👥 Total víctimas: {total_victimas}")
                print(f"   📋 Metadatos con NUC: {metadatos_poblados}")
                
                # 2. Obtener todos los documentos
                print("📋 2. OBTENIENDO DOCUMENTOS:")
                
                cur.execute("""
                    SELECT d.id, d.ruta, d.archivo, m.id as metadata_id
                    FROM documentos d
                    LEFT JOIN metadatos m ON d.id = m.documento_id
                    ORDER BY d.id
                """)
                
                documentos = cur.fetchall()
                print(f"   📊 Documentos a procesar: {len(documentos)}")
                
                # 3. Procesar en lotes
                print("🔄 3. PROCESANDO EN LOTES:")
                
                lote_size = 100
                actualizados = 0
                errores = 0
                sin_json = 0
                
                for i in range(0, len(documentos), lote_size):
                    lote = documentos[i:i+lote_size]
                    print(f"   📦 Procesando lote {i//lote_size + 1}/{(len(documentos)+lote_size-1)//lote_size}")
                    
                    for doc_id, ruta, archivo, metadata_id in lote:
                        try:
                            # Buscar JSON correspondiente
                            json_path = None
                            
                            # Prioridad: archivo, luego ruta
                            if archivo:
                                json_path = mapear_nombre_archivo_a_json(archivo)
                            
                            if not json_path and ruta:
                                json_path = mapear_nombre_archivo_a_json(ruta)
                            
                            if not json_path:
                                sin_json += 1
                                continue
                            
                            # Cargar JSON
                            if not os.path.exists(json_path):
                                sin_json += 1
                                continue
                                
                            with open(json_path, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                            
                            if 'metadatos' not in data:
                                sin_json += 1
                                continue
                                
                            metadatos_json = data['metadatos']
                            
                            # Mapear TODOS los campos con corrección de encoding
                            valores = {
                                'nuc': metadatos_json.get('NUC', ''),
                                'cuaderno': corregir_encoding(metadatos_json.get('Cuaderno', '')),
                                'codigo': str(metadatos_json.get('Código', '')),
                                'despacho': str(metadatos_json.get('Despacho', '')),
                                'detalle': corregir_encoding(metadatos_json.get('Detalle', '')),
                                'entidad_productora': corregir_encoding(metadatos_json.get('Entidad productora', '')),
                                'serie': metadatos_json.get('Serie', ''),
                                'subserie': metadatos_json.get('Subserie', ''),
                                'folio_inicial': int(metadatos_json.get('Folio Inicial', 0)) if metadatos_json.get('Folio Inicial') else 0,
                                'folio_final': int(metadatos_json.get('Folio Final', 0)) if metadatos_json.get('Folio Final') else 0,
                                'fecha_creacion': parsear_fecha(metadatos_json.get('Fecha de creación')),
                                'observaciones': corregir_encoding(metadatos_json.get('Observaciones', '')),
                                'hash_sha256': metadatos_json.get('Hash_SHA256', ''),
                                'firma_digital': metadatos_json.get('Firma_Digital', ''),
                                'timestamp_auth': parsear_fecha(metadatos_json.get('Timestamp')),
                                'equipo_id_auth': metadatos_json.get('Equipo_ID', ''),
                                'producer': metadatos_json.get('Producer', ''),
                                'anexos': corregir_encoding(metadatos_json.get('Anexos', '')),
                                'authentication_info': metadatos_json.get('AuthenticationInfo', {})
                            }
                            
                            # Actualizar o insertar
                            if metadata_id:
                                # Actualizar registro existente
                                cur.execute("""
                                    UPDATE metadatos SET
                                        nuc = %s, cuaderno = %s, codigo = %s, despacho = %s,
                                        detalle = %s, entidad_productora = %s, serie = %s, subserie = %s,
                                        folio_inicial = %s, folio_final = %s, fecha_creacion = %s,
                                        observaciones = %s, hash_sha256 = %s, firma_digital = %s,
                                        timestamp_auth = %s, equipo_id_auth = %s, producer = %s,
                                        anexos = %s, authentication_info = %s
                                    WHERE id = %s
                                """, (
                                    valores['nuc'], valores['cuaderno'], valores['codigo'], valores['despacho'],
                                    valores['detalle'], valores['entidad_productora'], valores['serie'], valores['subserie'],
                                    valores['folio_inicial'], valores['folio_final'], valores['fecha_creacion'],
                                    valores['observaciones'], valores['hash_sha256'], valores['firma_digital'],
                                    valores['timestamp_auth'], valores['equipo_id_auth'], valores['producer'],
                                    valores['anexos'], json.dumps(valores['authentication_info']),
                                    metadata_id
                                ))
                            else:
                                # Insertar nuevo registro
                                cur.execute("""
                                    INSERT INTO metadatos (
                                        documento_id, nuc, cuaderno, codigo, despacho,
                                        detalle, entidad_productora, serie, subserie,
                                        folio_inicial, folio_final, fecha_creacion,
                                        observaciones, hash_sha256, firma_digital,
                                        timestamp_auth, equipo_id_auth, producer,
                                        anexos, authentication_info, created_at
                                    ) VALUES (
                                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
                                    )
                                """, (
                                    doc_id, valores['nuc'], valores['cuaderno'], valores['codigo'], valores['despacho'],
                                    valores['detalle'], valores['entidad_productora'], valores['serie'], valores['subserie'],
                                    valores['folio_inicial'], valores['folio_final'], valores['fecha_creacion'],
                                    valores['observaciones'], valores['hash_sha256'], valores['firma_digital'],
                                    valores['timestamp_auth'], valores['equipo_id_auth'], valores['producer'],
                                    valores['anexos'], json.dumps(valores['authentication_info'])
                                ))
                            
                            actualizados += 1
                            
                        except Exception as e:
                            errores += 1
                            if errores <= 10:  # Solo mostrar primeros 10 errores
                                print(f"     ⚠️ Error doc {doc_id}: {str(e)[:100]}")
                    
                    # Commit por lote
                    conn.commit()
                    print(f"     ✅ Lote completado. Actualizados: {actualizados}, Errores: {errores}")
                    
                    # Pausa pequeña entre lotes
                    time.sleep(0.1)
                
                # 4. Verificación final
                print("📊 4. RESULTADO FINAL:")
                
                cur.execute("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(CASE WHEN nuc IS NOT NULL AND nuc != '' THEN 1 END) as con_nuc,
                        COUNT(CASE WHEN detalle IS NOT NULL AND detalle != '' THEN 1 END) as con_detalle,
                        COUNT(CASE WHEN serie IS NOT NULL AND serie != '' THEN 1 END) as con_serie,
                        COUNT(CASE WHEN fecha_creacion IS NOT NULL THEN 1 END) as con_fecha
                    FROM metadatos
                """)
                
                stats = cur.fetchone()
                print(f"   📄 Total metadatos: {stats[0]}")
                print(f"   🆔 Con NUC: {stats[1]} ({stats[1]/stats[0]*100:.1f}%)")
                print(f"   📝 Con detalle: {stats[2]} ({stats[2]/stats[0]*100:.1f}%)")
                print(f"   📂 Con serie: {stats[3]} ({stats[3]/stats[0]*100:.1f}%)")
                print(f"   📅 Con fecha: {stats[4]} ({stats[4]/stats[0]*100:.1f}%)")
                print(f"   ✅ Actualizados: {actualizados}")
                print(f"   ⚠️ Errores: {errores}")
                print(f"   📄 Sin JSON: {sin_json}")
                
                # 5. Verificar que víctimas siguen intactas
                print("🧪 5. VERIFICACIÓN DE INTEGRIDAD:")
                
                cur.execute("SELECT COUNT(*) FROM personas WHERE tipo ILIKE '%victima%' AND tipo NOT ILIKE '%victimario%'")
                victimas_final = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM documentos WHERE analisis IS NOT NULL")
                analisis_final = cur.fetchone()[0]
                
                print(f"   👥 Víctimas después: {victimas_final}")
                print(f"   📋 Análisis intactos: {analisis_final}")
                
                if victimas_final == total_victimas:
                    print("   ✅ VÍCTIMAS PRESERVADAS CORRECTAMENTE")
                else:
                    print("   ❌ ALERTA: Cambió el número de víctimas")
                
                print("\n🎉 POBLADO COMPLETO FINALIZADO")
                print("💡 Ahora el frontend debe mostrar todos los metadatos")
                
    except Exception as e:
        print(f"❌ Error general: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    respuesta = input("🚀 ¿Proceder con poblado completo de metadatos? (s/N): ")
    if respuesta.lower() == 's':
        poblar_todos_metadatos()
    else:
        print("❌ Operación cancelada")
