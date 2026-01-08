#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agente Inteligente de Consultas usando Semantic Kernel
=====================================================

Este agente analiza consultas del usuario, conoce el esquema de la BD PostgreSQL,
y decide la mejor estrategia (BD directa, RAG semántico, o híbrido) usando
Semantic Kernel para orquestar la decisión.

Autor: Sistema FGN - Septiembre 2025
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum
from dotenv import load_dotenv

# Semantic Kernel imports
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.core_plugins import TimePlugin, MathPlugin
from semantic_kernel.prompt_template import PromptTemplateConfig

# Imports locales
import psycopg2
import psycopg2.extras

# Cargar variables de entorno
load_dotenv()

class EstrategiaConsulta(Enum):
    """Estrategias disponibles para ejecutar consultas"""
    BD_DIRECTA = "bd_directa"           # Consulta PostgreSQL directa
    RAG_SEMANTICO = "rag_semantico"    # Análisis semántico con Azure Search
    HIBRIDO = "hibrido"                # Combinar BD + RAG
    BD_ENRIQUECIDO = "bd_enriquecido"  # BD + contexto RAG mínimo

@dataclass
class PlanConsulta:
    """Plan de ejecución generado por el agente"""
    consulta_original: str
    estrategia: EstrategiaConsulta
    confianza: float
    justificacion: str
    filtros_detectados: Dict[str, Any]
    sql_generado: Optional[str] = None
    necesita_contexto: bool = False
    tablas_involucradas: List[str] = None
    
