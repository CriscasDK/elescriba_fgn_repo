#!/usr/bin/env python3
"""
Sistema RAG Completo con Trazabilidad y Mejora Continua
Integra consultas frecuentes (vistas materializadas) con generación LLM
"""

import os
import json
import time
import hashlib
import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from decimal import Decimal

import psycopg2
import psycopg2.extras
from openai import AzureOpenAI
from dotenv import load_dotenv

# Importar Azure Search 
try:
    from .azure_search_vectorizado import AzureSearchVectorizado
except ImportError:
    try:
        from azure_search_vectorizado import AzureSearchVectorizado
    except ImportError:
        print("WARNING: Azure Search no disponible")

def convert_db_types(obj):
    """Convertir tipos de base de datos a tipos JSON-serializables"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: convert_db_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_db_types(item) for item in obj]
    else:
        return obj

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/rag_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv('.env.gpt41')

class TipoConsulta(Enum):
    FRECUENTE = "frecuente"
    RAG = "rag"
    HIBRIDA = "hibrida"

class MetodoResolucion(Enum):
    VISTA_MATERIALIZADA = "vista_materializada"
    BUSQUEDA_SQL = "busqueda_sql"
    LLM_GENERACION = "llm_generacion"
    CACHE = "cache"

@dataclass
class ConsultaRAG:
    usuario_id: str
    pregunta: str
    sesion_id: Optional[str] = None
    ip_cliente: Optional[str] = None
    user_agent: Optional[str] = None

@dataclass
@dataclass
class RespuestaRAG:
    texto: str
    fuentes: List[Dict[str, Any]]
    confianza: float
    metodo: MetodoResolucion
    tiempo_respuesta: int
    id: Optional[int] = None
    datos_estructurados: Optional[Dict] = None
    metadatos_llm: Optional[Dict] = None

@dataclass
class FeedbackRAG:
    calificacion: int  # 1-5
    comentario: Optional[str] = None
    aspectos: Optional[Dict[str, int]] = None  # {precision: 4, relevancia: 5}
    respuesta_esperada: Optional[str] = None

class SistemaRAGTrazable:
    """Sistema RAG con trazabilidad completa y mejora continua"""
    
    def __init__(self):
        self.db_config = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': os.getenv('POSTGRES_PORT', '5432'),
            'database': os.getenv('POSTGRES_DB', 'documentos_juridicos_gpt4'),
            'user': os.getenv('POSTGRES_USER', 'docs_user'),
            'password': os.getenv('POSTGRES_PASSWORD', 'docs_password_2024')
        }
        
        # Cliente Azure OpenAI con cliente HTTP limpio
        import httpx
        http_client = httpx.Client(
            timeout=30.0,
            headers={"User-Agent": "RAG-System/1.0"}
        )
        
        self.azure_client = AzureOpenAI(
            api_key=os.getenv('AZURE_OPENAI_API_KEY'),
            api_version=os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview'),
            azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
            http_client=http_client
        )
        
        self.deployment_name = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4o-mini')
        
        # Templates para diferentes tipos de respuesta
        self.templates = {
            'estadisticas': """
Basándome en los datos del sistema de documentos judiciales:

{datos_estructurados}

Resumen: {contexto}

Esta información proviene de {num_fuentes} fuente(s) de datos procesadas automáticamente.
""",
            
            'busqueda_entidades': """
He encontrado la siguiente información sobre "{termino_busqueda}":

{resultados_busqueda}

Fuentes consultadas: {fuentes}

¿Te gustaría que profundice en algún aspecto específico?
""",
            
            'analisis_relaciones': """
Análisis de relaciones para "{consulta}":

{analisis_redes}

Esta información se basa en el análisis de co-ocurrencia de entidades en {num_documentos} documentos procesados.
""",
            
            'pregunta_compleja': """
Contexto relevante encontrado:

{contexto_sql}

Análisis detallado:

{respuesta_llm}

Fuentes: {fuentes_detalle}
"""
        }

    def get_db_connection(self):
        """Obtener conexión a la base de datos"""
        return psycopg2.connect(**self.db_config)

    async def procesar_consulta(self, consulta: ConsultaRAG) -> Tuple[RespuestaRAG, int]:
        """Procesar consulta RAG con trazabilidad completa"""
        start_time = time.time()
        
        try:
            # 1. Registrar consulta
            with self.get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT registrar_consulta_rag(%s, %s, %s, %s)
                    """, (consulta.usuario_id, consulta.pregunta, consulta.ip_cliente, consulta.user_agent))
                    
                    consulta_id = cur.fetchone()[0]
                    logger.info(f"Consulta registrada con ID: {consulta_id}")

            # 2. Buscar en cache
            respuesta_cache = await self._buscar_cache(consulta.pregunta)
            if respuesta_cache:
                logger.info("Respuesta encontrada en cache")
                tiempo_respuesta = int((time.time() - start_time) * 1000)
                return respuesta_cache, consulta_id

            # 3. Clasificar tipo de consulta
            tipo_consulta = await self._clasificar_consulta(consulta.pregunta)
            logger.info(f"Tipo de consulta detectado: {tipo_consulta}")

            # 4. Resolver según tipo
            if tipo_consulta == TipoConsulta.FRECUENTE:
                respuesta = await self._resolver_consulta_frecuente(consulta.pregunta)
            elif tipo_consulta == TipoConsulta.RAG:
                respuesta = await self._resolver_consulta_rag(consulta.pregunta)
            else:
                respuesta = await self._resolver_consulta_hibrida(consulta.pregunta)

            # 5. Calcular tiempo de respuesta
            tiempo_respuesta = int((time.time() - start_time) * 1000)
            respuesta.tiempo_respuesta = tiempo_respuesta

            # 6. Registrar respuesta
            with self.get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT registrar_respuesta_rag(%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        consulta_id, respuesta.texto, json.dumps(convert_db_types(respuesta.fuentes)),
                        respuesta.confianza, respuesta.metodo.value,
                        json.dumps(convert_db_types(respuesta.datos_estructurados)) if respuesta.datos_estructurados else None,
                        json.dumps(convert_db_types(respuesta.metadatos_llm)) if respuesta.metadatos_llm else None
                    ))
                    respuesta_id = cur.fetchone()[0]
                    respuesta.id = respuesta_id

            # 7. Actualizar métricas de consulta
            with self.get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE rag_consultas 
                        SET tiempo_respuesta_ms = %s, metodo_resolucion = %s 
                        WHERE id = %s
                    """, (tiempo_respuesta, respuesta.metodo.value, consulta_id))

            # 8. Guardar en cache si es relevante
            if respuesta.confianza >= 0.8 and tipo_consulta in [TipoConsulta.FRECUENTE, TipoConsulta.HIBRIDA]:
                await self._guardar_cache(consulta.pregunta, respuesta)

            logger.info(f"Consulta procesada exitosamente en {tiempo_respuesta}ms")
            return respuesta, consulta_id

        except Exception as e:
            logger.error(f"Error procesando consulta: {str(e)}")
            tiempo_respuesta = int((time.time() - start_time) * 1000)
            
            # Respuesta de error
            respuesta_error = RespuestaRAG(
                texto=f"Lo siento, hubo un error procesando tu consulta: {str(e)}",
                fuentes=[],
                confianza=0.0,
                metodo=MetodoResolucion.LLM_GENERACION,
                tiempo_respuesta=tiempo_respuesta
            )
            
            return respuesta_error, consulta_id if 'consulta_id' in locals() else None

    async def _buscar_cache(self, pregunta: str) -> Optional[RespuestaRAG]:
        """Buscar respuesta en cache"""
        try:
            with self.get_db_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("SELECT * FROM buscar_respuesta_cache(%s)", (pregunta,))
                    resultado = cur.fetchone()
                    
                    if resultado:
                        return RespuestaRAG(
                            texto=resultado['respuesta'],
                            fuentes=resultado['fuentes'] or [],
                            confianza=0.9,  # Cache tiene alta confianza
                            metodo=MetodoResolucion.CACHE,
                            tiempo_respuesta=0
                        )
            return None
        except Exception as e:
            logger.warning(f"Error buscando en cache: {str(e)}")
            return None

    async def _clasificar_consulta(self, pregunta: str) -> TipoConsulta:
        """Clasificar tipo de consulta usando la función SQL"""
        # Detectar preguntas conceptuales complejas que deben ir directamente a RAG
        pregunta_lower = pregunta.lower()
        
        # Preguntas sobre genocidio, conceptos complejos, análisis profundo
        conceptos_complejos = [
            'genocidio', 'genocida', 'exterminio', 'sistematico',
            'union patriotica', 'patriotica', 'up',
            'por que', 'porque', 'como', 'cuando', 'donde',
            'analisis', 'explicacion', 'razon', 'motivo',
            'contexto', 'trasfondo', 'antecedente',
            # NUEVO: hipótesis de investigación
            'hipotesis', 'hipótesis', 'lineas de investigacion', 'líneas de investigación',
            'explicaciones plausibles', 'posibles explicaciones'
        ]
        
        if any(concepto in pregunta_lower for concepto in conceptos_complejos):
            logger.info("Pregunta conceptual compleja detectada - dirigiendo a RAG")
            return TipoConsulta.RAG
            
        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT clasificar_tipo_consulta(%s)", (pregunta,))
                    tipo = cur.fetchone()[0]
                    return TipoConsulta(tipo)
        except Exception as e:
            logger.warning(f"Error clasificando consulta: {str(e)}")
            return TipoConsulta.HIBRIDA

    async def _resolver_consulta_frecuente(self, pregunta: str) -> RespuestaRAG:
        """Resolver consulta usando vistas materializadas"""
        logger.info("Resolviendo consulta frecuente con vistas materializadas")
        
        # Detectar qué vista materializada usar
        pregunta_lower = pregunta.lower()
        # Normalizar acentos para mejor detección
        import unicodedata
        pregunta_norm = unicodedata.normalize('NFD', pregunta_lower)
        pregunta_norm = ''.join(c for c in pregunta_norm if unicodedata.category(c) != 'Mn')
        
        if any(palabra in pregunta_norm for palabra in ['dashboard', 'estadisticas', 'metricas', 'resumen']):
            return await self._generar_dashboard()
        elif any(palabra in pregunta_norm for palabra in ['departamento', 'geografia', 'lugar', 'territorial']):
            return await self._generar_analisis_geografico(pregunta)
        elif any(palabra in pregunta_norm for palabra in ['top', 'principales', 'mayores', 'mas mencionado']):
            return await self._generar_top_entidades(pregunta)
        elif any(palabra in pregunta_norm for palabra in ['cuantas', 'cuantos', 'cantidad', 'numero', 'total']):
            return await self._generar_conteo_entidades(pregunta)
        else:
            # Fallback a búsqueda RAG directa (evitar recursión con _resolver_consulta_hibrida)
            return await self._resolver_consulta_rag(pregunta)

    async def _generar_dashboard(self) -> RespuestaRAG:
        """Generar respuesta del dashboard principal"""
        try:
            with self.get_db_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("SELECT get_dashboard_metricas() as metricas")
                    resultado = cur.fetchone()
                    
                    metricas = resultado['metricas']
                    
                    # Formatear respuesta
                    texto = f"""📊 **Dashboard Ejecutivo - Sistema de Documentos Judiciales**

