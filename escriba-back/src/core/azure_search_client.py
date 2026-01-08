"""
Cliente para Azure Cognitive Search
Maneja la búsqueda vectorial en los índices de documentos jurídicos
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from azure.search.documents import SearchClient
from azure.search.documents.models import Vector
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI

class AzureSearchClient:
    """Cliente para realizar búsquedas vectoriales en Azure Cognitive Search"""
    
    def __init__(self):
        """Inicializar cliente Azure Search"""
        self.endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
        self.key = os.getenv('AZURE_SEARCH_KEY')
        self.index_chunks = os.getenv('AZURE_SEARCH_INDEX_CHUNKS', 'exhaustive-legal-chunks')
        self.index_docs = os.getenv('AZURE_SEARCH_INDEX_DOCS', 'exhaustive-legal-index')
        
        if not all([self.endpoint, self.key]):
            raise ValueError("Azure Search endpoint y key son requeridos")
        
        # Cliente para índice de chunks
        self.search_client_chunks = SearchClient(
            endpoint=self.endpoint,
            index_name=self.index_chunks,
            credential=AzureKeyCredential(self.key)
        )
        
        # Cliente para índice de documentos
        self.search_client_docs = SearchClient(
            endpoint=self.endpoint,
            index_name=self.index_docs,
            credential=AzureKeyCredential(self.key)
        )
        
        # Cliente Azure OpenAI para embeddings
        self.openai_client = AzureOpenAI(
            api_key=os.getenv('AZURE_OPENAI_API_KEY'),
            api_version=os.getenv('AZURE_OPENAI_API_VERSION', '2024-12-01-preview'),
            azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT')
        )
        
        logging.info("Azure Search Client inicializado correctamente")
    
    def generar_embedding(self, texto: str) -> List[float]:
        """Generar embedding para un texto usando Azure OpenAI"""
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-ada-002",  # Modelo de embeddings
                input=texto
            )
            return response.data[0].embedding
        except Exception as e:
            logging.error(f"Error generando embedding: {e}")
            raise
    
    def buscar_chunks_relevantes(self, consulta: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Buscar chunks más relevantes usando búsqueda vectorial"""
        try:
            # Generar embedding de la consulta
            consulta_embedding = self.generar_embedding(consulta)
            
            # Crear vector de búsqueda
            vector_query = Vector(
                value=consulta_embedding,
                k=top_k,
                fields="content_vector"  # Campo del vector en el índice
            )
            
            # Realizar búsqueda híbrida (vectorial + texto)
            results = self.search_client_chunks.search(
                search_text=consulta,
                vectors=[vector_query],
                select=[
                    "chunk_id", "content", "document_id", "expediente_nuc",
                    "tipo_documental", "chunk_index", "metadata"
                ],
                top=top_k
            )
            
            chunks_relevantes = []
            for result in results:
                chunk = {
                    "chunk_id": result.get("chunk_id"),
                    "content": result.get("content"),
                    "document_id": result.get("document_id"),
                    "expediente_nuc": result.get("expediente_nuc"),
                    "tipo_documental": result.get("tipo_documental"),
                    "chunk_index": result.get("chunk_index"),
                    "score": result.get("@search.score", 0),
                    "metadata": result.get("metadata", {})
                }
                chunks_relevantes.append(chunk)
            
            logging.info(f"Encontrados {len(chunks_relevantes)} chunks relevantes")
            return chunks_relevantes
            
        except Exception as e:
            logging.error(f"Error en búsqueda de chunks: {e}")
            return []
    
    def buscar_documentos_completos(self, consulta: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Buscar documentos completos más relevantes"""
        try:
            # Generar embedding de la consulta
            consulta_embedding = self.generar_embedding(consulta)
            
            # Crear vector de búsqueda
            vector_query = Vector(
                value=consulta_embedding,
                k=top_k,
                fields="content_vector"  # Campo del vector en el índice
            )
            
            # Realizar búsqueda híbrida
            results = self.search_client_docs.search(
                search_text=consulta,
                vectors=[vector_query],
                select=[
                    "document_id", "expediente_nuc", "tipo_documental",
                    "texto_extraido", "analisis", "fecha_documento",
                    "metadata", "entidades"
                ],
                top=top_k
            )
            
            documentos_relevantes = []
            for result in results:
                documento = {
                    "document_id": result.get("document_id"),
                    "expediente_nuc": result.get("expediente_nuc"),
                    "tipo_documental": result.get("tipo_documental"),
                    "texto_extraido": result.get("texto_extraido"),
                    "analisis": result.get("analisis"),
                    "fecha_documento": result.get("fecha_documento"),
                    "score": result.get("@search.score", 0),
                    "metadata": result.get("metadata", {}),
                    "entidades": result.get("entidades", {})
                }
                documentos_relevantes.append(documento)
            
            logging.info(f"Encontrados {len(documentos_relevantes)} documentos relevantes")
            return documentos_relevantes
            
        except Exception as e:
            logging.error(f"Error en búsqueda de documentos: {e}")
            return []
    
    def busqueda_hibrida(self, consulta: str, chunks_count: int = 8, docs_count: int = 3) -> Dict[str, Any]:
        """Realizar búsqueda híbrida combinando chunks y documentos"""
        try:
            # Buscar chunks relevantes
            chunks = self.buscar_chunks_relevantes(consulta, chunks_count)
            
            # Buscar documentos completos
            documentos = self.buscar_documentos_completos(consulta, docs_count)
            
            return {
                "chunks": chunks,
                "documentos": documentos,
                "total_chunks": len(chunks),
                "total_documentos": len(documentos)
            }
            
        except Exception as e:
            logging.error(f"Error en búsqueda híbrida: {e}")
            return {"chunks": [], "documentos": [], "total_chunks": 0, "total_documentos": 0}
    
    def construir_contexto_rag(self, resultados: Dict[str, Any], max_tokens: int = 3000) -> str:
        """Construir contexto optimizado para el LLM"""
        try:
            contexto_partes = []
            token_count = 0
            
            # Agregar chunks más relevantes
            if resultados.get("chunks"):
                contexto_partes.append("=== FRAGMENTOS RELEVANTES ===\n")
                for i, chunk in enumerate(resultados["chunks"][:6], 1):
                    contenido = chunk.get("content", "")[:500]  # Limitar tamaño
                    expediente = chunk.get("expediente_nuc", "N/A")
                    tipo = chunk.get("tipo_documental", "N/A")
                    
                    fragmento = f"\n[{i}] Expediente: {expediente} | Tipo: {tipo}\n{contenido}...\n"
                    
                    # Estimar tokens (aproximadamente 4 caracteres por token)
                    tokens_fragmento = len(fragmento) // 4
                    if token_count + tokens_fragmento > max_tokens * 0.7:  # 70% para chunks
                        break
                    
                    contexto_partes.append(fragmento)
                    token_count += tokens_fragmento
            
            # Agregar análisis de documentos completos
            if resultados.get("documentos"):
                contexto_partes.append("\n=== ANÁLISIS DOCUMENTALES ===\n")
                for i, doc in enumerate(resultados["documentos"][:3], 1):
                    analisis = doc.get("analisis", "")[:300]  # Limitar análisis
                    expediente = doc.get("expediente_nuc", "N/A")
                    
                    if analisis:
                        analisis_parte = f"\n[A{i}] Expediente: {expediente}\nAnálisis: {analisis}...\n"
                        
                        tokens_analisis = len(analisis_parte) // 4
                        if token_count + tokens_analisis > max_tokens:
                            break
                        
                        contexto_partes.append(analisis_parte)
                        token_count += tokens_analisis
            
            contexto_final = "".join(contexto_partes)
            
            logging.info(f"Contexto RAG construido: ~{token_count} tokens estimados")
            return contexto_final
            
        except Exception as e:
            logging.error(f"Error construyendo contexto RAG: {e}")
            return "Error al construir contexto de documentos relevantes."
