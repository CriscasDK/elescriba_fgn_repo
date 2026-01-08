#!/usr/bin/env python3
"""
🔍 AUDITORÍA COMPLETA: VERIFICAR QUE TODOS LOS CAMPOS DE TODOS LOS JSONs
ESTÉN REFLEJADOS EN LA BASE DE DATOS

Premisa: Cada campo de cada JSON debe estar poblado en las tablas correspondientes
"""

import json
import os
import psycopg2
from pathlib import Path
import sys

def get_db_connection():
    """Configuración de conexión a la base de datos"""
    return {
        'host': 'localhost',
        'port': '5432',
        'database': 'documentos_juridicos_gpt4',
        'user': 'docs_user',
        'password': 'docs_password_2025'
    }

def obtener_estructura_json_completa(json_dir="json_files"):
    """Analizar TODOS los JSONs y extraer TODOS los campos únicos"""
    
    print("🔍 ANALIZANDO ESTRUCTURA DE TODOS LOS JSONs...")
    print("=" * 70)
    
    campos_encontrados = {
        'raiz': set(),
        'metadatos': set(),
        'personas_tipos': set(),
        'otros_campos': set()
    }
    
    archivos_json = []
    json_path = Path(json_dir)
    
    if not json_path.exists():
        print(f"❌ Directorio {json_dir} no existe")
        return None
    
    # Obtener todos los archivos JSON
    for archivo in json_path.glob("*.json"):
        archivos_json.append(archivo)
    
    print(f"📁 Archivos JSON encontrados: {len(archivos_json)}")
    
    # Analizar cada JSON
    for i, archivo_json in enumerate(archivos_json):
        if i % 100 == 0:
            print(f"   Procesando archivo {i+1}/{len(archivos_json)}: {archivo_json.name}")
        
        try:
            with open(archivo_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Campos de nivel raíz
            for campo in data.keys():
                campos_encontrados['raiz'].add(campo)
            
            # Analizar metadatos si existe
            if 'metadatos' in data and isinstance(data['metadatos'], dict):
                for campo_meta in data['metadatos'].keys():
                    campos_encontrados['metadatos'].add(campo_meta)
            
            # Analizar personas por tipo si existe
            if 'personas' in data and isinstance(data['personas'], dict):
                for tipo_persona in data['personas'].keys():
                    campos_encontrados['personas_tipos'].add(tipo_persona)
            
            # Buscar otros campos anidados
            for key, value in data.items():
                if isinstance(value, dict) and key not in ['metadatos', 'personas']:
                    campos_encontrados['otros_campos'].add(key)
        
        except Exception as e:
            print(f"⚠️ Error procesando {archivo_json}: {e}")
    
    return campos_encontrados

def verificar_tablas_bd():
    """Verificar qué tablas y columnas existen en la BD"""
    
    try:
        db_config = get_db_connection()
        
        with psycopg2.connect(**db_config) as conn:
            with conn.cursor() as cur:
                print("\n📊 ESTRUCTURA ACTUAL DE LA BASE DE DATOS")
                print("=" * 70)
                
                # Obtener todas las tablas
                cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    ORDER BY table_name
                """)
                tablas = cur.fetchall()
                
                estructura_bd = {}
                
                for (tabla,) in tablas:
                    print(f"\n🗃️  TABLA: {tabla}")
                    
                    # Obtener columnas de cada tabla
                    cur.execute("""
                        SELECT column_name, data_type, is_nullable
                        FROM information_schema.columns 
                        WHERE table_name = %s 
                        ORDER BY ordinal_position
                    """, (tabla,))
                    
                    columnas = cur.fetchall()
                    estructura_bd[tabla] = columnas
                    
                    for columna, tipo, nullable in columnas:
                        null_text = "NULL" if nullable == "YES" else "NOT NULL"
                        print(f"   📋 {columna} ({tipo}) {null_text}")
                
                return estructura_bd
                
    except Exception as e:
        print(f"❌ Error conectando a BD: {e}")
        return None

def verificar_poblacion_campos(campos_json, estructura_bd):
    """Verificar que todos los campos JSON estén poblados en BD"""
    
    print("\n🔍 VERIFICACIÓN DE POBLAMIENTO CAMPO POR CAMPO")
    print("=" * 70)
    
    try:
        db_config = get_db_connection()
        
        with psycopg2.connect(**db_config) as conn:
            with conn.cursor() as cur:
                
                print("\n1️⃣ VERIFICANDO METADATOS:")
                print("-" * 40)
                
                # Verificar campos de metadatos
                if 'metadatos' in estructura_bd:
                    campos_metadatos_bd = [col[0] for col in estructura_bd['metadatos']]
                    
                    for campo_json in sorted(campos_json['metadatos']):
                        if campo_json in campos_metadatos_bd:
                            # Verificar si está poblado
                            cur.execute(f"""
                                SELECT 
                                    COUNT(*) as total,
                                    COUNT(CASE WHEN {campo_json} IS NOT NULL AND {campo_json} != '' THEN 1 END) as poblado
                                FROM metadatos
                            """)
                            total, poblado = cur.fetchone()
                            porcentaje = (poblado / total * 100) if total > 0 else 0
                            status = "✅" if poblado > 0 else "❌"
                            print(f"   {status} {campo_json}: {poblado:,}/{total:,} ({porcentaje:.1f}%)")
                        else:
                            print(f"   ❌ {campo_json}: NO EXISTE en tabla metadatos")
                
                print("\n2️⃣ VERIFICANDO DOCUMENTOS:")
                print("-" * 40)
                
                # Verificar campos principales en documentos
                if 'documentos' in estructura_bd:
                    campos_docs = ['archivo', 'ruta', 'nuc', 'serie', 'analisis', 'texto_extraido']
                    campos_docs_bd = [col[0] for col in estructura_bd['documentos']]
                    
                    for campo in campos_docs:
                        if campo in campos_docs_bd:
                            cur.execute(f"""
                                SELECT 
                                    COUNT(*) as total,
                                    COUNT(CASE WHEN {campo} IS NOT NULL AND {campo} != '' THEN 1 END) as poblado
                                FROM documentos
                            """)
                            total, poblado = cur.fetchone()
                            porcentaje = (poblado / total * 100) if total > 0 else 0
                            status = "✅" if poblado > 0 else "❌"
                            print(f"   {status} {campo}: {poblado:,}/{total:,} ({porcentaje:.1f}%)")
                
                print("\n3️⃣ VERIFICANDO PERSONAS:")
                print("-" * 40)
                
                # Verificar tipos de personas
                cur.execute("SELECT DISTINCT tipo, COUNT(*) FROM personas GROUP BY tipo ORDER BY COUNT(*) DESC LIMIT 10")
                tipos_bd = cur.fetchall()
                
                print("   Tipos más frecuentes en BD:")
                for tipo, count in tipos_bd:
                    status = "✅" if tipo in campos_json['personas_tipos'] else "⚠️"
                    print(f"   {status} {tipo}: {count:,}")
                
                print("\n4️⃣ RESUMEN DE INTEGRIDAD:")
                print("-" * 40)
                
                # Conteos generales
                cur.execute("SELECT COUNT(*) FROM documentos")
                total_docs = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM metadatos")
                total_metadatos = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM personas")
                total_personas = cur.fetchone()[0]
                
                print(f"   📄 Total documentos: {total_docs:,}")
                print(f"   📋 Total metadatos: {total_metadatos:,}")
                print(f"   👥 Total personas: {total_personas:,}")
                
                cobertura_metadatos = (total_metadatos / total_docs * 100) if total_docs > 0 else 0
                print(f"   📈 Cobertura metadatos: {cobertura_metadatos:.1f}%")
                
    except Exception as e:
        print(f"❌ Error en verificación: {e}")
        import traceback
        traceback.print_exc()

def generar_reporte_faltantes(campos_json, estructura_bd):
    """Generar reporte de campos que faltan"""
    
    print("\n📝 REPORTE DE CAMPOS FALTANTES")
    print("=" * 70)
    
    # Campos de metadatos faltantes
    if 'metadatos' in estructura_bd:
        campos_metadatos_bd = set(col[0] for col in estructura_bd['metadatos'])
        campos_json_metadatos = campos_json['metadatos']
        
        faltantes_metadatos = campos_json_metadatos - campos_metadatos_bd
        sobrantes_metadatos = campos_metadatos_bd - campos_json_metadatos
        
        if faltantes_metadatos:
            print(f"\n❌ CAMPOS METADATOS FALTANTES EN BD ({len(faltantes_metadatos)}):")
            for campo in sorted(faltantes_metadatos):
                print(f"   - {campo}")
        
        if sobrantes_metadatos:
            print(f"\n⚠️ CAMPOS BD QUE NO ESTÁN EN JSONs ({len(sobrantes_metadatos)}):")
            for campo in sorted(sobrantes_metadatos):
                if campo not in ['id', 'documento_id', 'created_at', 'updated_at']:
                    print(f"   - {campo}")

def main():
    """Función principal de auditoría"""
    
    print("🚀 AUDITORÍA COMPLETA DE INTEGRIDAD DE DATOS")
    print("=" * 70)
    print("Verificando que TODOS los campos de TODOS los JSONs estén en BD...")
    print()
    
    # 1. Analizar estructura de JSONs
    campos_json = obtener_estructura_json_completa()
    if not campos_json:
        print("❌ No se pudo analizar estructura de JSONs")
        return
    
    print(f"\n📊 CAMPOS ENCONTRADOS EN JSONs:")
    print(f"   🔑 Campos raíz: {len(campos_json['raiz'])}")
    print(f"   📋 Campos metadatos: {len(campos_json['metadatos'])}")
    print(f"   👥 Tipos personas: {len(campos_json['personas_tipos'])}")
    print(f"   📝 Otros campos: {len(campos_json['otros_campos'])}")
    
    # 2. Verificar estructura de BD
    estructura_bd = verificar_tablas_bd()
    if not estructura_bd:
        print("❌ No se pudo obtener estructura de BD")
        return
    
    # 3. Verificar poblamiento
    verificar_poblacion_campos(campos_json, estructura_bd)
    
    # 4. Generar reporte de faltantes
    generar_reporte_faltantes(campos_json, estructura_bd)
    
    print("\n🎯 AUDITORÍA COMPLETADA")
    print("=" * 70)

if __name__ == "__main__":
    main()