🎯 **Estado del Procesamiento:**
• Documentos procesados: {metricas['total_documentos']:,} ({metricas['progreso_procesamiento']}%)
• Progreso: {metricas['progreso_procesamiento']:.1f}% de 11,446 documentos totales

👥 **Entidades Identificadas:**
• Personas: {metricas['total_personas']:,} individuos únicos
• Organizaciones: {metricas['total_organizaciones']:,} entidades organizacionales  
• Lugares: {metricas['total_lugares']:,} ubicaciones georreferenciadas
• Casos únicos: {metricas['casos_unicos']:,} NUC procesados

🏛️ **Clasificación por Tipo:**
• Víctimas: {metricas['entidades_por_tipo']['victimas']:,}
• Victimarios: {metricas['entidades_por_tipo']['victimarios']:,}
• Defensa: {metricas['entidades_por_tipo']['defensa']:,}
• Fiscales: {metricas['entidades_por_tipo']['fiscales']:,}
• Fuerzas legítimas: {metricas['entidades_por_tipo']['fuerzas_legitimas']:,}
• Fuerzas ilegales: {metricas['entidades_por_tipo']['fuerzas_ilegales']:,}

⏰ **Última actualización:** {metricas['ultima_actualizacion']}

*Datos generados automáticamente desde vistas materializadas optimizadas*"""

                    return RespuestaRAG(
                        texto=texto,
                        fuentes=[{"tipo": "vista_materializada", "nombre": "mv_dashboard_principal"}],
                        confianza=0.95,
                        metodo=MetodoResolucion.VISTA_MATERIALIZADA,
                        tiempo_respuesta=0,
                        datos_estructurados=metricas
                    )
        except Exception as e:
            logger.error(f"Error generando dashboard: {str(e)}")
            raise

    async def _generar_analisis_geografico(self, pregunta: str) -> RespuestaRAG:
        """Generar análisis geográfico"""
        try:
            # Extraer departamento si se menciona
            departamento = None
            for palabra in pregunta.split():
                if len(palabra) > 4 and palabra.lower() not in ['departamento', 'geografia']:
                    departamento = palabra
                    break
            
            with self.get_db_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    if departamento:
                        cur.execute("SELECT * FROM get_analisis_geografico(%s) LIMIT 5", (departamento,))
                    else:
                        cur.execute("SELECT * FROM get_analisis_geografico() LIMIT 10")
                    
                    resultados = cur.fetchall()
                    
                    if not resultados:
                        texto = f"No se encontró información geográfica para '{departamento}'" if departamento else "No hay datos geográficos disponibles"
                        return RespuestaRAG(texto=texto, fuentes=[], confianza=0.3, metodo=MetodoResolucion.VISTA_MATERIALIZADA, tiempo_respuesta=0)
                    
                    # Formatear respuesta
                    texto = "🗺️ **Análisis Geográfico**\n\n"
                    
                    for i, resultado in enumerate(resultados, 1):
                        texto += f"**{i}. {resultado['departamento']}**\n"
                        texto += f"• Lugares específicos: {resultado['lugares_especificos']:,}\n"
                        texto += f"• Municipios afectados: {resultado['municipios_afectados']:,}\n"
                        texto += f"• Total menciones: {resultado['total_menciones']:,}\n"
                        texto += f"• Casos involucrados: {resultado['casos_involucrados']:,}\n"
                        
                        if resultado['top_lugares']:
                            top_lugares = resultado['top_lugares'][:3]
                            lugares_str = ", ".join([f"{lugar['lugar']} ({lugar['menciones']})" for lugar in top_lugares])
                            texto += f"• Principales lugares: {lugares_str}\n"
                        
                        texto += "\n"
                    
                    texto += "*Análisis basado en vistas materializadas optimizadas*"
                    
                    return RespuestaRAG(
                        texto=texto,
                        fuentes=[{"tipo": "vista_materializada", "nombre": "mv_analisis_geografico"}],
                        confianza=0.9,
                        metodo=MetodoResolucion.VISTA_MATERIALIZADA,
                        tiempo_respuesta=0,
                        datos_estructurados={"resultados": [dict(r) for r in resultados]}
                    )
        except Exception as e:
            logger.error(f"Error en análisis geográfico: {str(e)}")
            raise

    async def _generar_top_entidades(self, pregunta: str) -> RespuestaRAG:
        """Generar top de entidades"""
        try:
            # Detectar qué tipo de entidad busca
            pregunta_lower = pregunta.lower()
            
            if 'persona' in pregunta_lower or 'gente' in pregunta_lower:
                tipo_filtro = 'persona'
            elif 'organizacion' in pregunta_lower or 'grupo' in pregunta_lower:
                tipo_filtro = 'organizacion'
            elif 'lugar' in pregunta_lower or 'sitio' in pregunta_lower:
                tipo_filtro = 'lugar'
            else:
                tipo_filtro = None
            
            with self.get_db_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    if tipo_filtro:
                        cur.execute("""
                            SELECT * FROM mv_top_entidades 
                            WHERE tipo_entidad = %s 
                            ORDER BY frecuencia DESC 
                            LIMIT 15
                        """, (tipo_filtro,))
                    else:
                        cur.execute("""
                            SELECT * FROM mv_top_entidades 
                            ORDER BY frecuencia DESC 
                            LIMIT 20
                        """)
                    
                    resultados = cur.fetchall()
                    
                    if not resultados:
                        return RespuestaRAG(
                            texto="No se encontraron entidades frecuentes para mostrar",
                            fuentes=[], confianza=0.3,
                            metodo=MetodoResolucion.VISTA_MATERIALIZADA, tiempo_respuesta=0
                        )
                    
                    # Agrupar por tipo
                    por_tipo = {}
                    for resultado in resultados:
                        tipo = resultado['tipo_entidad']
                        if tipo not in por_tipo:
                            por_tipo[tipo] = []
                        por_tipo[tipo].append(resultado)
                    
                    # Formatear respuesta
                    texto = "🏆 **Entidades Más Mencionadas**\n\n"
                    
                    iconos = {
                        'persona': '👤',
                        'organizacion': '🏛️',
                        'lugar': '📍'
                    }
                    
                    for tipo, entidades in por_tipo.items():
                        icono = iconos.get(tipo, '📋')
                        texto += f"{icono} **{tipo.title()}s:**\n"
                        
                        for i, entidad in enumerate(entidades[:10], 1):
                            texto += f"{i}. {entidad['entidad']} ({entidad['frecuencia']} menciones)\n"
                        
                        texto += "\n"
                    
                    texto += "*Basado en análisis de frecuencia de menciones*"
                    
                    return RespuestaRAG(
                        texto=texto,
                        fuentes=[{"tipo": "vista_materializada", "nombre": "mv_top_entidades"}],
                        confianza=0.9,
                        metodo=MetodoResolucion.VISTA_MATERIALIZADA,
                        tiempo_respuesta=0,
                        datos_estructurados={"entidades_por_tipo": por_tipo}
                    )
        except Exception as e:
            logger.error(f"Error generando top entidades: {str(e)}")
            raise

    async def _generar_conteo_entidades(self, pregunta: str) -> RespuestaRAG:
        """Generar conteo específico de entidades"""
        try:
            # Normalizar pregunta quitando acentos
            import unicodedata
            pregunta_lower = pregunta.lower()
            pregunta_norm = unicodedata.normalize('NFD', pregunta_lower)
            pregunta_norm = ''.join(c for c in pregunta_norm if unicodedata.category(c) != 'Mn')
            
            with self.get_db_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    
                    # Detectar qué tipo de conteo se requiere
                    if 'victima' in pregunta_norm:
                        cur.execute("""
                            SELECT COUNT(DISTINCT nombre) as total 
                            FROM personas 
                            WHERE tipo ILIKE '%victima%' AND tipo NOT ILIKE '%victimario%'
                        """)
                        resultado = cur.fetchone()
                        entidad = "víctimas únicas"
                        total = resultado['total']
                        
                        # Desglose adicional
                        cur.execute("""
                            SELECT tipo, COUNT(DISTINCT nombre) as cantidad
                            FROM personas 
                            WHERE tipo ILIKE '%victima%' AND tipo NOT ILIKE '%victimario%'
                            GROUP BY tipo
                            ORDER BY cantidad DESC
                        """)
                        desglose = cur.fetchall()
                        
                    elif 'victimario' in pregunta_norm:
                        cur.execute("""
                            SELECT COUNT(DISTINCT nombre) as total 
                            FROM personas 
                            WHERE tipo ILIKE '%victimario%'
                        """)
                        resultado = cur.fetchone()
                        entidad = "victimarios únicos"
                        total = resultado['total']
                        
                        cur.execute("""
                            SELECT tipo, COUNT(DISTINCT nombre) as cantidad
                            FROM personas 
                            WHERE tipo ILIKE '%victimario%'
                            GROUP BY tipo
                            ORDER BY cantidad DESC
                        """)
                        desglose = cur.fetchall()
                        
                    elif 'persona' in pregunta_norm:
                        cur.execute("SELECT COUNT(DISTINCT nombre) as total FROM personas")
                        resultado = cur.fetchone()
                        entidad = "personas únicas"
                        total = resultado['total']
                        
                        cur.execute("""
                            SELECT tipo, COUNT(DISTINCT nombre) as cantidad
                            FROM personas 
                            GROUP BY tipo
                            ORDER BY cantidad DESC
                            LIMIT 10
                        """)
                        desglose = cur.fetchall()
                        
                    elif 'organizacion' in pregunta_norm:
                        cur.execute("SELECT COUNT(DISTINCT nombre) as total FROM organizaciones")
                        resultado = cur.fetchone()
                        entidad = "organizaciones únicas"
                        total = resultado['total']
                        
                        cur.execute("""
                            SELECT tipo, COUNT(DISTINCT nombre) as cantidad
                            FROM organizaciones 
                            GROUP BY tipo
                            ORDER BY cantidad DESC
                            LIMIT 10
                        """)
                        desglose = cur.fetchall()
                        
                    elif 'documento' in pregunta_norm:
                        cur.execute("SELECT COUNT(*) as total FROM documentos")
                        resultado = cur.fetchone()
                        entidad = "documentos"
                        total = resultado['total']
                        
                        cur.execute("""
                            SELECT 
                                DATE_PART('year', fecha_proceso) as año,
                                COUNT(*) as cantidad
                            FROM documentos 
                            WHERE fecha_proceso IS NOT NULL
                            GROUP BY DATE_PART('year', fecha_proceso)
                            ORDER BY año DESC
                            LIMIT 5
                        """)
                        desglose = cur.fetchall()
                        
                    else:
                        # Conteo general
                        cur.execute("""
                            SELECT 
                                'documentos' as tipo, (SELECT COUNT(*) FROM documentos) as total
                            UNION ALL
                            SELECT 
                                'personas únicas' as tipo, (SELECT COUNT(DISTINCT nombre) FROM personas) as total
                            UNION ALL
                            SELECT 
                                'organizaciones únicas' as tipo, (SELECT COUNT(DISTINCT nombre) FROM organizaciones) as total
                        """)
                        totales = cur.fetchall()
                        
                        texto = "📊 **Resumen de Entidades en el Sistema**\n\n"
                        for item in totales:
                            texto += f"• {item['tipo'].title()}: **{item['total']:,}**\n"
                        
                        texto += f"\n*Datos actualizados automáticamente desde la base de datos*"
                        
                        return RespuestaRAG(
                            texto=texto,
                            fuentes=[{"tipo": "consulta_directa", "tabla": "conteo_general"}],
                            confianza=0.99,
                            metodo=MetodoResolucion.VISTA_MATERIALIZADA,
                            tiempo_respuesta=0,
                            datos_estructurados={"totales": [dict(t) for t in totales]}
                        )
                    
                    # Formatear respuesta específica
                    texto = f"📊 **Total de {entidad.title()}**: **{total:,}**\n\n"
                    
                    if desglose:
                        texto += f"📋 **Desglose por tipo:**\n"
                        for item in desglose[:8]:  # Top 8
                            tipo_nombre = item.get('tipo', item.get('año', 'N/A'))
                            cantidad = item.get('cantidad', 0)
                            texto += f"• {tipo_nombre}: {cantidad:,}\n"
                        
                        if len(desglose) > 8:
                            texto += f"• ... y {len(desglose) - 8} tipos más\n"
                    
                    texto += f"\n*Consulta optimizada ejecutada directamente en la base de datos*"
                    
                    return RespuestaRAG(
                        texto=texto,
                        fuentes=[{"tipo": "consulta_directa", "tabla": "conteo_" + entidad}],
                        confianza=0.99,
                        metodo=MetodoResolucion.VISTA_MATERIALIZADA,
                        tiempo_respuesta=0,
                        datos_estructurados={
                            "total": convert_db_types(total),
                            "entidad": entidad,
                            "desglose": [convert_db_types(dict(d)) for d in desglose]
                        }
                    )
                    
        except Exception as e:
            logger.error(f"Error generando conteo de entidades: {str(e)}")
            raise

    async def _resolver_consulta_rag(self, pregunta: str) -> RespuestaRAG:
        """Resolver consulta compleja usando RAG con Azure Search + LLM"""
        logger.info("Resolviendo consulta compleja con RAG + LLM")
        
        try:
            # 1. Buscar primero en Azure Search (vectorizado/semántico)
            contexto_azure = []
            try:
                azure_search = AzureSearchVectorizado()
                chunks_azure = await azure_search.buscar_semanticamente(pregunta, top_k=5)
                
                if chunks_azure:
                    logger.info(f"Azure Search encontró {len(chunks_azure)} chunks relevantes")
                    for chunk in chunks_azure:
                        # Extraer metadatos de ubicación
                        pagina = chunk.metadata.get('pagina', 'N/A') if hasattr(chunk, 'metadata') else 'N/A'
                        parrafo = chunk.metadata.get('parrafo', 'N/A') if hasattr(chunk, 'metadata') else 'N/A'
                        
                        contexto_azure.append({
                            'texto': chunk.contenido if hasattr(chunk, 'contenido') else str(chunk),
                            'fuente': f"Archivo: {chunk.nombre_archivo if hasattr(chunk, 'nombre_archivo') else 'N/A'} - {chunk.tipo_documental if hasattr(chunk, 'tipo_documental') else 'Documento'}",
                            'relevancia': chunk.score if hasattr(chunk, 'score') else 0.0,
                            'tipo': 'azure_search',
                            'analisis': chunk.analisis if hasattr(chunk, 'analisis') else '',
                            'pagina': pagina,
                            'parrafo': parrafo,
                            'nombre_archivo': chunk.nombre_archivo if hasattr(chunk, 'nombre_archivo') else 'N/A',
                            'expediente_nuc': chunk.expediente_nuc if hasattr(chunk, 'expediente_nuc') else 'N/A',
                            'tipo_documental': chunk.tipo_documental if hasattr(chunk, 'tipo_documental') else 'N/A'
                        })
                else:
                    logger.warning("Azure Search no encontró chunks relevantes")
            except Exception as e:
                logger.warning(f"Error con Azure Search: {str(e)}")
            
            # 2. Si Azure Search no encuentra suficiente, buscar en PostgreSQL
            contexto_sql = []
            if len(contexto_azure) < 3:
                logger.info("Complementando con búsqueda SQL")
                terminos_clave = await self._extraer_terminos_clave(pregunta)
                resultado_sql = await self._buscar_contexto_sql(terminos_clave, pregunta)
                
                # Convertir resultado SQL a formato de lista
                if resultado_sql and isinstance(resultado_sql, dict):
                    # Extraer información relevante del resultado SQL
                    for key, value in resultado_sql.items():
                        if isinstance(value, list) and value:
                            for item in value[:3]:  # Máximo 3 items por categoría
                                contexto_sql.append({
                                    'texto': str(item),
                                    'fuente': f"PostgreSQL - {key}",
                                    'relevancia': 0.5,
                                    'tipo': 'sql_search'
                                })
            
            # 3. Combinar contextos
            contexto_completo = contexto_azure + contexto_sql
            
            # 4. Generar respuesta con LLM
            respuesta_llm = await self._generar_respuesta_llm(pregunta, contexto_completo)
            
            return respuesta_llm
            
        except Exception as e:
            logger.error(f"Error en consulta RAG: {str(e)}")
            raise

    async def _extraer_terminos_clave(self, pregunta: str) -> List[str]:
        """Extraer términos clave de la pregunta usando técnicas simples"""
        # Implementación simple - en producción se podría usar NLP más avanzado
        palabras_clave = []
        
        # Buscar nombres propios (palabras que empiezan con mayúscula)
        import re
        nombres_propios = re.findall(r'\b[A-Z][a-záéíóúñ]+\b', pregunta)
        palabras_clave.extend(nombres_propios)
        
        # Buscar siglas
        siglas = re.findall(r'\b[A-Z]{2,}\b', pregunta)
        palabras_clave.extend(siglas)
        
        # Palabras importantes (sustantivos comunes en el dominio)
        palabras_importantes = [
            'victima', 'victimas', 'victimario', 'victimarios', 'defensa',
            'fiscal', 'juez', 'organizacion', 'grupo', 'ejercito', 'policia',
            'lugar', 'municipio', 'departamento', 'caso', 'documento'
        ]
        
        for palabra in palabras_importantes:
            if palabra in pregunta.lower():
                palabras_clave.append(palabra)
        
        return list(set(palabras_clave))  # Eliminar duplicados

    async def _buscar_contexto_sql(self, terminos_clave: List[str], pregunta_original: str) -> Dict[str, Any]:
        """Buscar contexto relevante usando las funciones RAG de SQL"""
        contexto = {
            'personas': [],
            'organizaciones': [],
            'lugares': [],
            'total_fuentes': 0
        }
        
        try:
            with self.get_db_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    
                    # Buscar personas relevantes
                    if terminos_clave:
                        cur.execute("""
                            SELECT * FROM rag_buscar_contexto_personas(%s::text[], 10)
                        """, (terminos_clave,))
                        contexto['personas'] = [dict(row) for row in cur.fetchall()]
                    
                    # Buscar organizaciones relevantes
                    if terminos_clave:
                        cur.execute("""
                            SELECT * FROM rag_buscar_contexto_organizaciones(%s::text[], 10)
                        """, (terminos_clave,))
                        contexto['organizaciones'] = [dict(row) for row in cur.fetchall()]
                    
                    # Buscar lugares relevantes
                    if terminos_clave:
                        cur.execute("""
                            SELECT * FROM rag_buscar_contexto_geografico(%s::text[], 10)
                        """, (terminos_clave,))
                        contexto['lugares'] = [dict(row) for row in cur.fetchall()]
            
            contexto['total_fuentes'] = (
                len(contexto['personas']) + 
                len(contexto['organizaciones']) + 
                len(contexto['lugares'])
            )
            
            logger.info(f"Contexto encontrado: {contexto['total_fuentes']} fuentes")
            return contexto
            
        except Exception as e:
            logger.warning(f"Error buscando contexto SQL: {str(e)}")
            return contexto

    async def _generar_respuesta_llm(self, pregunta: str, contexto) -> RespuestaRAG:
        """Generar respuesta usando Azure OpenAI"""
        try:
            # Manejar tanto listas como diccionarios
            if isinstance(contexto, list):
                contexto_str = self._formatear_contexto_lista_para_llm(contexto)
            else:
                contexto_str = self._formatear_contexto_para_llm(contexto)
            
            pregunta_lower = pregunta.lower()
            if any(k in pregunta_lower for k in ['hipótesis', 'hipotesis', 'líneas de investigación', 'lineas de investigacion', 'posibles explicaciones', 'explicaciones plausibles']):
                # Modo generación de hipótesis de investigación
                system_prompt = """Eres un analista legal senior de la Fiscalía.