class AgenteConsultasInteligente:
    """
    Agente inteligente que usa Semantic Kernel para analizar consultas
    y decidir la mejor estrategia de ejecución
    """
    
    def __init__(self):
        self.kernel = self._inicializar_kernel()
        self.esquema_bd = self._cargar_esquema_postgresql()
        self.capacidades_rag = self._definir_capacidades_rag()
        self._registrar_plugins()
        
    def _inicializar_kernel(self) -> sk.Kernel:
        """Inicializa Semantic Kernel con Azure OpenAI"""
        kernel = sk.Kernel()
        
        # Configurar Azure OpenAI
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
        
        # Agregar plugins básicos
        kernel.add_plugin(TimePlugin(), plugin_name="Time")
        kernel.add_plugin(MathPlugin(), plugin_name="Math")
        
        return kernel
    
    def _cargar_esquema_postgresql(self) -> Dict[str, Any]:
        """Carga el esquema real de PostgreSQL"""
        return {
            "tablas": {
                "personas": {
                    "descripcion": "Víctimas y personas mencionadas en documentos",
                    "campos": {
                        "id": "SERIAL PRIMARY KEY",
                        "nombre": "VARCHAR - Nombre de la persona/víctima",
                        "tipo": "VARCHAR - Tipo (victim, victimario, testigo, etc.)",
                        "documento_id": "INTEGER - FK a documentos.id",
                        "observaciones": "TEXT - Observaciones adicionales"
                    },
                    "indices": ["nombre", "tipo", "documento_id"],
                    "filtros_geograficos": "Via JOIN con documentos->metadatos"
                },
                "documentos": {
                    "descripcion": "Documentos jurídicos completos",
                    "campos": {
                        "id": "SERIAL PRIMARY KEY", 
                        "contenido": "TEXT - Contenido completo del documento",
                        "archivo_nombre": "VARCHAR - Nombre del archivo",
                        "fecha_creacion": "TIMESTAMP - Fecha de creación"
                    },
                    "indices": ["archivo_nombre", "fecha_creacion"]
                },
                "metadatos": {
                    "descripcion": "Metadatos de documentos incluyendo geografía",
                    "campos": {
                        "id": "SERIAL PRIMARY KEY",
                        "documento_id": "INTEGER - FK a documentos.id",
                        "nuc": "VARCHAR - Número Único de Caso",
                        "departamento": "VARCHAR - Departamento geográfico", 
                        "municipio": "VARCHAR - Municipio geográfico",
                        "tipo_documento": "VARCHAR - Tipo de documento",
                        "fecha": "DATE - Fecha del evento/documento"
                    },
                    "indices": ["nuc", "departamento", "municipio", "tipo_documento"]
                }
            },
            "relaciones": {
                "personas.documento_id -> documentos.id": "Una persona pertenece a un documento",
                "metadatos.documento_id -> documentos.id": "Metadatos pertenecen a un documento",
                "personas -> metadatos (via documentos)": "Acceso a datos geográficos de víctimas"
            },
            "consultas_optimizadas": {
                "victimas_por_geografia": "SELECT p.* FROM personas p JOIN documentos d ON p.documento_id = d.id JOIN metadatos m ON d.id = m.documento_id WHERE m.departamento = ? AND p.tipo ILIKE '%victim%'",
                "conteo_victimas": "SELECT COUNT(*) FROM personas WHERE tipo ILIKE '%victim%'",
                "victimas_con_contexto": "Requiere JOIN completo personas->documentos->metadatos"
            }
        }
    
    def _definir_capacidades_rag(self) -> Dict[str, Any]:
        """Define qué puede hacer el sistema RAG"""
        return {
            "analisis_semantico": [
                "Análisis de patrones de violencia",
                "Contexto histórico de eventos", 
                "Relaciones entre organizaciones",
                "Análisis conceptual de términos jurídicos"
            ],
            "busqueda_documental": [
                "Búsqueda por contenido semántico",
                "Extracción de fragmentos relevantes",
                "Ranking por relevancia",
                "Búsqueda en texto completo"
            ],
            "limitaciones": [
                "No hace agregaciones numéricas precisas",
                "No filtra por metadatos estructurados eficientemente", 
                "No garantiza completitud de datos",
                "Mejor para análisis cualitativo que cuantitativo"
            ]
        }
    
    def _registrar_plugins(self):
        """Registra funciones como plugins de Semantic Kernel"""
        
        @sk.kernel_function(
            description="Analiza una consulta y determina si requiere acceso directo a base de datos estructurada",
            name="analizar_necesidad_bd"
        )
        def analizar_necesidad_bd(consulta: str, filtros: str) -> str:
            """Determina si la consulta necesita BD directa"""
            consulta_lower = consulta.lower()
            
            # Casos claros de BD directa
            indicadores_bd = [
                "lista" in consulta_lower and ("víctima" in consulta_lower or "victima" in consulta_lower),
                "cuántas" in consulta_lower or "cuantas" in consulta_lower,
                "total" in consulta_lower and ("víctima" in consulta_lower or "victima" in consulta_lower),
                "conteo" in consulta_lower,
                "estadística" in consulta_lower or "estadistica" in consulta_lower
            ]
            
            if any(indicadores_bd):
                return "BD_DIRECTA: Consulta requiere datos estructurados precisos"
            
            return "EVALUAR: Necesita análisis más profundo"
        
        @sk.kernel_function(
            description="Analiza si una consulta requiere análisis semántico o conceptual",
            name="analizar_necesidad_rag"
        )
        def analizar_necesidad_rag(consulta: str) -> str:
            """Determina si la consulta necesita RAG semántico"""
            consulta_lower = consulta.lower()
            
            # Casos claros de RAG
            indicadores_rag = [
                "por qué" in consulta_lower or "porque" in consulta_lower,
                "qué significa" in consulta_lower or "que significa" in consulta_lower,
                "analizar" in consulta_lower or "analiza" in consulta_lower,
                "contexto" in consulta_lower,
                "patrón" in consulta_lower or "patron" in consulta_lower,
                "genocidio" in consulta_lower,
                "unión patriótica" in consulta_lower or "union patriotica" in consulta_lower,
                # NUEVO: hipótesis de investigación
                "hipótesis" in consulta_lower or "hipotesis" in consulta_lower or
                "lineas de investigacion" in consulta_lower or "líneas de investigación" in consulta_lower or
                "plantea una hipótesis" in consulta_lower or "plantee una hipótesis" in consulta_lower or
                "posibles explicaciones" in consulta_lower or "explicaciones plausibles" in consulta_lower or
                "hipótesis de investigación" in consulta_lower or "hipotesis de investigacion" in consulta_lower
            ]
            
            if any(indicadores_rag):
                return "RAG_SEMANTICO: Consulta requiere análisis conceptual"
                
            return "EVALUAR: Necesita análisis más profundo"
        
        @sk.kernel_function(
            description="Genera SQL optimizado para consultas de víctimas con filtros geográficos",
            name="generar_sql_victimas"
        )
        def generar_sql_victimas(filtros_json: str) -> str:
            """Genera SQL para consultas de víctimas"""
            try:
                filtros = json.loads(filtros_json)
                
                sql_base = """
                SELECT DISTINCT
                    p.nombre,
                    p.tipo,
                    m.departamento,
                    m.municipio,
                    m.nuc,
                    d.archivo_nombre
                FROM personas p
                JOIN documentos d ON p.documento_id = d.id
                JOIN metadatos m ON d.id = m.documento_id
                WHERE (p.tipo ILIKE '%victim%' OR p.observaciones ILIKE '%victim%')
                AND p.tipo NOT ILIKE '%victimario%'
                AND p.nombre IS NOT NULL AND p.nombre != ''
                """
                
                params = []
                
                if filtros.get('departamento'):
                    sql_base += " AND m.departamento = %s"
                    params.append(filtros['departamento'])
                    
                if filtros.get('municipio'):
                    sql_base += " AND m.municipio = %s"
                    params.append(filtros['municipio'])
                    
                if filtros.get('nucs'):
                    placeholders = ','.join(['%s'] * len(filtros['nucs']))
                    sql_base += f" AND m.nuc IN ({placeholders})"
                    params.extend(filtros['nucs'])
                
                sql_base += " ORDER BY p.nombre LIMIT 100"
                
                return json.dumps({
                    "sql": sql_base,
                    "params": params,
                    "estrategia": "BD_DIRECTA"
                })
                
            except Exception as e:
                return f"Error generando SQL: {str(e)}"
        
        # Registrar plugins en el kernel
        self.kernel.add_plugin_from_object(self, plugin_name="ConsultasDB")
    
    async def analizar_consulta(self, consulta: str, filtros: Dict[str, Any] = None) -> PlanConsulta:
        """
        Función principal: analiza la consulta y genera plan de ejecución
        """
        if filtros is None:
            filtros = {}
            
        try:
            # Regla de ruteo rápida: consultas de hipótesis deben ir a RAG SEMÁNTICO
            consulta_lower = consulta.lower()
            if any(k in consulta_lower for k in [
                "hipótesis", "hipotesis", "líneas de investigación", "lineas de investigacion",
                "plantee una hipótesis", "plantea una hipótesis", "posibles explicaciones", "explicaciones plausibles"
            ]):
                return PlanConsulta(
                    consulta_original=consulta,
                    estrategia=EstrategiaConsulta.RAG_SEMANTICO,
                    confianza=0.9,
                    justificacion="Consulta identificada como generación de hipótesis de investigación; se requiere análisis semántico con LLM",
                    filtros_detectados=filtros,
                    necesita_contexto=True,
                    tablas_involucradas=[]
                )

            # Prompt principal para análisis de consulta
            prompt_analisis = f"""
Eres un experto analista de consultas para un sistema jurídico que combina:
1. Base de datos PostgreSQL con víctimas, documentos y metadatos geográficos
2. Sistema RAG para análisis semántico de documentos

ESQUEMA BD DISPONIBLE:
{json.dumps(self.esquema_bd, indent=2, ensure_ascii=False)}

CAPACIDADES RAG:
{json.dumps(self.capacidades_rag, indent=2, ensure_ascii=False)}

CONSULTA DEL USUARIO: "{consulta}"
FILTROS APLICADOS: {json.dumps(filtros, ensure_ascii=False)}

ANALIZA y determina la MEJOR ESTRATEGIA:

1. BD_DIRECTA: Para listas, conteos, datos estructurados precisos
2. RAG_SEMANTICO: Para análisis conceptual, patrones, contexto histórico  
3. HIBRIDO: Para datos estructurados + contexto semántico
4. BD_ENRIQUECIDO: BD + contexto mínimo

Responde en JSON:
{{
    "estrategia": "BD_DIRECTA|RAG_SEMANTICO|HIBRIDO|BD_ENRIQUECIDO",
    "confianza": 0.95,
    "justificacion": "Explicación detallada",
    "tablas_involucradas": ["personas", "metadatos"],
    "necesita_contexto": false,
    "sql_sugerido": "SELECT ... (si aplica)"
}}
"""

            # Ejecutar análisis con Semantic Kernel
            resultado = await self.kernel.invoke_prompt(prompt_analisis)
            
            # Parsear respuesta JSON
            respuesta_texto = str(resultado).strip()
            if respuesta_texto.startswith('```json'):
                respuesta_texto = respuesta_texto[7:-3]
            elif respuesta_texto.startswith('```'):
                respuesta_texto = respuesta_texto[3:-3]
                
            analisis = json.loads(respuesta_texto)
            
            # Crear plan de consulta
            plan = PlanConsulta(
                consulta_original=consulta,
                estrategia=EstrategiaConsulta(analisis['estrategia'].lower()),
                confianza=analisis['confianza'],
                justificacion=analisis['justificacion'],
                filtros_detectados=filtros,
                sql_generado=analisis.get('sql_sugerido'),
                necesita_contexto=analisis.get('necesita_contexto', False),
                tablas_involucradas=analisis.get('tablas_involucradas', [])
            )
            
            logging.info(f"🤖 Agente SK - Estrategia: {plan.estrategia.value} (Confianza: {plan.confianza})")
            logging.info(f"🤖 Agente SK - Justificación: {plan.justificacion}")
            
            return plan
            
        except Exception as e:
            logging.error(f"Error en agente inteligente: {e}")
            # Fallback a BD directa para consultas de víctimas
            if any(palabra in consulta.lower() for palabra in ['víctima', 'victima', 'lista']):
                return PlanConsulta(
                    consulta_original=consulta,
                    estrategia=EstrategiaConsulta.BD_DIRECTA,
                    confianza=0.7,
                    justificacion=f"Fallback a BD por error en análisis: {str(e)}",
                    filtros_detectados=filtros
                )
            else:
                return PlanConsulta(
                    consulta_original=consulta,
                    estrategia=EstrategiaConsulta.RAG_SEMANTICO,
                    confianza=0.5,
                    justificacion=f"Fallback a RAG por error: {str(e)}",
                    filtros_detectados=filtros
                )

    async def generar_hipotesis_investigacion(self, consulta: str, contexto: Optional[str] = None) -> str:
        """Genera hipótesis de investigación estructuradas a partir de la consulta y opcionalmente un contexto.

        Salida esperada (Markdown):
        - 3 a 5 hipótesis numeradas
        - Para cada hipótesis: descripción, evidencias de soporte, supuestos, señales en contra, cómo refutar/confirmar, próximos pasos.
        """
        instrucciones = f"""
Eres un analista senior de la Fiscalía especializado en construcción de hipótesis de investigación.

Tarea: A partir de la consulta del usuario, plantea hipótesis de investigación claras, contrastables y accionables.

Consulta del usuario: "{consulta}"
{f'\nContexto disponible (resumen):\n{contexto}\n' if contexto else ''}

Devuelve en Markdown, con este formato:

## Hipótesis de Investigación

1) [Título breve de la hipótesis]
   - Descripción: ...
   - Evidencias de soporte: ...
   - Supuestos: ...
   - Señales en contra: ...
   - Cómo refutar/confirmar: ...
   - Próximos pasos (acciones): ...

2) ... (entre 3 y 5 hipótesis)

Criterios:
- Redacta en lenguaje claro y jurídico.
- Evita afirmaciones categóricas; usa lenguaje probabilístico.
- Orienta a acciones concretas de verificación.
        """

        resultado = await self.kernel.invoke_prompt(instrucciones)
        return str(resultado).strip()
    
    def analizar_consulta_sincrona(self, consulta: str, filtros: Dict[str, Any] = None) -> PlanConsulta:
        """Versión síncrona para compatibilidad con Streamlit"""
        try:
            # Intentar usar loop existente
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Si hay loop corriendo, usar thread executor
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        lambda: asyncio.run(self.analizar_consulta(consulta, filtros))
                    )
                    return future.result()
            else:
                return loop.run_until_complete(self.analizar_consulta(consulta, filtros))
        except RuntimeError:
            # No hay loop, crear uno nuevo
            return asyncio.run(self.analizar_consulta(consulta, filtros))
    
    def generar_sql_optimizado(self, plan: PlanConsulta) -> Tuple[str, List]:
        """Genera SQL optimizado basado en el plan"""
        if plan.estrategia != EstrategiaConsulta.BD_DIRECTA:
            return None, []
            
        # SQL base para víctimas
        if any(palabra in plan.consulta_original.lower() for palabra in ['víctima', 'victima']):
            sql = """
            SELECT DISTINCT
                p.nombre,
                p.tipo,
                m.departamento,
                m.municipio,
                m.nuc,
                d.archivo_nombre,
                COUNT(*) OVER() as total_count
            FROM personas p
            JOIN documentos d ON p.documento_id = d.id
            LEFT JOIN metadatos m ON d.id = m.documento_id
            WHERE (p.tipo ILIKE %s OR p.observaciones ILIKE %s)
            AND p.tipo NOT ILIKE %s
            AND p.nombre IS NOT NULL AND p.nombre != ''
            """
            
            params = ['%victim%', '%victim%', '%victimario%']
            
            # Aplicar filtros
            if plan.filtros_detectados.get('departamento'):
                sql += " AND m.departamento = %s"
                params.append(plan.filtros_detectados['departamento'])
                
            if plan.filtros_detectados.get('municipio'):
                sql += " AND m.municipio = %s"
                params.append(plan.filtros_detectados['municipio'])
                
            if plan.filtros_detectados.get('nucs'):
                placeholders = ','.join(['%s'] * len(plan.filtros_detectados['nucs']))
                sql += f" AND m.nuc IN ({placeholders})"
                params.extend(plan.filtros_detectados['nucs'])
            
            sql += " ORDER BY p.nombre LIMIT 100"
            
            return sql, params
            
        return None, []

# Función de conveniencia para usar en el sistema principal
def crear_agente_inteligente() -> AgenteConsultasInteligente:
    """Factory function para crear el agente"""
    return AgenteConsultasInteligente()

if __name__ == "__main__":
    # Test básico
    async def test_agente():
        agente = AgenteConsultasInteligente()
        
        # Test 1: Consulta de víctimas con filtro geográfico
        plan1 = await agente.analizar_consulta(
            "dame la lista total de víctimas", 
            {"departamento": "Antioquia"}
        )
        print(f"Plan 1: {plan1.estrategia.value} - {plan1.justificacion}")
        
        # Test 2: Consulta analítica
        plan2 = await agente.analizar_consulta(
            "analiza los patrones de violencia contra la Unión Patriótica"
        )
        print(f"Plan 2: {plan2.estrategia.value} - {plan2.justificacion}")
    
    # Ejecutar test
    asyncio.run(test_agente())