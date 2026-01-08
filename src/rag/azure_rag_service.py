"""
Servicio especializado para consultas RAG (Retrieval-Augmented Generation)
"""

import time
import logging
import asyncio
from typing import List, Dict, Any, Optional
from ..core.base_query_service import RAGQueryService
from ..core.models import QueryRequest, QueryResponse, QueryType, RAGResult, Source, SearchFilter

class AzureRAGService(RAGQueryService):
    """Servicio RAG usando Azure Cognitive Search + Azure OpenAI"""
    
    def __init__(self):
        self.azure_search_client = None
        self.azure_openai_client = None
        self.search_enabled = False
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Inicializar clientes de Azure"""
        try:
            # Importar y configurar Azure Search
            from ..rag.azure_search_client import AzureSearchClient
            self.azure_search_client = AzureSearchClient()
            
            # Importar y configurar Azure OpenAI
            from openai import AzureOpenAI
            import os
            self.azure_openai_client = AzureOpenAI(
                api_key=os.getenv('AZURE_OPENAI_API_KEY'),
                api_version=os.getenv('AZURE_OPENAI_API_VERSION', '2024-12-01-preview'),
                azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT')
            )
            
            self.search_enabled = True
            logging.info("✅ Azure RAG Service inicializado correctamente")
            
        except Exception as e:
            logging.warning(f"⚠️ Azure RAG Service limitado: {e}")
            self.search_enabled = False
    
    def is_capable(self, query_text: str) -> float:
        """Determinar capacidad para consultas de análisis semántico"""
        if not self.search_enabled:
            return 0.0
        
        query_lower = query_text.lower()
        
        # Palabras clave que indican análisis semántico/contextual
        rag_keywords = [
            'patrones', 'estructuras', 'análisis', 'contexto',
            'qué dice', 'cómo se', 'por qué', 'explica',
            'metodologías', 'estrategias', 'operaciones',
            'modus operandi', 'cadenas de mando', 'jerarquías',
            'dinámicas', 'procesos', 'fenómenos'
        ]
        
        matches = sum(1 for keyword in rag_keywords if keyword in query_lower)
        return min(matches / 2.0, 1.0)  # Max score si hay 2+ matches
    
    async def process_query(self, request: QueryRequest) -> QueryResponse:
        """Procesar consulta RAG"""
        start_time = time.time()
        
        try:
            if not self.search_enabled:
                raise Exception("Servicio RAG no disponible")
            
            # 1. Buscar documentos relevantes
            search_start = time.time()
            relevant_docs = await self.search_documents(request.text, 
                                                       self._extract_filters(request.filters))
            search_time = int((time.time() - search_start) * 1000)
            
            # 2. Construir contexto
            context = self._build_context(relevant_docs)
            
            # 3. Generar respuesta
            generation_start = time.time()
            answer = await self.generate_response(request.text, context)
            generation_time = int((time.time() - generation_start) * 1000)
            
            # 4. Construir fuentes
            sources = [Source(
                type="azure_search",
                identifier=doc.get('document_id', 'unknown'),
                relevance_score=doc.get('score', 0.0),
                metadata={
                    'expediente_nuc': doc.get('expediente_nuc'),
                    'tipo_documental': doc.get('tipo_documental')
                }
            ) for doc in relevant_docs[:5]]  # Top 5 fuentes
            
            total_time = int((time.time() - start_time) * 1000)
            
            response = QueryResponse(
                query_id=f"rag_{int(time.time())}",
                original_query=request.text,
                method_used=QueryType.RAG,
                answer=answer,
                confidence=self._calculate_confidence(relevant_docs, answer),
                execution_time_ms=total_time,
                sources=sources,
                tokens_used=self._estimate_tokens(context + answer)
            )
            
            return response
            
        except Exception as e:
            logging.error(f"Error en consulta RAG: {e}")
            raise
    
    async def search_documents(self, query: str, filters: SearchFilter = None) -> List[Dict[str, Any]]:
        """Buscar documentos relevantes usando Azure Search"""
        try:
            # Usar búsqueda híbrida (vectorial + texto)
            results = self.azure_search_client.busqueda_hibrida(
                consulta=query,
                chunks_count=8,
                docs_count=3
            )
            
            # Combinar chunks y documentos
            relevant_docs = []
            
            # Agregar chunks relevantes
            for chunk in results.get('chunks', []):
                relevant_docs.append({
                    'type': 'chunk',
                    'content': chunk.get('content'),
                    'document_id': chunk.get('document_id'),
                    'expediente_nuc': chunk.get('expediente_nuc'),
                    'tipo_documental': chunk.get('tipo_documental'),
                    'score': chunk.get('score', 0.0)
                })
            
            # Agregar documentos completos
            for doc in results.get('documentos', []):
                relevant_docs.append({
                    'type': 'document',
                    'content': doc.get('analisis') or doc.get('texto_extraido'),
                    'document_id': doc.get('document_id'),
                    'expediente_nuc': doc.get('expediente_nuc'),
                    'tipo_documental': doc.get('tipo_documental'),
                    'score': doc.get('score', 0.0)
                })
            
            # Ordenar por relevancia
            relevant_docs.sort(key=lambda x: x.get('score', 0.0), reverse=True)
            
            return relevant_docs[:10]  # Top 10 más relevantes
            
        except Exception as e:
            logging.error(f"Error en búsqueda de documentos: {e}")
            return []
    
    async def generate_response(self, query: str, context: str) -> str:
        """Generar respuesta usando Azure OpenAI"""
        try:
            prompt = self._build_prompt(query, context)
            
            response = self.azure_openai_client.chat.completions.create(
                model=os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4.1'),
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logging.error(f"Error generando respuesta: {e}")
            return "Lo siento, no pude generar una respuesta adecuada en este momento."
    
    def _build_context(self, relevant_docs: List[Dict[str, Any]]) -> str:
        """Construir contexto optimizado para el LLM"""
        if not relevant_docs:
            return "No se encontraron documentos relevantes."
        
        context_parts = ["=== DOCUMENTOS RELEVANTES ===\n"]
        
        for i, doc in enumerate(relevant_docs[:6], 1):
            content = doc.get('content', '')[:500]  # Limitar contenido
            expediente = doc.get('expediente_nuc', 'N/A')
            tipo = doc.get('tipo_documental', 'N/A')
            
            context_parts.append(f"\n[{i}] Expediente: {expediente} | Tipo: {tipo}")
            context_parts.append(f"Contenido: {content}...\n")
        
        return "\n".join(context_parts)
    
    def _build_prompt(self, query: str, context: str) -> str:
        """Construir prompt especializado"""
        return f"""