Tu tarea es CONSTRUIR HIPÓTESIS DE INVESTIGACIÓN basándote únicamente en el contexto proporcionado, con máxima trazabilidad.

REGLAS:
1. Propón 3 a 5 hipótesis claras, contrastables y accionables.
2. Cada hipótesis debe incluir: descripción, evidencias de soporte [CITA-X], supuestos, señales en contra, cómo refutar/confirmar, próximos pasos.
3. Usa lenguaje probabilístico (posiblemente, es plausible, podría indicar), evita afirmaciones categóricas.
4. Mantén rigor legal y referencia toda evidencia con [CITA-X]."""

                user_prompt = f"""PREGUNTA: {pregunta}

CONTEXTO DISPONIBLE:
{contexto_str}

Devuelve en Markdown:

## Hipótesis de Investigación

1) [Título breve]
   - Descripción: ...
   - Evidencias de soporte: ... [CITA-1], [CITA-2]
   - Supuestos: ...
   - Señales en contra: ...
   - Cómo refutar/confirmar: ...
   - Próximos pasos (acciones): ...

2) ... (3 a 5 hipótesis en total)

Al final incluye:
REFERENCIAS:
[CITA-X] Fuente y localización (archivo/página/párrafo)"""
            else:
                # Modo respuesta estándar con citas
                system_prompt = """Eres un asistente legal especializado en análisis de documentos judiciales del caso UP (Unión Patriótica).
