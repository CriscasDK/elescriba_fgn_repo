#!/usr/bin/env python3
"""
Script para verificar el poblamiento completo de la base de datos
comparando con los archivos JSON disponibles.
"""

import json
import psycopg2
from pathlib import Path
import sys
from collections import defaultdict
from typing import Dict, Set, List, Any

# Configuración de la base de datos
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'documentos_juridicos',
    'user': 'docs_user',
    'password': 'docs_password_2025'
}

def conectar_db():
    """Conecta a la base de datos PostgreSQL."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Error conectando a la base de datos: {e}")
        sys.exit(1)

def obtener_archivos_json(directorio: Path) -> Set[str]:
    """Obtiene la lista de archivos JSON disponibles."""
    archivos = set()
    for archivo in directorio.glob("*.json"):
        archivos.add(archivo.stem.replace('_batch_resultado_20250619_', '_').replace('_batch_resultado_20250618_', '_'))
    return archivos

def obtener_archivos_db() -> Set[str]:
    """Obtiene la lista de archivos ya procesados en la base de datos."""
    conn = conectar_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT archivo FROM documentos")
        resultados = cursor.fetchall()
        archivos_db = {resultado[0].replace('.pdf', '') for resultado in resultados}
        return archivos_db
    finally:
        cursor.close()
        conn.close()

def obtener_estructura_tabla() -> Dict[str, str]:
    """Obtiene la estructura actual de la tabla documentos."""
    conn = conectar_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'documentos' 
            ORDER BY ordinal_position
        """)
        
        columnas = {}
        for row in cursor.fetchall():
            columnas[row[0]] = {
                'tipo': row[1],
                'nullable': row[2] == 'YES'
            }
        return columnas
    finally:
        cursor.close()
        conn.close()

def analizar_campos_json(directorio: Path, muestra: int = 100) -> Dict[str, Any]:
    """Analiza una muestra de archivos JSON para identificar campos."""
    archivos_json = list(directorio.glob("*.json"))
    muestra_archivos = archivos_json[:muestra] if len(archivos_json) > muestra else archivos_json
    
    campos_json = defaultdict(lambda: {
        'frecuencia': 0,
        'tipos': set(),
        'ejemplos': []
    })
    
    for archivo in muestra_archivos:
        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Analizar campos principales
            for campo, valor in data.items():
                if campo == 'metadatos' and isinstance(valor, dict):
                    # Analizar subcampos de metadatos
                    for subcampo, subvalor in valor.items():
                        campo_completo = f"metadatos.{subcampo}"
                        info = campos_json[campo_completo]
                        info['frecuencia'] += 1
                        info['tipos'].add(type(subvalor).__name__)
                        if len(info['ejemplos']) < 3:
                            info['ejemplos'].append(str(subvalor)[:100])
                elif campo == 'estadisticas' and isinstance(valor, dict):
                    # Analizar subcampos de estadísticas
                    for subcampo, subvalor in valor.items():
                        campo_completo = f"estadisticas.{subcampo}"
                        info = campos_json[campo_completo]
                        info['frecuencia'] += 1
                        info['tipos'].add(type(subvalor).__name__)
                        if len(info['ejemplos']) < 3:
                            info['ejemplos'].append(str(subvalor)[:100])
                else:
                    # Campo principal
                    info = campos_json[campo]
                    info['frecuencia'] += 1
                    info['tipos'].add(type(valor).__name__)
                    if len(info['ejemplos']) < 3:
                        info['ejemplos'].append(str(valor)[:100])
                        
        except Exception as e:
            print(f"Error procesando {archivo}: {e}")
    
    return dict(campos_json)

def generar_mapeo_campos() -> Dict[str, str]:
    """Genera mapeo entre campos JSON y columnas de la tabla."""
    return {
        'archivo': 'archivo',
        'ruta': 'ruta',
        'procesado': 'procesado',
        'estado': 'estado',
        'texto_extraido': 'texto_extraido',
        'analisis': 'analisis',
        'paginas': 'paginas',
        'tamaño_mb': 'tamaño_mb',
        'costo_estimado': 'costo_estimado',
        'metadatos.NUC': 'nuc',
        'metadatos.Cuaderno': 'cuaderno',
        'metadatos.Código': 'codigo',
        'metadatos.Despacho': 'despacho',
        'metadatos.Entidad productora': 'entidad_productora',
        'metadatos.Serie': 'serie',
        'metadatos.Subserie': 'subserie',
        'metadatos.Folio Inicial': 'folio_inicial',
        'metadatos.Folio Final': 'folio_final',
        'metadatos.Hash_SHA256': 'hash_sha256',
    }