CONSULTA DEL USUARIO: {query}

CONTEXTO DE DOCUMENTOS JURÍDICOS:
{context}

INSTRUCCIONES:
- Analiza el contexto proporcionado para responder la consulta
- Enfócate en patrones, estructuras y análisis jurídicos
- Incluye referencias específicas a expedientes cuando sea relevante
- Si el contexto no es suficiente, indícalo claramente
- Usa un lenguaje técnico pero accesible
- Proporciona una respuesta detallada y fundamentada
"""
    
    def _get_system_prompt(self) -> str:
        """Prompt del sistema especializado"""
        return """Eres un experto analista jurídico especializado en documentos del conflicto armado colombiano. 

Tu función es analizar documentos judiciales y proporcionar respuestas precisas sobre:
- Patrones de violencia y estructuras criminales
- Análisis de responsabilidades y cadenas de mando
- Metodologías y modus operandi documentados
- Contexto histórico y jurídico de los casos

Siempre basa tus respuestas ÚNICAMENTE en el contexto proporcionado y mantén un enfoque analítico y objetivo."""
    
    def _extract_filters(self, filters: Dict) -> SearchFilter:
        """Extraer filtros para búsqueda"""
        return SearchFilter(
            start_date=filters.get('start_date'),
            end_date=filters.get('end_date'),
            document_type=filters.get('document_type'),
            nuc=filters.get('nuc')
        )
    
    def _calculate_confidence(self, docs: List[Dict], answer: str) -> float:
        """Calcular confianza basada en calidad de documentos y respuesta"""
        if not docs:
            return 0.3
        
        # Confianza basada en:
        # 1. Número de documentos relevantes
        doc_score = min(len(docs) / 5.0, 1.0)
        
        # 2. Scores promedio de relevancia
        avg_score = sum(doc.get('score', 0.0) for doc in docs) / len(docs)
        relevance_score = min(avg_score, 1.0)
        
        # 3. Longitud de la respuesta (indicador de contenido)
        length_score = min(len(answer) / 500.0, 1.0)
        
        # Combinación ponderada
        confidence = (doc_score * 0.4 + relevance_score * 0.4 + length_score * 0.2)
        return min(confidence, 0.95)  # Max 95% para RAG
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimar tokens usados (aproximación)"""
        return len(text) // 4  # Aproximadamente 4 caracteres por token
    
    def get_service_info(self) -> Dict[str, Any]:
        """Información del servicio"""
        return {
            "name": "Azure RAG Service",
            "type": "rag",
            "capabilities": [
                "Análisis semántico de documentos",
                "Búsqueda vectorial",
                "Generación contextual con IA",
                "Identificación de patrones complejos"
            ],
            "search_enabled": self.search_enabled,
            "models": ["Azure Cognitive Search", "GPT-4.1"]
        }
