#!/usr/bin/env python3
"""
Script para analizar todos los campos únicos presentes en los archivos JSON
de documentos judiciales y generar estructura para PostgreSQL.
"""

import json
import os
from pathlib import Path
from collections import defaultdict
from typing import Dict, Any, Set, List
import sys

def analizar_tipo_valor(valor: Any) -> str:
    """Determina el tipo de dato PostgreSQL más apropiado para un valor."""
    if valor is None:
        return 'TEXT'
    elif isinstance(valor, bool):
        return 'BOOLEAN'
    elif isinstance(valor, int):
        return 'INTEGER'
    elif isinstance(valor, float):
        return 'NUMERIC'
    elif isinstance(valor, str):
        if len(valor) > 1000:
            return 'TEXT'
        else:
            return 'VARCHAR(1000)'
    elif isinstance(valor, dict):
        return 'JSONB'
    elif isinstance(valor, list):
        return 'JSONB'
    else:
        return 'TEXT'

def extraer_campos_recursivo(obj: Any, prefijo: str = "") -> Dict[str, Any]:
    """Extrae todos los campos de un objeto JSON de forma recursiva."""
    campos = {}
    
    if isinstance(obj, dict):
        for clave, valor in obj.items():
            nombre_campo = f"{prefijo}.{clave}" if prefijo else clave
            
            if isinstance(valor, dict):
                # Si es un diccionario, extraer campos recursivamente
                campos.update(extraer_campos_recursivo(valor, nombre_campo))
            elif isinstance(valor, list) and valor and isinstance(valor[0], dict):
                # Si es una lista de diccionarios, analizar el primer elemento
                campos.update(extraer_campos_recursivo(valor[0], f"{nombre_campo}[0]"))
            else:
                # Campo simple
                campos[nombre_campo] = valor
    
    return campos