Tu tarea es responder preguntas basándote únicamente en el contexto proporcionado con MÁXIMA TRAZABILIDAD.

INSTRUCCIONES OBLIGATORIAS PARA CITAS LEGALES:
1. CADA afirmación DEBE estar respaldada con su cita exacta usando el formato [CITA-X]
2. Responde SOLO con información del contexto proporcionado
3. Incluye citas textuales entrecomilladas cuando sea relevante
4. Si no hay información suficiente para una afirmación, dilo claramente
5. Mantén el rigor legal y la precisión documental
6. Estructura la respuesta de manera profesional y clara

FORMATO DE CITAS REQUERIDO:
- Después de cada afirmación: [CITA-X] donde X es el número de referencia
- Para citas textuales: "texto exacto" [CITA-X]
- Ejemplo: La Unión Patriótica fue objeto de persecución sistemática [CITA-1].

RECUERDA: Este es un sistema legal que requiere trazabilidad máxima. Cada dato debe ser verificable."""

                user_prompt = f"""PREGUNTA: {pregunta}

CONTEXTO DISPONIBLE:
{contexto_str}

Responde a la pregunta basándote únicamente en el contexto proporcionado.

ESTRUCTURA REQUERIDA DE LA RESPUESTA:
1. Respuesta principal con citas [CITA-X] después de cada afirmación
2. Al final, incluye una sección "REFERENCIAS:" listando todas las citas usadas

