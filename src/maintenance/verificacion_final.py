#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Verificación Final del Sistema de Trazabilidad
Sistema de Documentos Judiciales - Verificación Post-Completado

Autor: Sistema ETL Documentos Judiciales
Fecha: Julio 2025
Estado: PROYECTO COMPLETADO ✅
"""

import psycopg2
import pandas as pd
from datetime import datetime
import sys

def conectar():
    """Función de conexión a PostgreSQL"""
    return psycopg2.connect(
        host='localhost', 
        port='5432', 
        database='documentos_juridicos_gpt4',
        user='docs_user', 
        password='docs_password_2025'
    )

def verificar_trazabilidad():
    """Verificación completa de trazabilidad del sistema"""
    print("🔍 VERIFICACIÓN FINAL DEL SISTEMA DE TRAZABILIDAD")
    print("=" * 60)
    print(f"⏰ Fecha verificación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        with conectar() as conn:
            # 1. Estadísticas generales
            query_stats = """
                SELECT 
                    COUNT(*) as total_metadatos,
                    SUM(CASE WHEN nuc IS NOT NULL AND nuc != '' THEN 1 ELSE 0 END) as con_nuc,
                    SUM(CASE WHEN serie IS NOT NULL AND serie != '' THEN 1 ELSE 0 END) as con_serie,
                    SUM(CASE WHEN detalle IS NOT NULL AND detalle != '' THEN 1 ELSE 0 END) as con_detalle
                FROM metadatos
            """
            
            stats = pd.read_sql(query_stats, conn)
            
            total = stats.iloc[0]['total_metadatos']
            con_nuc = stats.iloc[0]['con_nuc']
            con_serie = stats.iloc[0]['con_serie']
            con_detalle = stats.iloc[0]['con_detalle']
            
            trazabilidad_pct = (con_nuc / total * 100) if total > 0 else 0
            
            print("📊 ESTADÍSTICAS GENERALES:")
            print(f"   📋 Total metadatos: {total:,}")
            print(f"   🆔 Con NUC: {con_nuc:,} ({trazabilidad_pct:.1f}%)")
            print(f"   📊 Con Serie: {con_serie:,} ({con_serie/total*100:.1f}%)")
            print(f"   📝 Con Detalle: {con_detalle:,} ({con_detalle/total*100:.1f}%)")
            
            # 2. Verificación de víctimas
            query_victimas = """
                SELECT 
                    COUNT(DISTINCT p.id) as total_victimas,
                    SUM(CASE WHEN m.nuc IS NOT NULL AND m.nuc != '' THEN 1 ELSE 0 END) as victimas_con_nuc
                FROM personas p
                INNER JOIN documentos d ON p.documento_id = d.id
                LEFT JOIN metadatos m ON d.id = m.documento_id
                WHERE p.tipo ILIKE '%victima%' 
                  AND p.tipo NOT ILIKE '%victimario%'
                  AND p.nombre IS NOT NULL 
                  AND p.nombre != ''
            """
            
            victimas_stats = pd.read_sql(query_victimas, conn)
            
            total_victimas = victimas_stats.iloc[0]['total_victimas']
            victimas_nuc = victimas_stats.iloc[0]['victimas_con_nuc']
            victimas_pct = (victimas_nuc / total_victimas * 100) if total_victimas > 0 else 0
            
            print(f"\n👥 ESTADÍSTICAS DE VÍCTIMAS:")
            print(f"   👥 Total víctimas: {total_victimas:,}")
            print(f"   🆔 Con trazabilidad: {victimas_nuc:,} ({victimas_pct:.1f}%)")
            
            # 3. Muestra aleatoria
            query_muestra = """
                SELECT 
                    p.nombre as victima,
                    d.archivo as documento,
                    m.nuc,
                    m.serie
                FROM personas p
                INNER JOIN documentos d ON p.documento_id = d.id
                INNER JOIN metadatos m ON d.id = m.documento_id
                WHERE p.tipo ILIKE '%victima%' 
                  AND p.tipo NOT ILIKE '%victimario%'
                  AND m.nuc IS NOT NULL 
                  AND m.nuc != ''
                ORDER BY RANDOM()
                LIMIT 3
            """
            
            muestra = pd.read_sql(query_muestra, conn)
            
            print(f"\n🔍 MUESTRA ALEATORIA DE VERIFICACIÓN:")
            for i, row in muestra.iterrows():
                print(f"   {i+1}. {row['victima']} → NUC: {row['nuc']}")
            
            # 4. Evaluación final
            print(f"\n🏆 EVALUACIÓN FINAL:")
            
            if trazabilidad_pct >= 99:
                print("✅ SISTEMA OPERATIVO - EXCELENCIA TOTAL")
                print("🎉 Trazabilidad perfecta lograda")
                status = "EXCELENTE"
            elif trazabilidad_pct >= 90:
                print("✅ SISTEMA OPERATIVO - MUY BUENO")
                print("📈 Trazabilidad excelente")
                status = "MUY BUENO"
            elif trazabilidad_pct >= 80:
                print("✅ SISTEMA FUNCIONAL - BUENO")
                print("📈 Trazabilidad buena")
                status = "BUENO"
            else:
                print("⚠️ SISTEMA REQUIERE MEJORAS")
                print("🔧 Trazabilidad insuficiente")
                status = "REQUIERE MEJORAS"
            
            print(f"\n📋 RESUMEN:")
            print(f"   🎯 Estado: {status}")
            print(f"   📊 Trazabilidad: {trazabilidad_pct:.1f}%")
            print(f"   👥 Víctimas: {victimas_pct:.1f}%")
            print(f"   ⏰ Verificado: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            
            return {
                'status': status,
                'trazabilidad_pct': trazabilidad_pct,
                'total_documentos': total,
                'total_victimas': total_victimas,
                'con_trazabilidad': con_nuc
            }
            
    except Exception as e:
        print(f"❌ ERROR durante verificación: {e}")
        return None

def main():
    """Función principal"""
    print("🚀 INICIANDO VERIFICACIÓN DEL SISTEMA")
    print()
    
    resultado = verificar_trazabilidad()
    
    if resultado:
        print(f"\n🏁 VERIFICACIÓN COMPLETADA")
        
        if resultado['trazabilidad_pct'] >= 99:
            print("🎊 ¡SISTEMA COMPLETADO CON ÉXITO!")
            sys.exit(0)
        else:
            print("⚠️ Sistema requiere atención")
            sys.exit(1)
    else:
        print("❌ Error en verificación")
        sys.exit(2)

if __name__ == "__main__":
    main()
