#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agente Inteligente con Análisis por Oraciones usando Semantic Kernel
==================================================================

Este agente descompone consultas complejas en oraciones individuales,
analiza cada oración por separado, y combina las estrategias para
generar un plan de ejecución óptimo.

Enfoque: La oración es la unidad mínima con significado completo.

Autor: Sistema FGN - Septiembre 2025
"""

import os
import json
import asyncio
import logging
import re
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum
from dotenv import load_dotenv

# Semantic Kernel imports
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.core_plugins import TimePlugin

# Imports locales
import psycopg2
import psycopg2.extras

# Cargar variables de entorno
load_dotenv()

class TipoOracion(Enum):
    """Tipos de intención identificados en oraciones"""
    CONSULTA_DATOS = "consulta_datos"           # "dame la lista de víctimas"
    FILTRO_GEOGRAFICO = "filtro_geografico"     # "de Antioquia" 
    FILTRO_TEMPORAL = "filtro_temporal"         # "entre 2020 y 2021"
    FILTRO_TEMATICO = "filtro_tematico"         # "de masacres"
    ANALISIS_CONCEPTUAL = "analisis_conceptual" # "analiza los patrones"
    CONTEXTO_HISTORICO = "contexto_historico"   # "explica el contexto"
    AGREGACION_NUMERICA = "agregacion_numerica" # "cuántas víctimas"
    COMPARACION = "comparacion"                 # "compara con otros departamentos"

class EstrategiaOracion(Enum):
    """Estrategias para ejecutar cada tipo de oración"""
    BD_DIRECTA = "bd_directa"
    RAG_SEMANTICO = "rag_semantico"
    FILTRO_APLICADO = "filtro_aplicado"
    ENRIQUECIMIENTO = "enriquecimiento"

@dataclass
class OracionAnalizada:
    """Resultado del análisis de una oración individual"""
    texto_original: str
    texto_normalizado: str
    tipo: TipoOracion
    estrategia: EstrategiaOracion
    entidades_detectadas: Dict[str, Any]  # departamento, fechas, NUCs, etc.
    confianza: float
    dependencias: List[str] = None  # Qué otras oraciones necesita

@dataclass
class PlanEjecucionCombinado:
    """Plan final combinando todas las oraciones"""
    consulta_original: str
    oraciones_analizadas: List[OracionAnalizada]
    estrategia_principal: str
    orden_ejecucion: List[int]  # Índices de oraciones en orden
    filtros_combinados: Dict[str, Any]
    necesita_bd: bool
    necesita_rag: bool
    sql_optimizado: Optional[str] = None
    confianza_total: float = 0.0

class AgenteAnalisisOraciones:
    """
    Agente que analiza consultas descomponiéndolas en oraciones
    y determinando la estrategia óptima para cada una
    """
    
    def __init__(self):
        self.kernel = self._inicializar_kernel()
        self.esquema_bd = self._cargar_esquema_bd()
        self._registrar_plugins()
        
    def _inicializar_kernel(self) -> sk.Kernel:
        """Inicializa Semantic Kernel"""
        kernel = sk.Kernel()
        
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT") 
        deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4")
        
        kernel.add_service(
            AzureChatCompletion(
                service_id="azure_openai",
                deployment_name=deployment_name,
                endpoint=endpoint,
                api_key=api_key,
            )
        )
        
        kernel.add_plugin(TimePlugin(), plugin_name="Time")
        return kernel
    
    def _cargar_esquema_bd(self) -> Dict[str, Any]:
        """Esquema simplificado enfocado en análisis por oraciones"""
        return {
            "entidades_principales": {
                "victimas": "personas con tipo 'victim'",
                "documentos": "documentos jurídicos completos",
                "ubicaciones": "departamentos y municipios", 
                "casos": "expedientes identificados por NUC"
            },
            "filtros_disponibles": {
                "geograficos": ["departamento", "municipio"],
                "temporales": ["fecha_inicio", "fecha_fin"],
                "temáticos": ["tipo_documento", "nuc", "organizacion"],
                "numericos": ["conteo", "agregacion"]
            },
            "capacidades_bd": [
                "Listados exactos de víctimas",
                "Conteos precisos", 
                "Filtros geográficos",
                "Filtros temporales",
                "Relaciones documentos-víctimas"
            ],
            "capacidades_rag": [
                "Análisis de patrones",
                "Contexto histórico",
                "Búsqueda semántica",
                "Interpretación conceptual"
            ]
        }
    
    def _registrar_plugins(self):
        """Registra funciones como plugins SK"""
        
        @sk.kernel_function(
            description="Descompone una consulta en oraciones independientes",
            name="descomponer_en_oraciones"
        )
        def descomponer_en_oraciones(consulta: str) -> str:
            """Descompone consulta en oraciones usando reglas lingüísticas"""
            # Normalizar consulta
            consulta = consulta.strip()
            
            # Separar por conectores típicos
            separadores = [
                " y ", " e ", " , ", " pero ", " sin embargo ", " además ",
                " también ", " luego ", " después ", " entonces "
            ]
            
            oraciones = [consulta]
            for sep in separadores:
                nuevas_oraciones = []
                for oracion in oraciones:
                    partes = oracion.split(sep)
                    nuevas_oraciones.extend([p.strip() for p in partes if p.strip()])
                oraciones = nuevas_oraciones
            
            # Filtrar oraciones muy cortas
            oraciones_validas = [o for o in oraciones if len(o.split()) >= 2]
            
            return json.dumps({
                "oraciones": oraciones_validas,
                "total": len(oraciones_validas)
            })
        
        @sk.kernel_function(
            description="Analiza el tipo e intención de una oración específica",
            name="analizar_oracion_individual"
        )
        def analizar_oracion_individual(oracion: str) -> str:
            """Analiza una oración individual para determinar tipo y estrategia"""
            oracion_lower = oracion.lower()
            
            # Detectar tipo de oración
            tipo_detectado = TipoOracion.CONSULTA_DATOS  # default
            
            if any(palabra in oracion_lower for palabra in ['de ', 'en ', 'desde ']):
                if any(geo in oracion_lower for geo in ['antioquia', 'medellín', 'bogotá', 'cali', 'departamento', 'municipio']):
                    tipo_detectado = TipoOracion.FILTRO_GEOGRAFICO
                elif any(temp in oracion_lower for temp in ['2020', '2021', '2022', 'enero', 'febrero', 'año']):
                    tipo_detectado = TipoOracion.FILTRO_TEMPORAL
            
            elif any(palabra in oracion_lower for palabra in ['analiza', 'analizar', 'patrón', 'patron']):
                tipo_detectado = TipoOracion.ANALISIS_CONCEPTUAL
                
            elif any(palabra in oracion_lower for palabra in ['contexto', 'historia', 'antecedentes']):
                tipo_detectado = TipoOracion.CONTEXTO_HISTORICO
                
            elif any(palabra in oracion_lower for palabra in ['cuántas', 'cuantas', 'cuántos', 'total']):
                tipo_detectado = TipoOracion.AGREGACION_NUMERICA
                
            elif any(palabra in oracion_lower for palabra in ['dame', 'lista', 'listado', 'muestra']):
                tipo_detectado = TipoOracion.CONSULTA_DATOS
            
            # Determinar estrategia basada en tipo
            estrategia_map = {
                TipoOracion.CONSULTA_DATOS: EstrategiaOracion.BD_DIRECTA,
                TipoOracion.FILTRO_GEOGRAFICO: EstrategiaOracion.FILTRO_APLICADO,
                TipoOracion.FILTRO_TEMPORAL: EstrategiaOracion.FILTRO_APLICADO,
                TipoOracion.FILTRO_TEMATICO: EstrategiaOracion.FILTRO_APLICADO,
                TipoOracion.ANALISIS_CONCEPTUAL: EstrategiaOracion.RAG_SEMANTICO,
                TipoOracion.CONTEXTO_HISTORICO: EstrategiaOracion.RAG_SEMANTICO,
                TipoOracion.AGREGACION_NUMERICA: EstrategiaOracion.BD_DIRECTA,
                TipoOracion.COMPARACION: EstrategiaOracion.ENRIQUECIMIENTO
            }
            
            estrategia = estrategia_map.get(tipo_detectado, EstrategiaOracion.BD_DIRECTA)
            
            # Extraer entidades
            entidades = {}
            
            # Detectar ubicaciones
            ubicaciones = ['antioquia', 'medellín', 'medellin', 'bogotá', 'bogota', 'cali', 'barranquilla']
            for ubi in ubicaciones:
                if ubi in oracion_lower:
                    entidades['departamento'] = ubi.title()
                    break
            
            # Detectar años
            años = re.findall(r'\b(20\d{2})\b', oracion)
            if años:
                entidades['años'] = años
            
            return json.dumps({
                "tipo": tipo_detectado.value,
                "estrategia": estrategia.value,
                "entidades": entidades,
                "confianza": 0.85
            })
        
        self.kernel.add_plugin_from_object(self, plugin_name="AnalizadorOraciones")
    
    async def analizar_consulta_completa(self, consulta: str, filtros_externos: Dict[str, Any] = None) -> PlanEjecucionCombinado:
        """
        Análisis completo: descompone en oraciones y genera plan combinado
        """
        if filtros_externos is None:
            filtros_externos = {}
            
        try:
            # PASO 1: Descomponer en oraciones
            resultado_descomposicion = await self.kernel.invoke_function(
                plugin_name="AnalizadorOraciones",
                function_name="descomponer_en_oraciones",
                consulta=consulta
            )
            
            descomposicion = json.loads(str(resultado_descomposicion))
            oraciones_texto = descomposicion["oraciones"]
            
            logging.info(f"🔍 Oraciones detectadas: {oraciones_texto}")
            
            # PASO 2: Analizar cada oración individualmente
            oraciones_analizadas = []
            
            for i, oracion_texto in enumerate(oraciones_texto):
                resultado_analisis = await self.kernel.invoke_function(
                    plugin_name="AnalizadorOraciones", 
                    function_name="analizar_oracion_individual",
                    oracion=oracion_texto
                )
                
                analisis = json.loads(str(resultado_analisis))
                
                oracion_analizada = OracionAnalizada(
                    texto_original=oracion_texto,
                    texto_normalizado=oracion_texto.lower().strip(),
                    tipo=TipoOracion(analisis["tipo"]),
                    estrategia=EstrategiaOracion(analisis["estrategia"]),
                    entidades_detectadas=analisis["entidades"],
                    confianza=analisis["confianza"]
                )
                
                oraciones_analizadas.append(oracion_analizada)
            
            # PASO 3: Combinar estrategias y generar plan final
            plan_final = self._combinar_estrategias(consulta, oraciones_analizadas, filtros_externos)
            
            return plan_final
            
        except Exception as e:
            logging.error(f"Error en análisis por oraciones: {e}")
            # Fallback simple
            return PlanEjecucionCombinado(
                consulta_original=consulta,
                oraciones_analizadas=[],
                estrategia_principal="BD_DIRECTA",
                orden_ejecucion=[0],
                filtros_combinados=filtros_externos,
                necesita_bd=True,
                necesita_rag=False,
                confianza_total=0.5
            )
    
    def _combinar_estrategias(self, consulta: str, oraciones: List[OracionAnalizada], filtros_externos: Dict[str, Any]) -> PlanEjecucionCombinado:
        """Combina las estrategias de todas las oraciones en un plan coherente"""
        
        # Combinar filtros de todas las oraciones
        filtros_combinados = filtros_externos.copy()
        
        for oracion in oraciones:
            if oracion.entidades_detectadas:
                filtros_combinados.update(oracion.entidades_detectadas)
        
        # Determinar estrategia principal
        estrategias_encontradas = [o.estrategia for o in oraciones]
        
        tiene_bd = any(e in [EstrategiaOracion.BD_DIRECTA, EstrategiaOracion.FILTRO_APLICADO] for e in estrategias_encontradas)
        tiene_rag = any(e in [EstrategiaOracion.RAG_SEMANTICO, EstrategiaOracion.ENRIQUECIMIENTO] for e in estrategias_encontradas)
        
        if tiene_bd and tiene_rag:
            estrategia_principal = "HIBRIDO"
        elif tiene_rag:
            estrategia_principal = "RAG_SEMANTICO"  
        else:
            estrategia_principal = "BD_DIRECTA"
        
        # Generar SQL si es consulta BD
        sql_optimizado = None
        if tiene_bd and any(o.tipo == TipoOracion.CONSULTA_DATOS for o in oraciones):
            sql_optimizado = self._generar_sql_desde_oraciones(oraciones, filtros_combinados)
        
        # Calcular confianza total
        confianza_total = sum(o.confianza for o in oraciones) / len(oraciones) if oraciones else 0.5
        
        return PlanEjecucionCombinado(
            consulta_original=consulta,
            oraciones_analizadas=oraciones,
            estrategia_principal=estrategia_principal,
            orden_ejecucion=list(range(len(oraciones))),
            filtros_combinados=filtros_combinados,
            necesita_bd=tiene_bd,
            necesita_rag=tiene_rag,
            sql_optimizado=sql_optimizado,
            confianza_total=confianza_total
        )
    
    def _generar_sql_desde_oraciones(self, oraciones: List[OracionAnalizada], filtros: Dict[str, Any]) -> str:
        """Genera SQL optimizado basado en análisis de oraciones"""
        
        # Detectar si es consulta de víctimas
        es_consulta_victimas = any(
            "víctima" in o.texto_normalizado or "victima" in o.texto_normalizado 
            for o in oraciones
        )
        
        if es_consulta_victimas:
            sql = """
            SELECT DISTINCT
                p.nombre,
                p.tipo,
                m.departamento,
                m.municipio,
                m.nuc,
                d.archivo_nombre
            FROM personas p
            JOIN documentos d ON p.documento_id = d.id
            LEFT JOIN metadatos m ON d.id = m.documento_id
            WHERE (p.tipo ILIKE '%victim%' OR p.observaciones ILIKE '%victim%')
            AND p.tipo NOT ILIKE '%victimario%'
            AND p.nombre IS NOT NULL AND p.nombre != ''
            """
            
            # Aplicar filtros detectados en oraciones
            if filtros.get('departamento'):
                sql += f" AND m.departamento ILIKE '%{filtros['departamento']}%'"
            
            sql += " ORDER BY p.nombre LIMIT 100"
            
            return sql
        
        return None
    
    def analizar_consulta_sincrono(self, consulta: str, filtros: Dict[str, Any] = None) -> PlanEjecucionCombinado:
        """Versión síncrona para Streamlit"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        lambda: asyncio.run(self.analizar_consulta_completa(consulta, filtros))
                    )
                    return future.result()
            else:
                return loop.run_until_complete(self.analizar_consulta_completa(consulta, filtros))
        except RuntimeError:
            return asyncio.run(self.analizar_consulta_completa(consulta, filtros))

# Factory function
def crear_agente_oraciones() -> AgenteAnalisisOraciones:
    """Crea instancia del agente de análisis por oraciones"""
    return AgenteAnalisisOraciones()

if __name__ == "__main__":
    async def test_oraciones():
        agente = AgenteAnalisisOraciones()
        
        # Test consulta compleja
        consulta = "dame la lista de víctimas de Antioquia y analiza los patrones de violencia"
        plan = await agente.analizar_consulta_completa(consulta)
        
        print(f"Consulta: {consulta}")
        print(f"Oraciones encontradas: {len(plan.oraciones_analizadas)}")
        for i, oracion in enumerate(plan.oraciones_analizadas):
            print(f"  {i+1}. '{oracion.texto_original}' → {oracion.tipo.value} → {oracion.estrategia.value}")
        print(f"Estrategia final: {plan.estrategia_principal}")
        print(f"Filtros: {plan.filtros_combinados}")
    
    asyncio.run(test_oraciones())