#!/usr/bin/env python3
"""
Módulo RAG Mejorado - Búsqueda Vectorial Optimizada
Complementa el sistema existente sin reemplazarlo
"""

import os
import logging
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from dotenv import load_dotenv

# Cargar configuración
load_dotenv('.env.gpt41')

@dataclass
class ResultadoRAGMejorado:
    respuesta: str
    fuentes: List[Dict]
    confianza: float
    tiempo_ms: int
    metodo: str
    vectorial_usado: bool = False
    chunks_encontrados: int = 0

class RAGMejorado:
    """RAG con búsqueda vectorial optimizada para Azure Search"""
    
    def __init__(self):
        self.azure_search_available = False
        self.azure_client = None
        self._init_azure_search()
        
        # Configurar Azure OpenAI con manejo de errores robusto
        self.openai_client = None
        try:
            from openai import AzureOpenAI
            
            # Verificar que tenemos las variables necesarias
            api_key = os.getenv('AZURE_OPENAI_API_KEY')
            endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
            
            if not api_key or not endpoint:
                logging.warning("⚠️ Variables de Azure OpenAI no configuradas")
                return
            
            self.openai_client = AzureOpenAI(
                api_key=api_key,
                api_version=os.getenv('AZURE_OPENAI_API_VERSION', '2024-12-01-preview'),
                azure_endpoint=endpoint
            )
            logging.info("✅ Azure OpenAI configurado correctamente")
            
        except ImportError:
            logging.warning("⚠️ Biblioteca openai no disponible")
        except Exception as e:
            logging.error(f"❌ Error configurando Azure OpenAI: {e}")
            self.openai_client = None
    
    def _init_azure_search(self):
        """Inicializar Azure Search si está disponible"""
        try:
            from src.core.azure_search_client import AzureSearchClient
            self.azure_client = AzureSearchClient()
            self.azure_search_available = True
            logging.info("✅ Azure Search disponible")
        except Exception as e:
            logging.warning(f"⚠️ Azure Search no disponible: {e}")
            self.azure_search_available = False
    
    def consultar_mejorado(self, consulta: str, usar_vectorial: bool = True) -> ResultadoRAGMejorado:
        """
        Consulta RAG mejorada con opción vectorial
        
        Args:
            consulta: Texto de la consulta
            usar_vectorial: Si usar búsqueda vectorial (True) o solo textual (False)
        """
        start_time = time.time()
        
        try:
            if usar_vectorial and self.azure_search_available:
                return self._consulta_vectorial(consulta, start_time)
            else:
                return self._consulta_textual_fallback(consulta, start_time)
                
        except Exception as e:
            logging.error(f"Error en consulta RAG mejorada: {e}")
            return ResultadoRAGMejorado(
                respuesta=f"Error procesando consulta: {str(e)}",
                fuentes=[],
                confianza=0.0,
                tiempo_ms=int((time.time() - start_time) * 1000),
                metodo="error",
                vectorial_usado=False
            )
    
    def _consulta_vectorial(self, consulta: str, start_time: float) -> ResultadoRAGMejorado:
        """Consulta usando búsqueda vectorial de Azure Search"""
        try:
            # 1. Buscar documentos relevantes con búsqueda híbrida
            resultados = self.azure_client.busqueda_hibrida(
                consulta=consulta,
                chunks_count=8,
                docs_count=3
            )
            
            chunks = resultados.get('chunks', [])
            documentos = resultados.get('documentos', [])
            
            # 2. Construir contexto optimizado
            contexto = self._construir_contexto_vectorial(chunks, documentos)
            
            # 3. Generar respuesta con LLM
            respuesta = self._generar_respuesta_llm(consulta, contexto)
            
            # 4. Extraer fuentes
            fuentes = self._extraer_fuentes_vectoriales(chunks, documentos)
            
            # 5. Calcular confianza
            confianza = self._calcular_confianza_vectorial(chunks, documentos, respuesta)
            
            tiempo_ms = int((time.time() - start_time) * 1000)
            
            return ResultadoRAGMejorado(
                respuesta=respuesta,
                fuentes=fuentes,
                confianza=confianza,
                tiempo_ms=tiempo_ms,
                metodo="vectorial_hibrido",
                vectorial_usado=True,
                chunks_encontrados=len(chunks)
            )
            
        except Exception as e:
            logging.error(f"Error en consulta vectorial: {e}")
            # Fallback a consulta textual
            return self._consulta_textual_fallback(consulta, start_time)
    
    def _consulta_textual_fallback(self, consulta: str, start_time: float) -> ResultadoRAGMejorado:
        """Fallback usando búsqueda textual simple"""
        try:
            # Simular respuesta textual básica
            respuesta = f"Búsqueda textual para: '{consulta}'. Sistema vectorial no disponible en este momento."
            
            tiempo_ms = int((time.time() - start_time) * 1000)
            
            return ResultadoRAGMejorado(
                respuesta=respuesta,
                fuentes=[],
                confianza=0.3,
                tiempo_ms=tiempo_ms,
                metodo="textual_fallback",
                vectorial_usado=False
            )
            
        except Exception as e:
            logging.error(f"Error en fallback textual: {e}")
            raise
    
    def _construir_contexto_vectorial(self, chunks: List[Dict], documentos: List[Dict]) -> str:
        """Construir contexto optimizado para el LLM"""
        contexto_partes = ["=== INFORMACIÓN RELEVANTE ===\n"]
        
        # Agregar chunks más relevantes
        if chunks:
            contexto_partes.append("📄 **Fragmentos Específicos:**\n")
            for i, chunk in enumerate(chunks[:5], 1):
                expediente = chunk.get('expediente_nuc', 'N/A')
                contenido = chunk.get('content', '')[:400]  # Limitar
                contexto_partes.append(f"[{i}] Expediente {expediente}: {contenido}...\n")
        
        # Agregar documentos completos si es necesario
        if documentos:
            contexto_partes.append("\n📋 **Documentos Relacionados:**\n")
            for i, doc in enumerate(documentos[:2], 1):
                expediente = doc.get('expediente_nuc', 'N/A')
                analisis = doc.get('analisis', '')[:300]
                contexto_partes.append(f"[{i}] Documento {expediente}: {analisis}...\n")
        
        return "\n".join(contexto_partes)
    
    def _generar_respuesta_llm(self, consulta: str, contexto: str) -> str:
        """Generar respuesta usando Azure OpenAI"""
        if not self.openai_client:
            return "Sistema de IA no disponible para generar respuesta."
        
        try:
            prompt = f"""
Eres un experto analista jurídico especializado en documentos del conflicto armado colombiano.

CONSULTA: {consulta}

CONTEXTO DISPONIBLE:
{contexto}

INSTRUCCIONES:
- Analiza el contexto proporcionado para responder la consulta
- Enfócate en información jurídica y factual
- Si el contexto no es suficiente, indícalo claramente
- Incluye referencias a expedientes cuando sea posible
- Mantén un lenguaje técnico pero comprensible
- Máximo 800 palabras

RESPUESTA:"""

            response = self.openai_client.chat.completions.create(
                model=os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4.1'),
                messages=[
                    {"role": "system", "content": "Eres un experto analista jurídico especializado en documentos procesales del conflicto armado colombiano."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logging.error(f"Error generando respuesta LLM: {e}")
            return f"Error generando respuesta: {str(e)}"
    
    def _extraer_fuentes_vectoriales(self, chunks: List[Dict], documentos: List[Dict]) -> List[Dict]:
        """Extraer fuentes con información vectorial"""
        fuentes = []
        
        # Fuentes de chunks
        for chunk in chunks[:3]:
            fuentes.append({
                'tipo': 'chunk',
                'expediente': chunk.get('expediente_nuc', 'N/A'),
                'documento_id': chunk.get('document_id', 'N/A'),
                'relevancia': chunk.get('score', 0.0),
                'tipo_documental': chunk.get('tipo_documental', 'N/A')
            })
        
        # Fuentes de documentos
        for doc in documentos[:2]:
            fuentes.append({
                'tipo': 'documento',
                'expediente': doc.get('expediente_nuc', 'N/A'),
                'documento_id': doc.get('document_id', 'N/A'),
                'relevancia': doc.get('score', 0.0),
                'tipo_documental': doc.get('tipo_documental', 'N/A')
            })
        
        return fuentes
    
    def _calcular_confianza_vectorial(self, chunks: List[Dict], documentos: List[Dict], respuesta: str) -> float:
        """Calcular confianza basada en calidad vectorial"""
        if not chunks and not documentos:
            return 0.2
        
        # Confianza basada en número de fuentes
        num_fuentes = len(chunks) + len(documentos)
        confianza_fuentes = min(num_fuentes / 8.0, 1.0)
        
        # Confianza basada en scores de relevancia
        scores = []
        for chunk in chunks:
            if 'score' in chunk:
                scores.append(chunk['score'])
        for doc in documentos:
            if 'score' in doc:
                scores.append(doc['score'])
        
        if scores:
            confianza_relevancia = sum(scores) / len(scores)
        else:
            confianza_relevancia = 0.5
        
        # Confianza basada en longitud de respuesta
        confianza_respuesta = min(len(respuesta) / 500.0, 1.0)
        
        # Combinación ponderada
        confianza = (
            confianza_fuentes * 0.4 + 
            confianza_relevancia * 0.4 + 
            confianza_respuesta * 0.2
        )
        
        return min(confianza, 0.95)  # Máximo 95%
    
    def obtener_estado(self) -> Dict[str, Any]:
        """Obtener estado del sistema RAG mejorado"""
        return {
            "azure_search_disponible": self.azure_search_available,
            "azure_openai_disponible": self.openai_client is not None,
            "modo_recomendado": "vectorial" if self.azure_search_available else "textual"
        }

# Instancia global
_rag_mejorado = None

def get_rag_mejorado():
    """Obtener instancia global del RAG mejorado"""
    global _rag_mejorado
    if _rag_mejorado is None:
        _rag_mejorado = RAGMejorado()
    return _rag_mejorado