Ejemplo de formato:
La Unión Patriótica fue perseguida sistemáticamente [CITA-1]. Esto constituye genocidio según la jurisprudencia [CITA-2].

REFERENCIAS:
[CITA-1] Archivo: sentencia_123.pdf, Página XX, Párrafo XX
[CITA-2] Archivo: auto_456.pdf, Página YY, Párrafo YY"""

            # Llamada a Azure OpenAI
            start_time = time.time()
            
            response = self.azure_client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            tiempo_llm = int((time.time() - start_time) * 1000)
            
            respuesta_texto = response.choices[0].message.content
            
            # Calcular métricas
            tokens_prompt = response.usage.prompt_tokens
            tokens_respuesta = response.usage.completion_tokens
            costo_estimado = (tokens_prompt * 0.000150 + tokens_respuesta * 0.000600) / 1000  # Precios GPT-4o-mini
            
            # Calcular confianza basada en cantidad de contexto
            if isinstance(contexto, list):
                total_fuentes = len(contexto)
                azure_chunks = [item for item in contexto if item.get('tipo') == 'azure_search']
                if azure_chunks:
                    confianza = min(0.9, 0.6 + (len(azure_chunks) * 0.05))  # Base más alta para Azure Search
                else:
                    confianza = min(0.9, 0.5 + (total_fuentes * 0.05))
            elif 'chunks_azure' in contexto:
                total_fuentes = len(contexto['chunks_azure'])
                confianza = min(0.9, 0.6 + (total_fuentes * 0.05))  # Base más alta para Azure Search
            else:
                total_fuentes = contexto.get('total_fuentes', 0)
                confianza = min(0.9, 0.5 + (total_fuentes * 0.05))
            
            # Preparar fuentes
            fuentes = []
            
            # Manejar fuentes de lista (nuevo formato)
            if isinstance(contexto, list):
                for i, item in enumerate(contexto[:5], 1):  # Máximo 5 fuentes
                    if isinstance(item, dict):
                        fuente_info = {
                            'cita': f'CITA-{i}',
                            'nombre_archivo': item.get('nombre_archivo', 'N/A'),
                            'expediente': item.get('expediente_nuc', 'N/A'),
                            'tipo_documento': item.get('tipo_documental', 'N/A'),
                            'pagina': item.get('pagina', 'N/A'),
                            'parrafo': item.get('parrafo', 'N/A'),
                            'relevancia': item.get('relevancia', 0.0),
                            'texto_fuente': item.get('texto', ''),  # Guardar texto completo para mostrar en UI
                            'texto_resumen': item.get('texto', '')[:200] + '...' if len(item.get('texto', '')) > 200 else item.get('texto', '')
                        }
                        fuentes.append(fuente_info)
            # Manejar fuentes de Azure Search (formato anterior)
            elif 'chunks_azure' in contexto:
                for chunk in contexto['chunks_azure'][:3]:
                    fuentes.append({
                        'tipo': 'documento_vectorizado',
                        'expediente': getattr(chunk, 'expediente_nuc', 'N/A'),
                        'tipo_documental': getattr(chunk, 'tipo_documental', 'N/A'),
                        'relevancia': getattr(chunk, 'score', 0)
                    })
            else:
                # Manejar fuentes tradicionales SQL (contexto como diccionario)
                if isinstance(contexto, dict):
                    for categoria, items in contexto.items():
                        if categoria != 'total_fuentes' and items:
                            for item in items[:3]:  # Primeras 3 de cada categoría
                                if isinstance(item, dict):
                                    fuentes.append({
                                        'tipo': categoria,
                                        'entidad': item.get('persona') or item.get('organizacion') or item.get('lugar', 'N/A'),
                                        'relevancia': item.get('score_relevancia', 0)
                                    })
            
            metadatos = {
                'model': self.deployment_name,
                'tokens_prompt': tokens_prompt,
                'tokens_respuesta': tokens_respuesta,
                'costo_estimado': costo_estimado,
                'tiempo_llm_ms': tiempo_llm,
                'temperatura': 0.3
            }
            
            return RespuestaRAG(
                texto=respuesta_texto,
                fuentes=fuentes,
                confianza=confianza,
                metodo=MetodoResolucion.LLM_GENERACION,
                tiempo_respuesta=tiempo_llm,
                metadatos_llm=metadatos
            )
            
        except Exception as e:
            logger.error(f"Error generando respuesta LLM: {str(e)}")
            raise

    def _formatear_contexto_para_llm(self, contexto: Dict[str, Any]) -> str:
        """Formatear contexto para enviar al LLM"""
        partes = []
        
        # Manejar chunks de Azure Search
        if 'chunks_azure' in contexto:
            partes.append("DOCUMENTOS RELEVANTES ENCONTRADOS:")
            for i, chunk in enumerate(contexto['chunks_azure'][:5], 1):
                expediente = getattr(chunk, 'expediente_nuc', 'N/A')
                tipo_doc = getattr(chunk, 'tipo_documental', 'N/A')
                contenido = getattr(chunk, 'contenido', '')
                analisis = getattr(chunk, 'analisis', '')
                
                partes.append(f"\n{i}. EXPEDIENTE: {expediente}")
                partes.append(f"   TIPO: {tipo_doc}")
                if contenido:
                    partes.append(f"   CONTENIDO: {contenido[:300]}...")
                if analisis:
                    partes.append(f"   ANÁLISIS: {analisis[:300]}...")
            partes.append("")
        
        # Manejar contexto tradicional SQL
        if contexto.get('personas'):
            partes.append("PERSONAS RELEVANTES:")
            for persona in contexto['personas'][:5]:
                partes.append(f"- {persona['persona']} ({persona['tipo']}): {persona['contexto'][:200]}...")
            partes.append("")
        
        if contexto.get('organizaciones'):
            partes.append("ORGANIZACIONES RELEVANTES:")
            for org in contexto['organizaciones'][:5]:
                partes.append(f"- {org['organizacion']} ({org['tipo']}): {org['contexto'][:200]}...")
            partes.append("")
        
        if contexto.get('lugares'):
            partes.append("LUGARES RELEVANTES:")
            for lugar in contexto['lugares'][:5]:
                partes.append(f"- {lugar['lugar']} ({lugar['departamento']}): {lugar['contexto'][:200]}...")
            partes.append("")
        
        return "\n".join(partes)

    def _formatear_contexto_lista_para_llm(self, contexto_lista) -> str:
        """Formatear lista de contexto para enviar al LLM con citas detalladas"""
        partes = []
        
        if not contexto_lista:
            return "No se encontró información relevante en los documentos."
        
        partes.append("INFORMACIÓN ENCONTRADA EN LOS DOCUMENTOS JUDICIALES:")
        partes.append("INSTRUCCIONES PARA CITAS: Cada afirmación DEBE incluir la cita exacta con formato [CITA-X] donde X es el número de referencia.")
        partes.append("")
        
        for i, item in enumerate(contexto_lista[:10], 1):  # Máximo 10 items
            if isinstance(item, dict):
                # Extraer información de ubicación
                pagina = item.get('pagina', 'N/A')
                parrafo = item.get('parrafo', 'N/A')
                nombre_archivo = item.get('nombre_archivo', 'N/A')
                tipo_doc = item.get('tipo_documental', 'N/A')
                expediente = item.get('expediente_nuc', 'N/A')
                
                partes.append(f"[CITA-{i}]")
                partes.append(f"ARCHIVO: {nombre_archivo}")
                partes.append(f"TIPO DOCUMENTO: {tipo_doc}")
                partes.append(f"EXPEDIENTE NUC: {expediente}")
                partes.append(f"UBICACIÓN: Página {pagina}, Párrafo {parrafo}")
                partes.append(f"RELEVANCIA: {item.get('relevancia', 0.0):.2f}")
                partes.append(f"TEXTO EXACTO:")
                
                texto = item.get('texto', '')
                if texto:
                    # Mantener el texto completo para citas exactas
                    partes.append(f'"{texto}"')
                
                analisis = item.get('analisis', '')
                if analisis:
                    partes.append(f"RESUMEN DEL ANÁLISIS: {analisis}")
                
                partes.append("")
            else:
                partes.append(f"[CITA-{i}] {str(item)[:500]}...")
                partes.append("")
        
        partes.append("IMPORTANTE: En tu respuesta, SIEMPRE incluye las citas usando el formato [CITA-X] después de cada afirmación.")
        partes.append("Ejemplo: 'La Unión Patriótica fue perseguida sistemáticamente [CITA-1] y esto constituye genocidio según la jurisprudencia [CITA-2].'")
        
        return "\n".join(partes)

    async def _resolver_consulta_hibrida(self, pregunta: str) -> RespuestaRAG:
        """Resolver consulta híbrida combinando vistas materializadas y RAG"""
        logger.info("Resolviendo consulta híbrida")
        
        # Detectar si la pregunta es del tipo que se puede resolver con vistas materializadas
        pregunta_lower = pregunta.lower()
        import unicodedata
        pregunta_norm = unicodedata.normalize('NFD', pregunta_lower)
        pregunta_norm = ''.join(c for c in pregunta_norm if unicodedata.category(c) != 'Mn')
        
        # Si es una consulta específica para vistas materializadas, probar primero
        if any(palabra in pregunta_norm for palabra in ['dashboard', 'estadisticas', 'metricas', 'resumen', 'departamento', 'geografia', 'lugar', 'territorial', 'top', 'principales', 'mayores', 'mas mencionado', 'cuantas', 'cuantos', 'cantidad', 'numero', 'total']):
            try:
                logger.info("Intentando resolución con vistas materializadas en híbrida")
                if any(palabra in pregunta_norm for palabra in ['dashboard', 'estadisticas', 'metricas', 'resumen']):
                    respuesta_vm = await self._generar_dashboard()
                elif any(palabra in pregunta_norm for palabra in ['departamento', 'geografia', 'lugar', 'territorial']):
                    respuesta_vm = await self._generar_analisis_geografico(pregunta)
                elif any(palabra in pregunta_norm for palabra in ['top', 'principales', 'mayores', 'mas mencionado']):
                    respuesta_vm = await self._generar_top_entidades(pregunta)
                elif any(palabra in pregunta_norm for palabra in ['cuantas', 'cuantos', 'cantidad', 'numero', 'total']):
                    respuesta_vm = await self._generar_conteo_entidades(pregunta)
                else:
                    respuesta_vm = None
                
                if respuesta_vm and respuesta_vm.confianza >= 0.7:
                    return respuesta_vm
            except Exception as e:
                logger.warning(f"Error en vistas materializadas híbrida: {str(e)}")
        
        # Si no funciona o no es del tipo apropiado, usar RAG
        return await self._resolver_consulta_rag(pregunta)

    async def _guardar_cache(self, pregunta: str, respuesta: RespuestaRAG):
        """Guardar respuesta en cache"""
        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT guardar_respuesta_cache(%s, %s, %s)
                    """, (pregunta, respuesta.texto, json.dumps(convert_db_types(respuesta.fuentes))))
                    logger.info("Respuesta guardada en cache")
        except Exception as e:
            logger.warning(f"Error guardando en cache: {str(e)}")

    async def registrar_feedback(self, consulta_id: int, respuesta_id: int, feedback: FeedbackRAG):
        """Registrar feedback del usuario"""
        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT registrar_feedback_rag(%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        consulta_id, respuesta_id, feedback.calificacion,
                        feedback.comentario, json.dumps(convert_db_types(feedback.aspectos)) if feedback.aspectos else None,
                        feedback.respuesta_esperada, None
                    ))
                    
                    feedback_id = cur.fetchone()[0]
                    logger.info(f"Feedback registrado con ID: {feedback_id}")
                    return feedback_id
        except Exception as e:
            logger.error(f"Error registrando feedback: {str(e)}")
            raise

    async def obtener_estadisticas_mejora_continua(self, dias: int = 30) -> Dict[str, Any]:
        """Obtener estadísticas para mejora continua"""
        try:
            with self.get_db_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    # Reporte de mejora continua
                    cur.execute("SELECT * FROM generar_reporte_mejora_continua(%s)", (dias,))
                    reporte = [dict(row) for row in cur.fetchall()]
                    
                    # Preguntas a optimizar
                    cur.execute("SELECT * FROM detectar_preguntas_optimizar()")
                    preguntas_optimizar = [dict(row) for row in cur.fetchall()]
                    
                    return {
                        'reporte_mejora': reporte,
                        'preguntas_optimizar': preguntas_optimizar,
                        'fecha_analisis': datetime.now().isoformat()
                    }
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {str(e)}")
            raise


