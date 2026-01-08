#!/usr/bin/env python3
"""
🔍 ANÁLISIS AVANZADO DE CONSULTAS DE VÍCTIMAS
Script para afinar y optimizar las consultas de víctimas con metadatos completos
"""

import psycopg2
from datetime import datetime
import json

def get_db_connection():
    """Configuración de conexión a la base de datos"""
    return {
        'host': 'localhost',
        'port': '5432',
        'database': 'documentos_juridicos_gpt4',
        'user': 'docs_user',
        'password': 'docs_password_2025'
    }

def analisis_tipos_victimas():
    """Analizar todos los tipos de personas en la base de datos"""
    print("\n🔍 ANÁLISIS DE TIPOS DE PERSONAS")
    print("=" * 60)
    
    try:
        db_config = get_db_connection()
        with psycopg2.connect(**db_config) as conn:
            with conn.cursor() as cur:
                # Obtener todos los tipos únicos
                cur.execute("""
                    SELECT 
                        tipo,
                        COUNT(*) as cantidad,
                        COUNT(DISTINCT nombre) as nombres_unicos,
                        COUNT(DISTINCT documento_id) as documentos_unicos
                    FROM personas 
                    GROUP BY tipo 
                    ORDER BY cantidad DESC
                """)
                
                tipos = cur.fetchall()
                
                for tipo, cantidad, nombres, docs in tipos:
                    print(f"📊 {tipo}: {cantidad:,} registros | {nombres:,} nombres únicos | {docs:,} docs")
                
                # Análisis específico de víctimas
                print(f"\n🎯 ANÁLISIS ESPECÍFICO DE VÍCTIMAS")
                print("-" * 40)
                
                cur.execute("""
                    SELECT 
                        tipo,
                        COUNT(*) as cantidad,
                        COUNT(DISTINCT nombre) as nombres_unicos
                    FROM personas 
                    WHERE tipo ILIKE '%victima%'
                    GROUP BY tipo 
                    ORDER BY cantidad DESC
                """)
                
                victimas_tipos = cur.fetchall()
                
                for tipo, cantidad, nombres in victimas_tipos:
                    print(f"✅ {tipo}: {cantidad:,} registros | {nombres:,} nombres únicos")
                
                # Filtro actual del frontend
                print(f"\n🔍 FILTRO ACTUAL DEL FRONTEND:")
                print("   Incluye: tipo ILIKE '%victima%'")
                print("   Excluye: tipo NOT ILIKE '%victimario%'")
                
                cur.execute("""
                    SELECT COUNT(*) as total_registros,
                           COUNT(DISTINCT nombre) as nombres_unicos,
                           COUNT(DISTINCT documento_id) as documentos_unicos
                    FROM personas 
                    WHERE tipo ILIKE '%victima%' 
                      AND tipo NOT ILIKE '%victimario%'
                      AND nombre IS NOT NULL 
                      AND nombre != ''
                """)
                
                total_reg, nombres_unicos, docs_unicos = cur.fetchone()
                print(f"📈 Resultado filtro: {total_reg:,} registros | {nombres_unicos:,} nombres | {docs_unicos:,} docs")
                
    except Exception as e:
        print(f"❌ Error: {e}")

def analisis_metadatos_cobertura():
    """Analizar cobertura de metadatos por campo"""
    print("\n📊 ANÁLISIS DE COBERTURA DE METADATOS")
    print("=" * 60)
    
    try:
        db_config = get_db_connection()
        with psycopg2.connect(**db_config) as conn:
            with conn.cursor() as cur:
                
                # Total de metadatos
                cur.execute("SELECT COUNT(*) FROM metadatos")
                total_metadatos = cur.fetchone()[0]
                print(f"📋 Total registros metadatos: {total_metadatos:,}")
                
                # Análisis por campo
                campos_metadatos = [
                    'nuc', 'serie', 'detalle', 'cuaderno', 'codigo', 'despacho',
                    'entidad_productora', 'subserie', 'observaciones', 'soporte',
                    'idioma', 'descriptores', 'anexos'
                ]
                
                print(f"\n🔍 COBERTURA POR CAMPO:")
                print("-" * 40)
                
                for campo in campos_metadatos:
                    cur.execute(f"""
                        SELECT COUNT(*) 
                        FROM metadatos 
                        WHERE {campo} IS NOT NULL 
                          AND {campo} != ''
                    """)
                    
                    poblado = cur.fetchone()[0]
                    porcentaje = (poblado / total_metadatos * 100) if total_metadatos > 0 else 0
                    
                    print(f"   {campo:20}: {poblado:6,} ({porcentaje:5.1f}%)")
                
    except Exception as e:
        print(f"❌ Error: {e}")

