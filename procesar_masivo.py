#!/usr/bin/env python3
"""PROCESADOR MASIVO - Para los 11,000 JSONs"""

import glob
import sys
import os
import time
from extractor_mejorado import process_json_mejorado, DB_CONFIG
import ollama
import psycopg2

def process_batch(json_directory, limite=None):
    """Procesar lote de JSONs"""
    
    # Buscar archivos JSON
    pattern = os.path.join(json_directory, "*.json")
    json_files = glob.glob(pattern)
    
    if not json_files:
        print(f"❌ No se encontraron archivos JSON en: {json_directory}")
        return
    
    # Aplicar límite si se especifica
    if limite:
        json_files = json_files[:limite]
    
    print(f"📂 Encontrados {len(json_files)} archivos JSON para procesar")
    print(f"📁 Directorio: {json_directory}")
    
    # Configurar modelo
    try:
        models_response = ollama.list()
        available_models = [model.model for model in models_response.models]
        deepseek_models = [m for m in available_models if 'deepseek' in m.lower()]
        modelo = deepseek_models[0]
        print(f"🤖 Usando modelo: {modelo}")
    except Exception as e:
        print(f"❌ Error configurando modelo: {e}")
        return
    
    # Estadísticas
    successful = 0
    failed = 0
    start_time = time.time()
    
    print(f"\n🚀 INICIANDO PROCESAMIENTO MASIVO...")
    print("="*70)
    
    for i, json_file in enumerate(json_files, 1):
        archivo_nombre = os.path.basename(json_file)
        print(f"\n📄 [{i:4d}/{len(json_files)}] {archivo_nombre}")
        
        try:
            success = process_json_mejorado(json_file, modelo)
            if success:
                successful += 1
                print(f"   ✅ Completado")
            else:
                failed += 1
                print(f"   ❌ Falló")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            failed += 1
        
        # Mostrar progreso cada 25 archivos
        if i % 25 == 0:
            elapsed = time.time() - start_time
            rate = i / elapsed * 60  # archivos por minuto
            remaining = (len(json_files) - i) / rate if rate > 0 else 0
            
            print(f"\n📊 PROGRESO INTERMEDIO:")
            print(f"   ✅ Exitosos: {successful}")
            print(f"   ❌ Fallidos: {failed}")
            print(f"   📈 Velocidad: {rate:.1f} archivos/min")
            print(f"   ⏱️ Tiempo restante estimado: {remaining:.1f} min")
            print(f"   ⏰ Tiempo transcurrido: {elapsed/60:.1f} min")
            
            # Mostrar estadísticas de BD
            try:
                conn = psycopg2.connect(**DB_CONFIG)
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(*) FROM documentos")
                docs = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM personas")
                personas = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM organizaciones")
                orgs = cursor.fetchone()[0]
                
                print(f"   💾 BD: {docs} docs, {personas} personas, {orgs} orgs")
                conn.close()
                
            except Exception as e:
                print(f"   ⚠️ Error consultando BD: {e}")
    
    # Estadísticas finales
    elapsed_total = time.time() - start_time
    
    print(f"\n🏁 PROCESAMIENTO MASIVO COMPLETADO")
    print("="*70)
    print(f"✅ Archivos exitosos: {successful}")
    print(f"❌ Archivos fallidos: {failed}")
    print(f"📊 Total procesados: {successful + failed}")
    print(f"🎯 Tasa de éxito: {(successful/(successful+failed)*100):.1f}%")
    print(f"⏰ Tiempo total: {elapsed_total/60:.1f} minutos")
    print(f"📈 Velocidad promedio: {(successful+failed)/(elapsed_total/60):.1f} archivos/min")
    
    # Estadísticas finales de BD
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM documentos")
        docs = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM personas")
        personas = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM organizaciones")
        orgs = cursor.fetchone()[0]
        
        print(f"\n💾 ESTADÍSTICAS FINALES DE BASE DE DATOS:")
        print(f"   📄 Documentos: {docs:,}")
        print(f"   👥 Personas: {personas:,}")
        print(f"   🏢 Organizaciones: {orgs:,}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error en estadísticas finales: {e}")

def main():
    """Función principal"""
    if len(sys.argv) < 2:
        print("📋 USO:")
        print("   python procesar_masivo.py /ruta/a/json/")
        print("   python procesar_masivo.py /ruta/a/json/ 100  # Procesar solo 100 archivos")
        return
    
    json_directory = sys.argv[1]
    limite = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    if not os.path.exists(json_directory):
        print(f"❌ Directorio no existe: {json_directory}")
        return
    
    print(f"🚀 PROCESADOR MASIVO DE DOCUMENTOS JURÍDICOS")
    print(f"📁 Directorio: {json_directory}")
    if limite:
        print(f"🔢 Límite: {limite} archivos")
    
    # Confirmar antes de procesar
    if not limite or limite > 10:
        confirm = input("\n¿Continuar con el procesamiento masivo? (s/N): ")
        if confirm.lower() not in ['s', 'si', 'y', 'yes']:
            print("❌ Procesamiento cancelado")
            return
    
    process_batch(json_directory, limite)

if __name__ == "__main__":
    main()