def main():
    """Función principal."""
    directorio_json = Path("/home/lab4/scripts/documentos_judiciales/json_files")
    
    print("=" * 80)
    print("VERIFICACIÓN DE POBLAMIENTO DE BASE DE DATOS")
    print("=" * 80)
    
    # 1. Comparar archivos JSON vs DB
    print("\n1. COMPARANDO ARCHIVOS DISPONIBLES VS BASE DE DATOS")
    print("-" * 50)
    
    archivos_json = set()
    for archivo in directorio_json.glob("*.json"):
        nombre_base = archivo.name.replace('.json', '').split('_batch_resultado_')[0]
        archivos_json.add(nombre_base + '.pdf')
    
    archivos_db = obtener_archivos_db()
    
    print(f"Archivos JSON disponibles: {len(archivos_json)}")
    print(f"Archivos en base de datos: {len(archivos_db)}")
    
    archivos_faltantes = archivos_json - archivos_db
    print(f"Archivos faltantes en DB: {len(archivos_faltantes)}")
    
    if archivos_faltantes:
        print(f"Ejemplos de archivos faltantes:")
        for i, archivo in enumerate(sorted(archivos_faltantes)[:10]):
            print(f"  {i+1}. {archivo}")
        if len(archivos_faltantes) > 10:
            print(f"  ... y {len(archivos_faltantes) - 10} más")
    
    # 2. Verificar estructura de campos
    print(f"\n2. VERIFICANDO ESTRUCTURA DE CAMPOS")
    print("-" * 50)
    
    estructura_tabla = obtener_estructura_tabla()
    campos_json = analizar_campos_json(directorio_json)
    mapeo_campos = generar_mapeo_campos()
    
    print(f"Columnas en tabla 'documentos': {len(estructura_tabla)}")
    print(f"Campos únicos en JSONs (muestra): {len(campos_json)}")
    
    # Identificar campos JSON que no están mapeados
    campos_no_mapeados = []
    for campo_json in campos_json.keys():
        if campo_json not in mapeo_campos:
            campos_no_mapeados.append(campo_json)
    
    print(f"\nCampos JSON sin mapear a tabla: {len(campos_no_mapeados)}")
    if campos_no_mapeados:
        print("Campos sin mapear:")
        for campo in sorted(campos_no_mapeados)[:10]:
            freq = campos_json[campo]['frecuencia']
            print(f"  - {campo} (frecuencia: {freq})")
        if len(campos_no_mapeados) > 10:
            print(f"  ... y {len(campos_no_mapeados) - 10} más")
    
    # 3. Verificar campos vacíos o nulos
    print(f"\n3. VERIFICANDO COMPLETITUD DE DATOS")
    print("-" * 50)
    
    conn = conectar_db()
    cursor = conn.cursor()
    
    try:
        # Verificar campos con valores nulos o vacíos
        for columna in estructura_tabla.keys():
            if columna in ['id', 'created_at', 'updated_at']:
                continue
                
            cursor.execute(f"""
                SELECT 
                    COUNT(*) as total,
                    COUNT({columna}) as con_datos,
                    COUNT(*) - COUNT({columna}) as nulos,
                    COUNT(CASE WHEN {columna} = '' THEN 1 END) as vacios
                FROM documentos
            """)
            
            result = cursor.fetchone()
            total, con_datos, nulos, vacios = result
            
            porcentaje_completo = (con_datos / total * 100) if total > 0 else 0
            
            if nulos > 0 or vacios > 0 or porcentaje_completo < 95:
                print(f"  {columna:20} -> {con_datos:4}/{total} ({porcentaje_completo:5.1f}%) | Nulos: {nulos} | Vacíos: {vacios}")
    
    finally:
        cursor.close()
        conn.close()
    
    # 4. Generar recomendaciones
    print(f"\n4. RECOMENDACIONES")
    print("-" * 50)
    
    if archivos_faltantes:
        print(f"• POBLACIÓN INCOMPLETA: Faltan {len(archivos_faltantes)} archivos por procesar")
        print("  Ejecutar script de poblamiento masivo")
    
    if campos_no_mapeados:
        print(f"• CAMPOS FALTANTES: {len(campos_no_mapeados)} campos JSON no están en la tabla")
        print("  Considerar agregar columnas o crear tablas relacionadas")
    
    print(f"• Revisar campos con baja completitud de datos")
    print(f"• Considerar índices para optimizar consultas")
    
    print(f"\n{'='*80}")
    print("VERIFICACIÓN COMPLETADA")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()