def consulta_victimas_optimizada(limite=5, offset=0, nuc_filtro=None, mostrar_detalles=True):
    """Consulta optimizada de víctimas con análisis detallado"""
    print(f"\n🎯 CONSULTA OPTIMIZADA DE VÍCTIMAS")
    print("=" * 60)
    
    try:
        db_config = get_db_connection()
        with psycopg2.connect(**db_config) as conn:
            with conn.cursor() as cur:
                
                # Construir filtros
                where_conditions = [
                    "p.tipo ILIKE %s", 
                    "p.tipo NOT ILIKE %s", 
                    "p.nombre IS NOT NULL", 
                    "p.nombre != ''"
                ]
                params = ['%victima%', '%victimario%']
                
                if nuc_filtro and nuc_filtro.strip():
                    where_conditions.append("m.nuc = %s")
                    params.append(nuc_filtro.strip())
                    print(f"🔍 Filtro NUC aplicado: {nuc_filtro}")
                
                where_clause = " AND ".join(where_conditions)
                
                # Consulta principal mejorada
                query = f"""
                    SELECT 
                        -- Información básica de persona
                        p.id as persona_id,
                        p.nombre,
                        p.tipo,
                        p.detalles as persona_detalles,
                        
                        -- Información de documento
                        d.id as doc_id,
                        d.archivo,
                        d.ruta_completa,
                        d.created_at as doc_fecha_creacion,
                        
                        -- Análisis y contenido
                        LENGTH(COALESCE(d.analisis, '')) as len_analisis,
                        LENGTH(COALESCE(d.texto_extraido, '')) as len_texto,
                        LEFT(COALESCE(d.analisis, ''), 200) as preview_analisis,
                        
                        -- Metadatos documentales básicos
                        COALESCE(NULLIF(m.nuc, ''), 'N/A') as nuc,
                        COALESCE(NULLIF(m.serie, ''), 'N/A') as serie,
                        COALESCE(NULLIF(m.subserie, ''), 'N/A') as subserie,
                        COALESCE(NULLIF(m.detalle, ''), 'N/A') as detalle,
                        COALESCE(NULLIF(m.cuaderno, ''), 'N/A') as cuaderno,
                        COALESCE(NULLIF(m.codigo, ''), 'N/A') as codigo,
                        COALESCE(NULLIF(m.despacho, ''), 'N/A') as despacho,
                        
                        -- Metadatos adicionales
                        COALESCE(NULLIF(m.entidad_productora, ''), 'N/A') as entidad_productora,
                        COALESCE(NULLIF(m.observaciones, ''), 'N/A') as observaciones,
                        COALESCE(NULLIF(m.soporte, ''), 'N/A') as soporte,
                        COALESCE(NULLIF(m.idioma, ''), 'N/A') as idioma,
                        COALESCE(NULLIF(m.descriptores, ''), 'N/A') as descriptores,
                        
                        -- Metadatos técnicos
                        m.folio_inicial,
                        m.folio_final,
                        m.hash_sha256,
                        m.fecha_inicio,
                        m.fecha_fin,
                        m.timestamp_batch,
                        
                        -- Indicadores de calidad
                        CASE WHEN m.id IS NOT NULL THEN 'SÍ' ELSE 'NO' END as tiene_metadatos,
                        CASE WHEN d.analisis IS NOT NULL AND d.analisis != '' THEN 'SÍ' ELSE 'NO' END as tiene_analisis,
                        CASE WHEN d.texto_extraido IS NOT NULL AND d.texto_extraido != '' THEN 'SÍ' ELSE 'NO' END as tiene_texto
                        
                    FROM personas p
                    JOIN documentos d ON p.documento_id = d.id
                    LEFT JOIN metadatos m ON d.id = m.documento_id
                    WHERE {where_clause}
                    ORDER BY p.nombre, d.id
                    LIMIT %s OFFSET %s
                """
                
                print(f"🔍 Parámetros: {params + [limite, offset]}")
                
                cur.execute(query, params + [limite, offset])
                resultados = cur.fetchall()
                
                print(f"✅ Registros obtenidos: {len(resultados)}")
                
                # Obtener total para paginación
                cur.execute(f"""
                    SELECT COUNT(*)
                    FROM personas p
                    JOIN documentos d ON p.documento_id = d.id
                    LEFT JOIN metadatos m ON d.id = m.documento_id
                    WHERE {where_clause}
                """, params)
                
                total = cur.fetchone()[0]
                print(f"📊 Total disponible: {total:,}")
                
                if not mostrar_detalles:
                    return resultados, total
                
                # Mostrar resultados detallados
                print("\n" + "=" * 80)
                
                for i, row in enumerate(resultados, 1):
                    print(f"\n🔍 VÍCTIMA #{i}")
                    print("-" * 40)
                    
                    # Información básica
                    print(f"👤 Nombre: {row[1]}")
                    print(f"🏷️  Tipo: {row[2]}")
                    print(f"📄 ID Persona: {row[0]} | Doc ID: {row[4]}")
                    if row[3] and row[3] != 'N/A':
                        print(f"📝 Detalles: {row[3][:100]}...")
                    
                    # Archivo y fecha
                    print(f"\n📂 ARCHIVO:")
                    print(f"   📄 Nombre: {row[5]}")
                    print(f"   📁 Ruta: {row[6][:80]}..." if len(str(row[6])) > 80 else f"   📁 Ruta: {row[6]}")
                    print(f"   📅 Creado: {row[7]}")
                    
                    # Contenido y análisis
                    print(f"\n📊 CONTENIDO:")
                    print(f"   📝 Análisis: {row[8]:,} chars | {row[29]}")
                    print(f"   📄 Texto: {row[9]:,} chars | {row[30]}")
                    if row[10] and len(row[10]) > 10:
                        print(f"   🔍 Preview: {row[10]}...")
                    
                    # Metadatos principales
                    print(f"\n📋 METADATOS ({row[28]}):")
                    print(f"   🆔 NUC: {row[11]}")
                    print(f"   📊 Serie: {row[12]} | Subserie: {row[13]}")
                    print(f"   📝 Detalle: {row[14][:60]}..." if len(str(row[14])) > 60 else f"   📝 Detalle: {row[14]}")
                    print(f"   📚 Cuaderno: {row[15]} | Código: {row[16]}")
                    print(f"   🏢 Despacho: {row[17]}")
                    
                    # Metadatos adicionales (solo si no son N/A)
                    if row[18] != 'N/A':
                        print(f"   🏛️  Entidad: {row[18][:50]}...")
                    if row[20] != 'N/A':
                        print(f"   💾 Soporte: {row[20]}")
                    if row[21] != 'N/A':
                        print(f"   🌐 Idioma: {row[21]}")
                    if row[22] != 'N/A':
                        print(f"   🔖 Descriptores: {row[22][:50]}...")
                    
                    # Información temporal
                    if row[25] or row[26]:
                        print(f"   📅 Período: {row[25] or 'N/A'} → {row[26] or 'N/A'}")
                    
                    print("-" * 80)
                
                return resultados, total
                
    except Exception as e:
        print(f"❌ Error en consulta: {e}")
        import traceback
        traceback.print_exc()
        return [], 0