def analizar_directorio_json(directorio: Path) -> Dict[str, Dict[str, Any]]:
    """Analiza todos los archivos JSON en un directorio."""
    print(f"Analizando archivos JSON en: {directorio}")
    
    campos_encontrados = defaultdict(lambda: {
        'tipos': set(),
        'ejemplos': [],
        'frecuencia': 0,
        'longitudes_max': []
    })
    
    archivos_procesados = 0
    errores = 0
    
    for archivo_json in directorio.glob("*.json"):
        try:
            with open(archivo_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extraer todos los campos
            campos = extraer_campos_recursivo(data)
            
            for campo, valor in campos.items():
                info = campos_encontrados[campo]
                info['frecuencia'] += 1
                info['tipos'].add(analizar_tipo_valor(valor))
                
                # Guardar ejemplos (máximo 3)
                if len(info['ejemplos']) < 3:
                    info['ejemplos'].append(str(valor)[:100] if valor is not None else None)
                
                # Guardar longitud si es string
                if isinstance(valor, str):
                    info['longitudes_max'].append(len(valor))
            
            archivos_procesados += 1
            
            # Mostrar progreso cada 1000 archivos
            if archivos_procesados % 1000 == 0:
                print(f"Procesados {archivos_procesados} archivos...")
                
        except Exception as e:
            errores += 1
            if errores <= 10:  # Solo mostrar primeros 10 errores
                print(f"Error procesando {archivo_json}: {e}")
    
    print(f"Análisis completado:")
    print(f"- Archivos procesados: {archivos_procesados}")
    print(f"- Errores: {errores}")
    print(f"- Campos únicos encontrados: {len(campos_encontrados)}")
    
    return dict(campos_encontrados)

def generar_reporte_campos(campos: Dict[str, Dict[str, Any]]) -> str:
    """Genera un reporte detallado de los campos encontrados."""
    reporte = []
    reporte.append("=" * 80)
    reporte.append("REPORTE DE ANÁLISIS DE CAMPOS JSON")
    reporte.append("=" * 80)
    reporte.append("")
    
    # Ordenar campos por frecuencia (descendente)
    campos_ordenados = sorted(campos.items(), 
                             key=lambda x: x[1]['frecuencia'], 
                             reverse=True)
    
    for campo, info in campos_ordenados:
        reporte.append(f"CAMPO: {campo}")
        reporte.append(f"  Frecuencia: {info['frecuencia']}")
        reporte.append(f"  Tipos detectados: {', '.join(info['tipos'])}")
        
        if info['longitudes_max']:
            max_len = max(info['longitudes_max'])
            promedio_len = sum(info['longitudes_max']) // len(info['longitudes_max'])
            reporte.append(f"  Longitud máxima: {max_len}, Promedio: {promedio_len}")
        
        reporte.append(f"  Ejemplos:")
        for i, ejemplo in enumerate(info['ejemplos'], 1):
            reporte.append(f"    {i}. {ejemplo}")
        
        reporte.append("")
    
    return "\n".join(reporte)

def generar_tipo_postgresql(info: Dict[str, Any]) -> str:
    """Determina el mejor tipo PostgreSQL para un campo basado en su análisis."""
    tipos = info['tipos']
    
    # Si hay múltiples tipos, usar JSONB o TEXT
    if len(tipos) > 1:
        if 'JSONB' in tipos:
            return 'JSONB'
        else:
            return 'TEXT'
    
    tipo_unico = next(iter(tipos))
    
    # Ajustar VARCHAR basado en longitudes
    if tipo_unico.startswith('VARCHAR') and info['longitudes_max']:
        max_len = max(info['longitudes_max'])
        if max_len > 500:
            return 'TEXT'
        elif max_len > 255:
            return 'VARCHAR(1000)'
        else:
            return 'VARCHAR(255)'
    
    return tipo_unico

def main():
    """Función principal."""
    if len(sys.argv) > 1:
        directorio = Path(sys.argv[1])
    else:
        directorio = Path("/home/lab4/scripts/documentos_judiciales/json_files")
    
    if not directorio.exists():
        print(f"Error: El directorio {directorio} no existe.")
        sys.exit(1)
    
    # Analizar campos
    campos = analizar_directorio_json(directorio)
    
    # Generar reporte
    reporte = generar_reporte_campos(campos)
    
    # Guardar reporte
    archivo_reporte = Path("analisis_campos_json.txt")
    with open(archivo_reporte, 'w', encoding='utf-8') as f:
        f.write(reporte)
    
    print(f"\nReporte guardado en: {archivo_reporte}")
    
    # Generar esquema PostgreSQL básico
    esquema = []
    esquema.append("-- Schema PostgreSQL generado automáticamente")
    esquema.append("-- Tabla principal para documentos judiciales")
    esquema.append("")
    esquema.append("CREATE TABLE IF NOT EXISTS documentos_judiciales (")
    esquema.append("    id SERIAL PRIMARY KEY,")
    esquema.append("    archivo_json VARCHAR(255) NOT NULL,")
    esquema.append("    fecha_insercion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,")
    
    # Campos más comunes primero
    campos_ordenados = sorted(campos.items(), 
                             key=lambda x: x[1]['frecuencia'], 
                             reverse=True)
    
    for campo, info in campos_ordenados:
        if campo and not campo.startswith('.') and '.' not in campo:
            tipo_pg = generar_tipo_postgresql(info)
            # Limpiar nombre del campo para PostgreSQL
            nombre_limpio = campo.lower().replace(' ', '_').replace('-', '_')
            nombre_limpio = ''.join(c for c in nombre_limpio if c.isalnum() or c == '_')
            
            # Determinar si debe ser NULL o NOT NULL
            null_constraint = "NULL" if info['frecuencia'] < len(campos) * 0.8 else "NOT NULL"
            
            esquema.append(f"    {nombre_limpio} {tipo_pg} {null_constraint},")
    
    # Remover última coma y cerrar
    if esquema[-1].endswith(','):
        esquema[-1] = esquema[-1][:-1]
    
    esquema.append(");")
    esquema.append("")
    esquema.append("-- Índices recomendados")
    esquema.append("CREATE INDEX IF NOT EXISTS idx_documentos_archivo ON documentos_judiciales(archivo);")
    esquema.append("CREATE INDEX IF NOT EXISTS idx_documentos_nuc ON documentos_judiciales(nuc);")
    esquema.append("CREATE INDEX IF NOT EXISTS idx_documentos_procesado ON documentos_judiciales(procesado);")
    
    # Guardar esquema
    archivo_esquema = Path("schema_postgresql.sql")
    with open(archivo_esquema, 'w', encoding='utf-8') as f:
        f.write('\n'.join(esquema))
    
    print(f"Esquema PostgreSQL guardado en: {archivo_esquema}")
    
    # Mostrar resumen
    print(f"\nRESUMEN:")
    print(f"Campos únicos analizados: {len(campos)}")
    print(f"Top 10 campos más frecuentes:")
    for i, (campo, info) in enumerate(campos_ordenados[:10], 1):
        print(f"  {i}. {campo} ({info['frecuencia']} ocurrencias)")

if __name__ == "__main__":
    main()