# Función principal para testing
async def main():
    """Función de prueba del sistema RAG"""
    sistema = SistemaRAGTrazable()
    
    # Ejemplo de consulta
    consulta = ConsultaRAG(
        usuario_id="test_user",
        pregunta="¿Cuáles son las estadísticas principales del caso?",
        ip_cliente="127.0.0.1"
    )
    
    respuesta, consulta_id = await sistema.procesar_consulta(consulta)
    
    print("=== RESPUESTA ===")
    print(respuesta.texto)
    print(f"\nConfianza: {respuesta.confianza}")
    print(f"Método: {respuesta.metodo.value}")
    print(f"Tiempo: {respuesta.tiempo_respuesta}ms")
    print(f"Fuentes: {len(respuesta.fuentes)}")
    
    # Ejemplo de feedback
    feedback = FeedbackRAG(
        calificacion=5,
        comentario="Excelente respuesta, muy completa",
        aspectos={"precision": 5, "relevancia": 5, "completitud": 4}
    )
    
    await sistema.registrar_feedback(consulta_id, 1, feedback)
    print("\nFeedback registrado")

# Función pública síncrona para integración fácil
def consulta_hibrida_sincrona(pregunta: str) -> Dict[str, Any]:
    """
    Función síncrona para facilitar integración con interfaces que no usan async
    Retorna respuesta RAG con trazabilidad completa de Azure Search
    """
    try:
        # Ejecutar la consulta usando asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def _ejecutar_consulta():
            try:
                # Cargar variables de entorno
                load_dotenv()
                load_dotenv('config/.env')
                
                # Usar directamente el Azure Search
                azure_search = AzureSearchVectorizado()
                chunks_azure = await azure_search.buscar_semanticamente(pregunta, top_k=5)
                
                # Formatear respuesta
                fuentes_formateadas = []
                if chunks_azure:
                    for i, chunk in enumerate(chunks_azure, 1):
                        # Los chunks vienen como objetos DocumentoChunk, no diccionarios
                        try:
                            # Extraer nombre de archivo más legible
                            nombre_archivo = chunk.nombre_archivo if hasattr(chunk, 'nombre_archivo') else 'N/A'
                            if nombre_archivo.endswith('.json'):
                                # Extraer información más descriptiva del nombre del archivo
                                partes = nombre_archivo.replace('.json', '').split('_')
                                if len(partes) >= 3:
                                    fecha = partes[0] if partes[0].isdigit() else 'S/F'
                                    tipo_doc = partes[1] if len(partes) > 1 else 'DOC'
                                    nombre_archivo = f"{tipo_doc}_{fecha}"
                            
                            # Limpiar y mejorar el contenido del chunk
                            contenido = chunk.contenido if hasattr(chunk, 'contenido') else ''
                            contenido_limpio = contenido.replace('\\n', ' ').replace('\\t', ' ')
                            
                            # Obtener metadatos
                            pagina = chunk.metadata.get('pagina', 'N/A') if hasattr(chunk, 'metadata') and chunk.metadata else 'N/A'
                            parrafo = chunk.metadata.get('parrafo', 'N/A') if hasattr(chunk, 'metadata') and chunk.metadata else 'N/A'
                            
                            fuentes_formateadas.append({
                                'archivo': nombre_archivo,
                                'contenido': contenido_limpio[:500] + '...' if len(contenido_limpio) > 500 else contenido_limpio,
                                'score': float(chunk.score if hasattr(chunk, 'score') else 0.0),
                                'pagina': pagina,
                                'parrafo': parrafo,
                                'tipo_documental': chunk.tipo_documental if hasattr(chunk, 'tipo_documental') else 'Documento Judicial',
                                'expediente_nuc': chunk.expediente_nuc if hasattr(chunk, 'expediente_nuc') else 'N/A',
                                'metadata': chunk.metadata if hasattr(chunk, 'metadata') else {},
                                'doc_ref': f"Doc {i}"  # Para las citas en el texto
                            })
                        except Exception as e:
                            logging.error(f"Error procesando chunk {i}: {e}")
                            # Fallback para chunks con estructura inesperada
                            fuentes_formateadas.append({
                                'archivo': f'Documento {i}',
                                'contenido': str(chunk)[:200] + '...',
                                'score': 0.0,
                                'pagina': 'N/A',
                                'parrafo': 'N/A',
                                'tipo_documental': 'Documento',
                                'expediente_nuc': 'N/A',
                                'metadata': {},
                                'doc_ref': f"Doc {i}"
                            })
                
                # Generar respuesta usando OpenAI si hay fuentes
                if fuentes_formateadas:
                    import httpx
                    from openai import AzureOpenAI
                    
                    http_client = httpx.Client(timeout=30.0)
                    azure_client = AzureOpenAI(
                        api_key=os.getenv('AZURE_OPENAI_API_KEY'),
                        api_version=os.getenv('AZURE_OPENAI_VERSION', '2024-12-01-preview'),
                        azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
                        http_client=http_client
                    )
                    
                    # Crear contexto para la respuesta con referencias numeradas
                    contexto_chunks = '\n\n'.join([
                        f"[Doc {i+1}] **{f['tipo_documental']}** - {f['archivo']}\n"
                        f"**Ubicación:** Página {f['pagina']}, Párrafo {f['parrafo']} | **Expediente:** {f['expediente_nuc']}\n"
                        f"**Relevancia:** {f['score']:.3f}\n"
                        f"**Contenido:** {f['contenido']}\n"
                        f"{'='*50}"
                        for i, f in enumerate(fuentes_formateadas[:5])
                    ])
                    
                    prompt = f"""Eres un experto jurista especializado en derechos humanos y derecho penal internacional. 

Responde la siguiente consulta sobre el genocidio de la Unión Patriótica basándote EXCLUSIVAMENTE en la información de los documentos judiciales proporcionados.

**Consulta:** {pregunta}

**Contexto de documentos judiciales:**
{contexto_chunks}

INSTRUCCIONES IMPORTANTES:
1. Proporciona una respuesta detallada y jurídicamente fundamentada
2. INCLUYE CITAS ESPECÍFICAS en el texto usando el formato [Doc 1], [Doc 2], etc.
3. Cada afirmación debe estar respaldada por referencias a los documentos
4. Incluye los elementos constitutivos del genocidio según el derecho internacional
5. Explica cómo se configuran estos elementos en el caso de la Unión Patriótica
6. Menciona reconocimiento jurisprudencial cuando esté en los documentos
7. La respuesta debe ser completa (mínimo 800 palabras) y bien estructurada

FORMATO DE CITAS: Usa [Doc 1], [Doc 2], [Doc 3] para referenciar los documentos proporcionados.

Respuesta:"""

                    response = azure_client.chat.completions.create(
                        model=os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4o-mini'),
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=2500,  # Aumentado para respuestas más completas
                        temperature=0.3
                    )
                    
                    respuesta_texto = response.choices[0].message.content
                    
                    return {
                        'respuesta': respuesta_texto,
                        'fuentes': fuentes_formateadas,
                        'confianza': 0.9,
                        'metodo': 'azure_search_rag',
                        'tiempo_respuesta': 0,
                        'num_fuentes': len(fuentes_formateadas)
                    }
                else:
                    return {
                        'respuesta': "No se encontraron documentos relevantes en Azure Search para esta consulta.",
                        'fuentes': [],
                        'confianza': 0.1,
                        'metodo': 'azure_search_fallback'
                    }
                
            except Exception as e:
                logging.error(f"Error en Azure Search RAG: {str(e)}")
                return {
                    'respuesta': f"Error en consulta Azure Search: {str(e)}",
                    'fuentes': [],
                    'confianza': 0.0,
                    'metodo': 'error'
                }
        
        # Ejecutar la función async
        try:
            resultado = loop.run_until_complete(_ejecutar_consulta())
            return resultado
        finally:
            loop.close()
            
    except Exception as e:
        logging.error(f"Error en consulta_hibrida_sincrona: {str(e)}")
        return {
            'respuesta': f"Error general en consulta: {str(e)}",
            'fuentes': [],
            'confianza': 0.0,
            'metodo': 'error_general'
        }
        
        # Ejecutar la consulta asíncrona
        resultado = asyncio.run(_ejecutar_consulta())
        return resultado
        
    except Exception as e:
        return {
            'respuesta': f"Error en consulta RAG con Azure Search: {str(e)}",
            'fuentes': [],
            'confianza': 0.0,
            'metodo': 'error',
            'tiempo_respuesta': 0
        }