def casos_prueba_especificos():
    """Ejecutar casos de prueba específicos"""
    print("\n🧪 CASOS DE PRUEBA ESPECÍFICOS")
    print("=" * 60)
    
    # Caso 1: NUC específico conocido
    print("\n🎯 CASO 1: NUC específico con metadatos")
    nuc_test = "11001606606419900000186"
    resultados, total = consulta_victimas_optimizada(limite=3, nuc_filtro=nuc_test, mostrar_detalles=False)
    print(f"   Resultado: {len(resultados)} registros de {total} total")
    
    # Caso 2: Muestra general sin filtro
    print("\n🎯 CASO 2: Muestra general (primeros 3)")
    resultados, total = consulta_victimas_optimizada(limite=3, mostrar_detalles=False)
    print(f"   Resultado: {len(resultados)} registros de {total:,} total")
    
    # Caso 3: Víctimas con análisis más largo
    print("\n🎯 CASO 3: Víctimas con análisis extenso")
    try:
        db_config = get_db_connection()
        with psycopg2.connect(**db_config) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT p.nombre, LENGTH(d.analisis) as len_analisis
                    FROM personas p
                    JOIN documentos d ON p.documento_id = d.id
                    WHERE p.tipo ILIKE '%victima%' 
                      AND p.tipo NOT ILIKE '%victimario%'
                      AND d.analisis IS NOT NULL 
                      AND LENGTH(d.analisis) > 1000
                    ORDER BY LENGTH(d.analisis) DESC
                    LIMIT 3
                """)
                
                analisis_extensos = cur.fetchall()
                for nombre, longitud in analisis_extensos:
                    print(f"   📝 {nombre}: {longitud:,} chars")
                    
    except Exception as e:
        print(f"   ❌ Error: {e}")

def main():
    """Función principal"""
    print("🚀 ANÁLISIS AVANZADO DE CONSULTAS DE VÍCTIMAS")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # 1. Análisis de tipos
    analisis_tipos_victimas()
    
    # 2. Análisis de metadatos
    analisis_metadatos_cobertura()
    
    # 3. Casos de prueba
    casos_prueba_especificos()
    
    # 4. Consulta detallada
    print("\n🎯 CONSULTA DETALLADA - PRIMERAS 2 VÍCTIMAS")
    print("=" * 60)
    consulta_victimas_optimizada(limite=2, mostrar_detalles=True)
    
    print("\n✅ ANÁLISIS COMPLETADO")
    print("=" * 80)

if __name__ == "__main__":
    main()
