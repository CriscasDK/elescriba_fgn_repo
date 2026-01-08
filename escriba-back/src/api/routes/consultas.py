"""
Endpoints de consultas - Conectados con lógica real
"""
import sys
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import time
import asyncio

# Agregar path para importar módulos core del monolito (NO romper app_dash.py)
proyecto_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(proyecto_root))

# Importar modelos Pydantic desde escriba-back
from src.api.models import (
    ConsultaBDRequest, ConsultaBDResponse,
    ConsultaRAGRequest, ConsultaRAGResponse,
    ConsultaHibridaRequest, ConsultaHibridaResponse,
    VictimasResponse, Victima, VictimaDetalle,
    OpcionesFiltrosResponse, DocumentoMetadatos
)

# Importar funciones de lógica desde el MONOLITO (core/consultas.py)
# Esto asegura que usamos la misma lógica que app_dash.py sin romper nada
from core.consultas import (
    ejecutar_consulta,
    ejecutar_consulta_geografica_directa,  # Función directa que bypasea agentes
    ejecutar_consulta_rag_inteligente,
    ejecutar_consulta_hibrida,
    obtener_victimas_paginadas,
    obtener_detalle_victima,
    obtener_metadatos_documento,
    obtener_opciones_nuc,
    obtener_opciones_departamento,
    obtener_opciones_municipio,
    obtener_opciones_tipo_documento,
    obtener_opciones_despacho,
    obtener_rango_fechas,
    clasificar_consulta
)

router = APIRouter()


# ==================== ENDPOINTS DE VÍCTIMAS ====================

