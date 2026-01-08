#!/usr/bin/env python3
"""
RAG Semántico Mejorado - Búsqueda vectorial usando embeddings
Complementa el sistema existente con capacidades semánticas avanzadas
"""

import os
import json
import time
import logging
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from dotenv import load_dotenv
import psycopg2
import psycopg2.extras
from openai import AzureOpenAI

# Cargar configuración
load_dotenv('.env.gpt41')

logging.basicConfig(level=logging.INFO)

@dataclass
class DocumentoSemantico:
    """Documento encontrado por búsqueda semántica"""
    id: str
    archivo: str
    contenido: str
    expediente_nuc: str
    tipo_documental: str
    similitud: float
    fuente: str  # 'analisis' o 'texto_extraido'

@dataclass
class ResultadoSemantico:
    """Resultado de búsqueda semántica"""
    respuesta: str
    documentos: List[DocumentoSemantico]
    confianza: float
    tiempo_ms: int
    metodo: str
    embeddings_usados: bool
    tokens_usados: int = 0

class RAGSemantico:
    """Sistema RAG con búsqueda semántica avanzada"""
    
    def __init__(self):
        self.db_conn = None
        self.azure_client = None
        self._init_database()
        self._init_azure_openai()
    
    def _init_database(self):
        """Inicializar conexión a PostgreSQL"""
        try:
            self.db_conn = psycopg2.connect(
                host=os.getenv('POSTGRES_HOST', 'localhost'),
                port=os.getenv('POSTGRES_PORT', '5432'),
                database=os.getenv('POSTGRES_DB', 'documentos_juridicos_gpt4'),
                user=os.getenv('POSTGRES_USER', 'docs_user'),
                password=os.getenv('POSTGRES_PASSWORD', 'docs_password_2025')
            )
            logging.info("✅ Base de datos PostgreSQL conectada")
        except Exception as e:
            logging.error(f"❌ Error conectando a PostgreSQL: {e}")
            raise
    
    def _init_azure_openai(self):
        """Inicializar cliente Azure OpenAI"""
        try:
            self.azure_client = AzureOpenAI(
                api_key=os.getenv('AZURE_OPENAI_API_KEY'),
                api_version=os.getenv('AZURE_OPENAI_API_VERSION', '2024-12-01-preview'),
                azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT')
            )
            logging.info("✅ Azure OpenAI conectado")
        except Exception as e:
            logging.error(f"❌ Error conectando Azure OpenAI: {e}")
            self.azure_client = None
    
    def consultar_semantico(self, pregunta: str, max_documentos: int = 5) -> ResultadoSemantico:
        """
        Consulta semántica principal
        
        Args:
            pregunta: Pregunta del usuario
            max_documentos: Máximo número de documentos a procesar
        """
        inicio = time.time()
        
        try:
            # 1. Generar embedding de la pregunta
            if self.azure_client:
                embedding_pregunta = self._generar_embedding(pregunta)
                embeddings_usados = True
            else:
                embedding_pregunta = None
                embeddings_usados = False
            
            # 2. Buscar documentos relevantes
            documentos = self._buscar_documentos_semanticos(
                pregunta, 
                embedding_pregunta, 
                max_documentos
            )
            
            # 3. Generar respuesta contextual
            if self.azure_client and documentos:
                respuesta, tokens = self._generar_respuesta_contextual(pregunta, documentos)
            else:
                respuesta = self._respuesta_fallback(pregunta, documentos)
                tokens = 0
            
            # 4. Calcular confianza
            confianza = self._calcular_confianza_semantica(documentos, respuesta)
            
            tiempo_ms = int((time.time() - inicio) * 1000)
            
            return ResultadoSemantico(
                respuesta=respuesta,
                documentos=documentos,
                confianza=confianza,
                tiempo_ms=tiempo_ms,
                metodo="semantico_llm" if self.azure_client else "semantico_textual",
                embeddings_usados=embeddings_usados,
                tokens_usados=tokens
            )
            
        except Exception as e:
            logging.error(f"Error en consulta semántica: {e}")
            raise
    
    def _generar_embedding(self, texto: str) -> List[float]:
        """Generar embedding usando Azure OpenAI"""
        try:
            response = self.azure_client.embeddings.create(
                model="text-embedding-ada-002",
                input=texto
            )
            return response.data[0].embedding
        except Exception as e:
            logging.error(f"Error generando embedding: {e}")
            return None
    
    def _buscar_documentos_semanticos(self, pregunta: str, embedding: Optional[List[float]], 
                                    max_docs: int) -> List[DocumentoSemantico]:
        """
        Buscar documentos usando múltiples métodos semánticos
        """
        documentos = []
        
        try:
            cursor = self.db_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # Método 1: Búsqueda por palabras clave con ranking
            documentos_keywords = self._buscar_por_keywords(cursor, pregunta, max_docs)
            documentos.extend(documentos_keywords)
            
            # Método 2: Búsqueda por similitud textual (si hay extensión pg_trgm)
            documentos_similitud = self._buscar_por_similitud(cursor, pregunta, max_docs)
            documentos.extend(documentos_similitud)
            
            # Método 3: Búsqueda contextual por entidades
            documentos_entidades = self._buscar_por_entidades(cursor, pregunta, max_docs)
            documentos.extend(documentos_entidades)
            
            # Eliminar duplicados y ordenar por relevancia
            documentos_unicos = self._eliminar_duplicados_y_rankear(documentos)
            
            return documentos_unicos[:max_docs]
            
        except Exception as e:
            logging.error(f"Error en búsqueda semántica: {e}")
            return []
    
    def _buscar_por_keywords(self, cursor, pregunta: str, max_docs: int) -> List[DocumentoSemantico]:
        """Búsqueda optimizada por palabras clave"""
        try:
            # Extraer palabras clave de la pregunta
            keywords = self._extraer_keywords(pregunta)
            keywords_sql = ' | '.join(keywords) if keywords else pregunta
            
            sql = """
            SELECT 
                d.id,
                d.archivo,
                COALESCE(d.analisis, d.texto_extraido) as contenido,
                COALESCE(m.nuc, 'N/A') as expediente_nuc,
                COALESCE(m.detalle, 'N/A') as tipo_documental,
                CASE 
                    WHEN d.analisis IS NOT NULL THEN 'analisis'
                    ELSE 'texto_extraido'
                END as fuente,
                -- Ranking de relevancia
                ts_rank(
                    to_tsvector('spanish', COALESCE(d.analisis, d.texto_extraido)),
                    plainto_tsquery('spanish', %s)
                ) as relevancia
            FROM documentos d
            LEFT JOIN metadatos m ON d.id = m.documento_id
            WHERE (
                to_tsvector('spanish', COALESCE(d.analisis, d.texto_extraido)) 
                @@ plainto_tsquery('spanish', %s)
            )
            AND COALESCE(d.analisis, d.texto_extraido) IS NOT NULL
            ORDER BY relevancia DESC, d.paginas DESC
            LIMIT %s
            """
            
            cursor.execute(sql, (pregunta, pregunta, max_docs))
            resultados = cursor.fetchall()
            
            documentos = []
            for row in resultados:
                doc = DocumentoSemantico(
                    id=str(row['id']),
                    archivo=row['archivo'] or 'N/A',
                    contenido=row['contenido'][:2000] if row['contenido'] else '',  # Limitar contenido
                    expediente_nuc=row['expediente_nuc'],
                    tipo_documental=row['tipo_documental'],
                    similitud=float(row['relevancia']) if row['relevancia'] else 0.0,
                    fuente=row['fuente']
                )
                documentos.append(doc)
            
            return documentos
            
        except Exception as e:
            logging.error(f"Error en búsqueda por keywords: {e}")
            return []
    
    def _buscar_por_similitud(self, cursor, pregunta: str, max_docs: int) -> List[DocumentoSemantico]:
        """Búsqueda por similitud textual usando trigrams"""
        try:
            sql = """
            SELECT 
                d.id,
                d.archivo,
                COALESCE(d.analisis, d.texto_extraido) as contenido,
                COALESCE(m.nuc, 'N/A') as expediente_nuc,
                COALESCE(m.detalle, 'N/A') as tipo_documental,
                CASE 
                    WHEN d.analisis IS NOT NULL THEN 'analisis'
                    ELSE 'texto_extraido'
                END as fuente,
                -- Similitud usando trigrams (si está disponible)
                GREATEST(
                    similarity(COALESCE(d.analisis, ''), %s),
                    similarity(COALESCE(d.texto_extraido, ''), %s)
                ) as similitud
            FROM documentos d
            LEFT JOIN metadatos m ON d.id = m.documento_id
            WHERE (
                similarity(COALESCE(d.analisis, ''), %s) > 0.1
                OR similarity(COALESCE(d.texto_extraido, ''), %s) > 0.1
            )
            AND COALESCE(d.analisis, d.texto_extraido) IS NOT NULL
            ORDER BY similitud DESC
            LIMIT %s
            """
            
            cursor.execute(sql, (pregunta, pregunta, pregunta, pregunta, max_docs))
            resultados = cursor.fetchall()
            
            documentos = []
            for row in resultados:
                doc = DocumentoSemantico(
                    id=str(row['id']),
                    archivo=row['archivo'] or 'N/A',
                    contenido=row['contenido'][:2000] if row['contenido'] else '',
                    expediente_nuc=row['expediente_nuc'],
                    tipo_documental=row['tipo_documental'],
                    similitud=float(row['similitud']) if row['similitud'] else 0.0,
                    fuente=row['fuente']
                )
                documentos.append(doc)
            
            return documentos
            
        except Exception as e:
            # Si no está disponible pg_trgm, continuar sin error
            logging.debug(f"Similitud por trigrams no disponible: {e}")
            return []
    
    def _buscar_por_entidades(self, cursor, pregunta: str, max_docs: int) -> List[DocumentoSemantico]:
        """Búsqueda contextual basada en entidades mencionadas"""
        try:
            # Buscar documentos que mencionen entidades relacionadas con la pregunta
            sql = """
            SELECT DISTINCT
                d.id,
                d.archivo,
                COALESCE(d.analisis, d.texto_extraido) as contenido,
                COALESCE(m.nuc, 'N/A') as expediente_nuc,
                COALESCE(m.detalle, 'N/A') as tipo_documental,
                'entidades' as fuente,
                0.7 as similitud,  -- Relevancia fija para entidades
                d.paginas
            FROM documentos d
            LEFT JOIN metadatos m ON d.id = m.documento_id
            LEFT JOIN personas p ON d.id = p.documento_id
            LEFT JOIN organizaciones o ON d.id = o.documento_id
            WHERE (
                p.nombre ILIKE %s OR 
                o.nombre ILIKE %s OR
                COALESCE(d.analisis, d.texto_extraido) ILIKE %s
            )
            AND COALESCE(d.analisis, d.texto_extraido) IS NOT NULL
            ORDER BY d.paginas DESC
            LIMIT %s
            """
            
            pregunta_like = f"%{pregunta}%"
            cursor.execute(sql, (pregunta_like, pregunta_like, pregunta_like, max_docs))
            resultados = cursor.fetchall()
            
            documentos = []
            for row in resultados:
                doc = DocumentoSemantico(
                    id=str(row['id']),
                    archivo=row['archivo'] or 'N/A',
                    contenido=row['contenido'][:2000] if row['contenido'] else '',
                    expediente_nuc=row['expediente_nuc'],
                    tipo_documental=row['tipo_documental'],
                    similitud=float(row['similitud']),
                    fuente=row['fuente']
                )
                documentos.append(doc)
            
            return documentos
            
        except Exception as e:
            logging.error(f"Error en búsqueda por entidades: {e}")
            return []
    
    def _extraer_keywords(self, pregunta: str) -> List[str]:
        """Extraer palabras clave relevantes de la pregunta"""
        # Palabras de parada en español
        stop_words = {
            'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'es', 'se', 'no', 'te', 'lo', 'le',
            'da', 'su', 'por', 'son', 'con', 'para', 'como', 'están', 'era', 'más', 'este',
            'qué', 'cuál', 'cuáles', 'cómo', 'dónde', 'cuándo', 'por qué'
        }
        
        # Limpiar y dividir la pregunta
        palabras = pregunta.lower().replace('?', '').replace(',', '').split()
        keywords = [p for p in palabras if len(p) > 3 and p not in stop_words]
        
        return keywords[:5]  # Máximo 5 keywords
    
    def _eliminar_duplicados_y_rankear(self, documentos: List[DocumentoSemantico]) -> List[DocumentoSemantico]:
        """Eliminar duplicados y rankear por relevancia"""
        docs_unicos = {}
        
        for doc in documentos:
            if doc.id not in docs_unicos or doc.similitud > docs_unicos[doc.id].similitud:
                docs_unicos[doc.id] = doc
        
        # Ordenar por similitud descendente
        return sorted(docs_unicos.values(), key=lambda x: x.similitud, reverse=True)
    
    def _generar_respuesta_contextual(self, pregunta: str, documentos: List[DocumentoSemantico]) -> Tuple[str, int]:
        """Generar respuesta usando Azure OpenAI con contexto de documentos"""
        try:
            # Construir contexto
            contexto = self._construir_contexto_documentos(documentos)
            
            prompt = f"""
Eres un experto analista jurídico especializado en documentos del conflicto armado colombiano.

PREGUNTA: {pregunta}

DOCUMENTOS RELEVANTES ENCONTRADOS:
{contexto}

INSTRUCCIONES:
- Analiza los documentos proporcionados para responder la pregunta
- Proporciona una respuesta clara, precisa y fundamentada en los documentos
- Incluye referencias específicas a expedientes cuando sea relevante
- Si la información no es suficiente, indícalo claramente
- Usa un lenguaje técnico pero accesible
- Máximo 1000 palabras

RESPUESTA:"""

            response = self.azure_client.chat.completions.create(
                model=os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4.1'),
                messages=[
                    {"role": "system", "content": "Eres un experto analista jurídico especializado en documentos procesales del conflicto armado colombiano."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.3
            )
            
            respuesta = response.choices[0].message.content
            tokens = response.usage.total_tokens
            
            return respuesta, tokens
            
        except Exception as e:
            logging.error(f"Error generando respuesta contextual: {e}")
            return self._respuesta_fallback(pregunta, documentos), 0
    
    def _construir_contexto_documentos(self, documentos: List[DocumentoSemantico]) -> str:
        """Construir contexto optimizado para el LLM"""
        if not documentos:
            return "No se encontraron documentos relevantes."
        
        contexto_partes = []
        
        for i, doc in enumerate(documentos, 1):
            contexto_partes.append(f"""
[DOCUMENTO {i}]
Expediente: {doc.expediente_nuc}
Archivo: {doc.archivo}
Tipo: {doc.tipo_documental}
Relevancia: {doc.similitud:.2f}
Fuente: {doc.fuente}

Contenido: {doc.contenido[:800]}...
---""")
        
        return "\n".join(contexto_partes)
    
    def _respuesta_fallback(self, pregunta: str, documentos: List[DocumentoSemantico]) -> str:
        """Respuesta fallback cuando no hay Azure OpenAI disponible"""
        if not documentos:
            return f"No se encontraron documentos relevantes para la pregunta: '{pregunta}'"
        
        respuesta = f"Encontrados {len(documentos)} documentos relevantes para: '{pregunta}'\n\n"
        
        for i, doc in enumerate(documentos[:3], 1):
            respuesta += f"{i}. Expediente {doc.expediente_nuc} - {doc.archivo}\n"
            respuesta += f"   Tipo: {doc.tipo_documental} | Relevancia: {doc.similitud:.2f}\n"
            respuesta += f"   Extracto: {doc.contenido[:200]}...\n\n"
        
        return respuesta
    
    def _calcular_confianza_semantica(self, documentos: List[DocumentoSemantico], respuesta: str) -> float:
        """Calcular confianza basada en calidad de documentos y respuesta"""
        if not documentos:
            return 0.2
        
        # Confianza basada en número y calidad de documentos
        num_docs = len(documentos)
        confianza_docs = min(num_docs / 5.0, 1.0)
        
        # Confianza basada en similitud promedio
        similitud_promedio = sum(doc.similitud for doc in documentos) / len(documentos)
        confianza_similitud = min(similitud_promedio * 2.0, 1.0)
        
        # Confianza basada en longitud de respuesta
        confianza_respuesta = min(len(respuesta) / 500.0, 1.0)
        
        # Bonificación por tener análisis (más confiable que texto extraído)
        docs_con_analisis = sum(1 for doc in documentos if doc.fuente == 'analisis')
        bonificacion_analisis = (docs_con_analisis / len(documentos)) * 0.1
        
        # Combinación ponderada
        confianza = (
            confianza_docs * 0.3 + 
            confianza_similitud * 0.4 + 
            confianza_respuesta * 0.2 +
            bonificacion_analisis
        )
        
        return min(confianza, 0.95)  # Máximo 95%
    
    def obtener_estado(self) -> Dict:
        """Obtener estado del sistema semántico"""
        return {
            "database_conectada": self.db_conn is not None,
            "azure_openai_disponible": self.azure_client is not None,
            "embeddings_disponibles": self.azure_client is not None,
            "busqueda_textual": True,
            "busqueda_entidades": True
        }
    
    def __del__(self):
        """Cerrar conexiones"""
        if self.db_conn:
            self.db_conn.close()

# Instancia global
_rag_semantico = None

def get_rag_semantico():
    """Obtener instancia global del RAG semántico"""
    global _rag_semantico
    if _rag_semantico is None:
        _rag_semantico = RAGSemantico()
    return _rag_semantico