async def main():
    """Ejemplo de uso del sistema RAG"""
    sistema = SistemaRAGCompleto()
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Ejemplo de consulta compleja
    consulta = ConsultaRAG(
        pregunta="¿Qué es el genocidio de la Unión Patriótica?",
        tipo_consulta=TipoConsulta.COMPLEJA,
        contexto_adicional={"campo_interes": "analisis_juridico"}
    )
    
    respuesta, consulta_id = await sistema.procesar_consulta(consulta)
    
    print(f"Consulta ID: {consulta_id}")
    print(f"Respuesta: {respuesta.texto}")
    print(f"Confianza: {respuesta.confianza}")
    print(f"Método: {respuesta.metodo.value}")
    print(f"Tiempo: {respuesta.tiempo_respuesta}ms")
    print(f"Fuentes: {len(respuesta.fuentes)}")
    
    # Ejemplo de feedback
    feedback = FeedbackRAG(
        calificacion=5,
        comentario="Excelente respuesta, muy completa",
        aspectos={"precision": 5, "relevancia": 5, "completitud": 4}
    )
    
    await sistema.registrar_feedback(consulta_id, 1, feedback)
    print("\nFeedback registrado")

class SistemaRAGCompleto:
    """Clase wrapper para mantener compatibilidad con la interfaz principal"""
    
    def __init__(self):
        """Inicializar el sistema RAG completo"""
        self.azure_search = None
        try:
            self.azure_search = AzureSearchVectorizado()
        except Exception as e:
            print(f"Warning: Azure Search no disponible: {e}")
    
    def consulta_hibrida(self, pregunta: str) -> Dict[str, Any]:
        """Ejecutar consulta híbrida usando la función síncrona"""
        try:
            return consulta_hibrida_sincrona(pregunta)
        except Exception as e:
            return {
                'respuesta': f"Error en consulta híbrida: {str(e)}",
                'fuentes': [],
                'confianza': 0.0,
                'metodos_usados': ['error']
            }
    
    async def busqueda_cruzada_avanzada(self, pregunta: str, filtros_documento: Optional[Dict] = None, 
                                        filtros_chunk: Optional[Dict] = None, 
                                        filtros_azure_search: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Realiza búsqueda cruzada entre documentos completos y chunks para mejor filtrado
        
        Returns:
            Dict con respuesta, fuentes_documentos, fuentes_chunks, metadatos_filtrado
        """
        if not self.azure_search:
            return {
                'respuesta': "Azure Search no está disponible",
                'fuentes_documentos': [],
                'fuentes_chunks': [],
                'metadatos_filtrado': {},
                'confianza': 0.0
            }
        
        try:
            # Procesar filtros universales si están disponibles
            filtros_docs_final = filtros_documento
            filtros_chunks_final = filtros_chunk
            
            if filtros_azure_search:
                # Usar filtros del sistema universal
                filtros_docs_final = filtros_azure_search.get('documentos')
                filtros_chunks_final = filtros_azure_search.get('chunks')
            
            # Realizar búsqueda cruzada con filtros aplicados
            documentos, chunks = await self.azure_search.busqueda_cruzada(
                pregunta, filtros_docs_final, filtros_chunks_final, top_k_docs=20, top_k_chunks=5
            )
            
            # Obtener metadatos para filtrado dinámico
            metadatos_filtrado = self.azure_search.obtener_metadatos_filtrado(documentos)
            
            # Formatear documentos completos
            fuentes_documentos = []
            for doc in documentos:
                fuentes_documentos.append({
                    'id': doc.id,
                    'expediente_nuc': doc.expediente_nuc,
                    'tipo_documental': doc.tipo_documental,
                    'nombre_archivo': doc.nombre_archivo,
                    'fecha_documento': doc.fecha_documento,
                    'departamento': doc.departamento,
                    'municipio': doc.municipio,
                    'organizacion_responsable': doc.organizacion_responsable,
                    'contenido': doc.contenido_completo[:500] + '...' if len(doc.contenido_completo) > 500 else doc.contenido_completo,
                    'score': doc.score
                })
            
            # Formatear chunks (reutilizar lógica existente)
            fuentes_chunks = []
            if chunks:
                for i, chunk in enumerate(chunks, 1):
                    try:
                        nombre_archivo = chunk.nombre_archivo if hasattr(chunk, 'nombre_archivo') else 'N/A'
                        if nombre_archivo.endswith('.json'):
                            partes = nombre_archivo.replace('.json', '').split('_')
                            if len(partes) >= 3:
                                fecha = partes[0] if partes[0].isdigit() else 'S/F'
                                tipo_doc = partes[1] if len(partes) > 1 else 'DOC'
                                nombre_archivo = f"{tipo_doc}_{fecha}"
                        
                        contenido = chunk.contenido if hasattr(chunk, 'contenido') else ''
                        contenido_limpio = contenido.replace('\\n', ' ').replace('\\t', ' ')
                        
                        pagina = chunk.metadata.get('pagina', 'N/A') if hasattr(chunk, 'metadata') and chunk.metadata else 'N/A'
                        parrafo = chunk.metadata.get('parrafo', 'N/A') if hasattr(chunk, 'metadata') and chunk.metadata else 'N/A'
                        
                        fuentes_chunks.append({
                            'archivo': nombre_archivo,
                            'contenido': contenido_limpio[:500] + '...' if len(contenido_limpio) > 500 else contenido_limpio,
                            'score': float(chunk.score if hasattr(chunk, 'score') else 0.0),
                            'pagina': pagina,
                            'parrafo': parrafo,
                            'tipo_documental': chunk.tipo_documental if hasattr(chunk, 'tipo_documental') else 'Documento Judicial',
                            'expediente_nuc': chunk.expediente_nuc if hasattr(chunk, 'expediente_nuc') else 'N/A',
                            'metadata': chunk.metadata if hasattr(chunk, 'metadata') else {},
                            'doc_ref': f"Chunk {i}"
                        })
                    except Exception as e:
                        logging.error(f"Error procesando chunk {i}: {e}")
            
            # Generar respuesta con contexto combinado
            contexto_combinado = ""
            if documentos:
                contexto_combinado += "DOCUMENTOS COMPLETOS RELEVANTES:\n"
                for i, doc in enumerate(documentos[:3], 1):
                    contexto_combinado += f"\nDocumento {i}:\n"
                    contexto_combinado += f"Expediente: {doc.expediente_nuc}\n"
                    contexto_combinado += f"Tipo: {doc.tipo_documental}\n"
                    contexto_combinado += f"Ubicación: {doc.departamento}, {doc.municipio}\n"
                    contexto_combinado += f"Organización: {doc.organizacion_responsable}\n"
                    contexto_combinado += f"Contenido: {doc.contenido_completo[:800]}\n"
                    contexto_combinado += "-" * 80 + "\n"
            
            if chunks:
                contexto_combinado += "\nCHUNKS ESPECÍFICOS RELEVANTES:\n"
                for i, chunk in enumerate(chunks, 1):
                    contexto_combinado += f"\nChunk {i}:\n"
                    contexto_combinado += f"Expediente: {chunk.expediente_nuc}\n"
                    contexto_combinado += f"Tipo: {chunk.tipo_documental}\n"
                    contexto_combinado += f"Contenido: {chunk.contenido}\n"
                    contexto_combinado += "-" * 80 + "\n"
            
            # Generar respuesta usando Azure OpenAI
            if self.azure_search.openai_client and contexto_combinado:
                prompt = f"""
Eres un experto analista de documentos jurídicos especializizado en crímenes de lesa humanidad.

CONTEXTO DOCUMENTAL:
{contexto_combinado}

PREGUNTA DEL USUARIO: {pregunta}

Instrucciones:
1. Analiza la información de los documentos completos Y los chunks específicos
2. Proporciona una respuesta integral y detallada
3. Incluye citas específicas a expedientes, tipos documentales y organizaciones
4. Menciona ubicaciones geográficas cuando sea relevante
5. Estructura tu respuesta de manera clara y profesional
6. Si hay información contradictoria, mencionala
7. Usa un máximo de 2500 tokens para la respuesta

RESPUESTA:
"""
                try:
                    response = await self.azure_search.openai_client.chat.completions.acreate(
                        model="gpt-4",
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=2500,
                        temperature=0.7
                    )
                    respuesta = response.choices[0].message.content
                except Exception as e:
                    respuesta = f"Error generando respuesta con IA: {str(e)}. Contexto disponible con {len(documentos)} documentos y {len(chunks)} chunks."
            else:
                respuesta = f"Información encontrada: {len(documentos)} documentos completos y {len(chunks)} chunks específicos. Contexto disponible pero sin generación IA."
            
            return {
                'respuesta': respuesta,
                'fuentes_documentos': fuentes_documentos,
                'fuentes_chunks': fuentes_chunks,
                'metadatos_filtrado': metadatos_filtrado,
                'confianza': 0.8 if documentos and chunks else 0.6,
                'estadisticas': {
                    'documentos_encontrados': len(documentos),
                    'chunks_encontrados': len(chunks),
                    'filtros_aplicados_docs': filtros_documento or {},
                    'filtros_aplicados_chunks': filtros_chunk or {}
                }
            }
            
        except Exception as e:
            logging.error(f"Error en búsqueda cruzada avanzada: {e}")
            return {
                'respuesta': f"Error en búsqueda cruzada: {str(e)}",
                'fuentes_documentos': [],
                'fuentes_chunks': [],
                'metadatos_filtrado': {},
                'confianza': 0.0
            }

if __name__ == "__main__":
    asyncio.run(main())