@router.get("/victimas", response_model=VictimasResponse, tags=["victimas"])
async def listar_victimas(
    page: int = 1,
    page_size: int = 20
):
    """
    Listar víctimas con paginación

    - **page**: Número de página (default: 1)
    - **page_size**: Tamaño de página (default: 20, max: 100)
    """
    try:
        # Validar parámetros
        if page < 1:
            raise HTTPException(status_code=400, detail="page debe ser >= 1")
        if page_size < 1 or page_size > 100:
            raise HTTPException(status_code=400, detail="page_size debe estar entre 1 y 100")

        # Obtener víctimas paginadas
        victimas_data, total = obtener_victimas_paginadas(page, page_size)

        # Convertir a modelos Pydantic
        victimas = [Victima(**v) for v in victimas_data]

        # Calcular total de páginas
        total_pages = (total + page_size - 1) // page_size

        return VictimasResponse(
            victimas=victimas,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo víctimas: {str(e)}")


@router.get("/victimas/{nombre}", response_model=VictimaDetalle, tags=["victimas"])
async def obtener_victima(nombre: str):
    """
    Obtener detalle completo de una víctima por nombre

    - **nombre**: Nombre de la víctima (puede ser parcial)
    """
    try:
        detalle = obtener_detalle_victima(nombre)

        if not detalle or detalle.get("menciones", 0) == 0:
            raise HTTPException(status_code=404, detail=f"Víctima '{nombre}' no encontrada")

        return VictimaDetalle(**detalle)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo detalle de víctima: {str(e)}")


# ==================== ENDPOINTS DE DOCUMENTOS ====================

@router.get("/documentos/{archivo}/metadatos", response_model=DocumentoMetadatos, tags=["documentos"])
async def obtener_metadatos(archivo: str):
    """
    Obtener metadatos completos de un documento

    - **archivo**: Nombre del archivo del documento
    """
    try:
        metadatos = obtener_metadatos_documento(archivo)

        if not metadatos:
            raise HTTPException(status_code=404, detail=f"Documento '{archivo}' no encontrado")

        return DocumentoMetadatos(**metadatos)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo metadatos: {str(e)}")


# ==================== ENDPOINTS DE CONSULTAS ====================

@router.post("/consultas/bd", response_model=ConsultaBDResponse, tags=["consultas"])
async def consulta_bd(request: ConsultaBDRequest):
    """
    Ejecutar consulta de base de datos con filtros

    Soporta:
    - Búsqueda por NUC, departamento, municipio
    - Filtros temporales (fecha_inicio, fecha_fin)
    - Filtros de despacho y tipo de documento
    """
    try:
        tiempo_inicio = time.time()

        # Si hay filtros geográficos/metadatos, usar función directa (bypasea agentes)
        if any([request.departamento, request.municipio, request.nuc,
                request.tipo_documento, request.despacho,
                request.fecha_inicio, request.fecha_fin]):
            resultado = ejecutar_consulta_geografica_directa(
                consulta=request.consulta,
                departamento=request.departamento,
                municipio=request.municipio,
                nuc=request.nuc,
                despacho=request.despacho,
                tipo_documento=request.tipo_documento,
                fecha_inicio=request.fecha_inicio,
                fecha_fin=request.fecha_fin,
                limit_victimas=request.limit_victimas
            )
        else:
            # Sin filtros, usar función con agentes
            resultado = ejecutar_consulta(
                consulta=request.consulta,
                nucs=request.nuc,
                departamento=request.departamento,
                municipio=request.municipio,
                tipo_documento=request.tipo_documento,
                despacho=request.despacho,
                fecha_inicio=request.fecha_inicio,
                fecha_fin=request.fecha_fin
            )

        tiempo_ms = int((time.time() - tiempo_inicio) * 1000)

        # Convertir víctimas a modelos Pydantic
        victimas = [Victima(**v) for v in resultado.get("victimas", [])]

        return ConsultaBDResponse(
            tipo="bd",
            victimas=victimas,
            fuentes=resultado.get("fuentes", []),
            total_victimas=len(victimas),
            total_fuentes=len(resultado.get("fuentes", [])),
            tiempo_ms=tiempo_ms,
            metadata={
                "consulta_original": request.consulta,
                "filtros_aplicados": {
                    "nuc": request.nuc,
                    "departamento": request.departamento,
                    "municipio": request.municipio,
                    "tipo_documento": request.tipo_documento,
                    "despacho": request.despacho,
                    "fecha_inicio": request.fecha_inicio,
                    "fecha_fin": request.fecha_fin
                }
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en consulta BD: {str(e)}")


@router.post("/consultas/rag", response_model=ConsultaRAGResponse, tags=["consultas"])
def consulta_rag(request: ConsultaRAGRequest):
    """
    Ejecutar consulta RAG (búsqueda semántica con IA)

    Usa Azure Cognitive Search + GPT-4o-mini para responder
    preguntas en lenguaje natural sobre los documentos.
    """
    try:
        tiempo_inicio = time.time()

        # Ejecutar consulta RAG (función sync que usa asyncio internamente)
        resultado = ejecutar_consulta_rag_inteligente(
            consulta=request.consulta,
            contexto_conversacional=request.contexto_conversacional
        )

        tiempo_ms = int((time.time() - tiempo_inicio) * 1000)

        return ConsultaRAGResponse(
            tipo="rag",
            respuesta=resultado.get("respuesta", ""),
            fuentes=resultado.get("fuentes", []),
            confianza=resultado.get("confianza"),
            tiempo_ms=tiempo_ms,
            metadata={
                "consulta_original": request.consulta,
                "modelo": "gpt-4o-mini",
                "top_k": request.top_k
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en consulta RAG: {str(e)}")


@router.post("/consultas/hibrida", response_model=ConsultaHibridaResponse, tags=["consultas"])
def consulta_hibrida(request: ConsultaHibridaRequest):
    """
    Ejecutar consulta híbrida (BD + RAG)

    Combina resultados estructurados de la BD con análisis
    semántico de RAG para respuestas más completas.
    """
    try:
        tiempo_inicio = time.time()

        # Ejecutar consulta híbrida (función sync que usa asyncio internamente)
        resultado = ejecutar_consulta_hibrida(
            consulta=request.consulta,
            departamento=request.departamento,
            municipio=request.municipio,
            nucs=[request.nuc] if request.nuc else None,  # Convertir a lista
            tipo_documento=request.tipo_documento,
            despacho=request.despacho,
            fecha_inicio=request.fecha_inicio,
            fecha_fin=request.fecha_fin
        )

        tiempo_ms = int((time.time() - tiempo_inicio) * 1000)

        # Convertir víctimas a modelos Pydantic
        victimas = [Victima(**v) for v in resultado.get("victimas_bd", [])]

        return ConsultaHibridaResponse(
            tipo="hibrida",
            victimas=victimas,
            total_victimas=len(victimas),
            respuesta_rag=resultado.get("respuesta_rag", ""),
            fuentes_rag=resultado.get("fuentes_rag", []),
            tiempo_ms=tiempo_ms,
            metadata={
                "consulta_original": request.consulta,
                "filtros_bd": {
                    "departamento": request.departamento,
                    "municipio": request.municipio,
                    "nuc": request.nuc
                }
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en consulta híbrida: {str(e)}")


@router.post("/consultas/clasificar", tags=["consultas"])
async def clasificar_tipo_consulta(consulta: str):
    """
    Clasificar el tipo de consulta (bd, rag, o hibrida)

    Útil para que el frontend sepa qué tipo de consulta enviar.
    """
    try:
        tipo = clasificar_consulta(consulta)

        return {
            "consulta": consulta,
            "tipo": tipo,
            "descripcion": {
                "bd": "Consulta estructurada a base de datos",
                "rag": "Consulta semántica con IA",
                "hibrida": "Consulta que combina BD y RAG"
            }.get(tipo, "Desconocido")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clasificando consulta: {str(e)}")


# ==================== ENDPOINTS DE OPCIONES/FILTROS ====================

@router.get("/opciones/filtros", response_model=OpcionesFiltrosResponse, tags=["opciones"])
async def obtener_opciones():
    """
    Obtener todas las opciones disponibles para filtros

    Útil para poblar dropdowns en el frontend.
    """
    try:
        nucs = obtener_opciones_nuc()
        departamentos = obtener_opciones_departamento()
        municipios = obtener_opciones_municipio()
        tipos_documento = obtener_opciones_tipo_documento()
        despachos = obtener_opciones_despacho()
        fecha_min, fecha_max = obtener_rango_fechas()

        return OpcionesFiltrosResponse(
            nucs=nucs,
            departamentos=departamentos,
            municipios=municipios,
            tipos_documento=tipos_documento,
            despachos=despachos,
            rango_fechas={
                "min": fecha_min,
                "max": fecha_max
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo opciones: {str(e)}")


# ==================== HEALTH CHECKS ====================

@router.get("/consultas/health", tags=["health"])
async def consultas_health():
    """Health check de módulo de consultas"""
    return {
        "module": "consultas",
        "status": "ok",
        "endpoints_activos": [
            "GET /victimas",
            "GET /victimas/{nombre}",
            "GET /documentos/{archivo}/metadatos",
            "POST /consultas/bd",
            "POST /consultas/rag",
            "POST /consultas/hibrida",
            "POST /consultas/clasificar",
            "GET /opciones/filtros"
        ]
    }
