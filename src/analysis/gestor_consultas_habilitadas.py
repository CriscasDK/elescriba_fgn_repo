#!/usr/bin/env python3
"""
🎯 SISTEMA DE CONSULTAS HABILITADAS PROGRESIVAMENTE
Permite habilitar/deshabilitar consultas específicas gradualmente
"""

import psycopg2
from dotenv import load_dotenv
import os
import json
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class ConsultaHabilitada:
    id: str
    nombre: str
    patron: str
    habilitada: bool
    descripcion: str
    tipo_respuesta: str  # 'conteo', 'listado', 'analisis'

class GestorConsultasHabilitadas:
    def __init__(self):
        load_dotenv('.env.gpt41')
        self.db_config = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': os.getenv('POSTGRES_PORT', '5432'),
            'database': os.getenv('POSTGRES_DB', 'documentos_juridicos_gpt4'),
            'user': os.getenv('POSTGRES_USER', 'docs_user'),
            'password': os.getenv('POSTGRES_PASSWORD', 'docs_password_2024')
        }
        
        # Configuración de consultas disponibles
        self.consultas_disponibles = [
            ConsultaHabilitada(
                id="conteo_victimas",
                nombre="Conteo de Víctimas",
                patron="cuant.*victima",
                habilitada=True,
                descripcion="Cuenta víctimas únicas excluyendo victimarios",
                tipo_respuesta="conteo"
            ),
            ConsultaHabilitada(
                id="listado_victimas",
                nombre="Listado de Víctimas",
                patron="list.*victima|victima.*list|mostrar.*victima",
                habilitada=False,
                descripcion="Lista todas las víctimas con metadatos completos",
                tipo_respuesta="listado"
            ),
            ConsultaHabilitada(
                id="conteo_victimarios",
                nombre="Conteo de Victimarios",
                patron="cuant.*victimario",
                habilitada=True,
                descripcion="Cuenta victimarios únicos",
                tipo_respuesta="conteo"
            ),
            ConsultaHabilitada(
                id="listado_victimarios",
                nombre="Listado de Victimarios", 
                patron="list.*victimario|victimario.*list|mostrar.*victimario",
                habilitada=False,
                descripcion="Lista todos los victimarios con metadatos",
                tipo_respuesta="listado"
            ),
            ConsultaHabilitada(
                id="conteo_documentos",
                nombre="Conteo de Documentos",
                patron="cuant.*documento",
                habilitada=True,
                descripcion="Cuenta documentos totales",
                tipo_respuesta="conteo"
            ),
            ConsultaHabilitada(
                id="analisis_temporal",
                nombre="Análisis Temporal",
                patron="cuando|fecha|temporal|año|periodo",
                habilitada=False,
                descripcion="Análisis de patrones temporales",
                tipo_respuesta="analisis"
            ),
            ConsultaHabilitada(
                id="analisis_geografico",
                nombre="Análisis Geográfico",
                patron="donde|lugar|departamento|municipio|region",
                habilitada=False,
                descripcion="Análisis de patrones geográficos",
                tipo_respuesta="analisis"
            )
        ]
    
    def get_consultas_habilitadas(self) -> List[ConsultaHabilitada]:
        """Obtener solo consultas habilitadas"""
        return [c for c in self.consultas_disponibles if c.habilitada]
    
    def habilitar_consulta(self, consulta_id: str) -> bool:
        """Habilitar una consulta específica"""
        for consulta in self.consultas_disponibles:
            if consulta.id == consulta_id:
                consulta.habilitada = True
                print(f"✅ Consulta '{consulta.nombre}' HABILITADA")
                return True
        return False
    
    def deshabilitar_consulta(self, consulta_id: str) -> bool:
        """Deshabilitar una consulta específica"""
        for consulta in self.consultas_disponibles:
            if consulta.id == consulta_id:
                consulta.habilitada = False
                print(f"❌ Consulta '{consulta.nombre}' DESHABILITADA")
                return True
        return False
    
    def obtener_listado_victimas(self, limit: int = 100, offset: int = 0) -> Dict:
        """Obtener listado completo de víctimas con metadatos"""
        try:
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor() as cur:
                    # Primero obtener el total
                    cur.execute("""
                        SELECT COUNT(DISTINCT p.nombre)
                        FROM personas p
                        JOIN documentos d ON p.documento_id = d.id
                        WHERE p.tipo ILIKE '%victima%' AND p.tipo NOT ILIKE '%victimario%'
                          AND p.nombre IS NOT NULL AND p.nombre != ''
                    """)
                    
                    total_count = cur.fetchone()[0]
                    
                    # Query principal con metadatos
                    cur.execute("""
                        SELECT DISTINCT
                            p.nombre,
                            p.tipo,
                            d.nuc,
                            d.ruta,
                            d.created_at,
                            d.serie,
                            d.id as documento_id
                        FROM personas p
                        JOIN documentos d ON p.documento_id = d.id
                        WHERE p.tipo ILIKE '%victima%' AND p.tipo NOT ILIKE '%victimario%'
                          AND p.nombre IS NOT NULL AND p.nombre != ''
                        ORDER BY p.nombre, d.created_at DESC
                        LIMIT %s OFFSET %s
                    """, (limit, offset))
                    
                    resultados = cur.fetchall()
                    
                    victimas = []
                    for row in resultados:
                        if len(row) != 7:
                            continue
                            
                        nombre, tipo, nuc, ruta, fecha, serie, doc_id = row
                        
                        victimas.append({
                            'nombre': nombre.strip() if nombre else 'N/A',
                            'tipo': tipo,
                            'metadatos': {
                                'nuc': nuc or 'N/A',
                                'ruta': ruta or 'N/A',
                                'fecha_creacion': fecha.isoformat() if fecha else None,
                                'tipo_documento': serie or 'N/A',
                                'documento_id': doc_id
                            }
                        })
                    
                    return {
                        'victimas': victimas,
                        'total': total_count,
                        'limite': limit,
                        'offset': offset,
                        'paginas': (total_count + limit - 1) // limit if total_count > 0 else 0
                    }
                    
        except Exception as e:
            print(f"❌ Error obteniendo listado: {e}")
            return {'error': str(e)}
    
    def obtener_documento_completo(self, documento_id: int) -> Dict:
        """Obtener documento completo con análisis y texto"""
        try:
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT 
                            id, nuc, ruta, texto_extraido, 
                            analisis, created_at, serie,
                            despacho
                        FROM documentos 
                        WHERE id = %s
                    """, (documento_id,))
                    
                    resultado = cur.fetchone()
                    
                    if not resultado:
                        return {'error': 'Documento no encontrado'}
                    
                    doc_id, nuc, ruta, texto, analisis, fecha, serie, despacho = resultado
                    
                    return {
                        'documento_id': doc_id,
                        'nuc': nuc,
                        'ruta_archivo': ruta,
                        'fecha_creacion': fecha.isoformat() if fecha else None,
                        'tipo_documento': serie,
                        'despacho': despacho,
                        'texto_extraido': texto,
                        'analisis': analisis
                    }
                    
        except Exception as e:
            print(f"❌ Error obteniendo documento: {e}")
            return {'error': str(e)}
    
    def mostrar_estado_consultas(self):
        """Mostrar estado actual de todas las consultas"""
        print("🎯 ESTADO ACTUAL DE CONSULTAS")
        print("=" * 60)
        
        habilitadas = 0
        for consulta in self.consultas_disponibles:
            estado = "✅ HABILITADA" if consulta.habilitada else "❌ DESHABILITADA"
            print(f"{estado} | {consulta.nombre}")
            print(f"           📝 {consulta.descripcion}")
            print(f"           🔍 Patrón: {consulta.patron}")
            print(f"           📊 Tipo: {consulta.tipo_respuesta}")
            print()
            
            if consulta.habilitada:
                habilitadas += 1
        
        print(f"📈 RESUMEN: {habilitadas}/{len(self.consultas_disponibles)} consultas habilitadas")

def main():
    gestor = GestorConsultasHabilitadas()
    
    print("🚀 INICIANDO GESTOR DE CONSULTAS HABILITADAS")
    print("=" * 60)
    
    # Mostrar estado actual
    gestor.mostrar_estado_consultas()
    
    # Test de listado de víctimas
    print("\n🧪 TEST: Listado de Víctimas (primeras 5)")
    print("=" * 50)
    
    resultado = gestor.obtener_listado_victimas(limit=5)
    
    if 'error' in resultado:
        print(f"❌ Error: {resultado['error']}")
    else:
        print(f"📊 Total víctimas: {resultado['total']:,}")
        print(f"📄 Mostrando: {len(resultado['victimas'])}")
        print(f"📑 Páginas: {resultado['paginas']}")
        
        for i, victima in enumerate(resultado['victimas'], 1):
            print(f"\n{i}. {victima['nombre']} ({victima['tipo']})")
            meta = victima['metadatos']
            print(f"   📁 NUC: {meta['nuc']}")
            print(f"   📄 Archivo: {meta['ruta']}")
            print(f"   📅 Fecha: {meta['fecha_creacion']}")
            print(f"   📋 Tipo: {meta['tipo_documento']}")

if __name__ == "__main__":
    main()
