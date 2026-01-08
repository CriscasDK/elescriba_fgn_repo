"""
Cliente mejorado para Azure Cognitive Search con manejo robusto de errores
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv('.env.gpt41')

class AzureSearchClientMejorado:
    """Cliente robusto para Azure Search con fallbacks"""
    
    def __init__(self):
        """Inicializar cliente con manejo de errores"""
        self.endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
        self.key = os.getenv('AZURE_SEARCH_KEY')
        self.index_chunks = os.getenv('AZURE_SEARCH_INDEX_CHUNKS', 'exhaustive-legal-chunks')
        self.index_docs = os.getenv('AZURE_SEARCH_INDEX_DOCS', 'exhaustive-legal-index')
        
        self.search_available = False
        self.openai_available = False
        
        # Intentar inicializar Azure Search
        self._init_search_client()
        
        # Intentar inicializar Azure OpenAI
        self._init_openai_client()
    
    def _init_search_client(self):
        """Inicializar cliente de Azure Search"""
        try:
            if not all([self.endpoint, self.key]):
                logging.warning("⚠️ Azure Search: endpoint o key no configurados")
                return
            
            from azure.search.documents import SearchClient
            from azure.core.credentials import AzureKeyCredential
            
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
            
            self.search_available = True
            logging.info("✅ Azure Search Client inicializado")
            
        except ImportError as e:
            logging.warning(f"⚠️ Azure Search no disponible: biblioteca no instalada - {e}")
        except Exception as e:
            logging.error(f"❌ Error inicializando Azure Search: {e}")
    
    def _init_openai_client(self):
        """Inicializar cliente de Azure OpenAI"""
        try:
            api_key = os.getenv('AZURE_OPENAI_API_KEY')
            endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
            
            if not api_key or not endpoint:
                logging.warning("⚠️ Azure OpenAI: credenciales no configuradas")
                return
            
            from openai import AzureOpenAI
            
            self.openai_client = AzureOpenAI(
                api_key=api_key,
                api_version=os.getenv('AZURE_OPENAI_API_VERSION', '2024-12-01-preview'),
                azure_endpoint=endpoint
            )
            
            self.openai_available = True
            logging.info("✅ Azure OpenAI Client inicializado")
            
        except ImportError as e:
            logging.warning(f"⚠️ Azure OpenAI no disponible: biblioteca no instalada - {e}")
        except Exception as e:
            logging.error(f"❌ Error inicializando Azure OpenAI: {e}")
    
    def busqueda_textual_chunks(self, consulta: str, top: int = 5) -> List[Dict]:
        """Búsqueda textual en chunks (fallback si no hay vectorial)"""
        if not self.search_available:
            logging.warning("Azure Search no disponible")
            return []
        
        try:
            results = self.search_client_chunks.search(
                search_text=consulta,
                top=top,
                select=["content", "expediente_nuc", "tipo_documental", "document_id"]
            )
            
            chunks = []
            for result in results:
                chunks.append({
                    'content': result.get('content', ''),
                    'expediente_nuc': result.get('expediente_nuc', ''),
                    'tipo_documental': result.get('tipo_documental', ''),
                    'document_id': result.get('document_id', ''),
                    'score': getattr(result, '@search.score', 0.0)
                })
            
            logging.info(f"📄 Encontrados {len(chunks)} chunks con búsqueda textual")
            return chunks
            
        except Exception as e:
            logging.error(f"Error en búsqueda textual chunks: {e}")
            return []
    
    def busqueda_textual_documentos(self, consulta: str, top: int = 3) -> List[Dict]:
        """Búsqueda textual en documentos"""
        if not self.search_available:
            logging.warning("Azure Search no disponible")
            return []
        
        try:
            results = self.search_client_docs.search(
                search_text=consulta,
                top=top,
                select=["analisis", "expediente_nuc", "tipo_documental", "document_id"]
            )
            
            documentos = []
            for result in results:
                documentos.append({
                    'analisis': result.get('analisis', ''),
                    'expediente_nuc': result.get('expediente_nuc', ''),
                    'tipo_documental': result.get('tipo_documental', ''),
                    'document_id': result.get('document_id', ''),
                    'score': getattr(result, '@search.score', 0.0)
                })
            
            logging.info(f"📋 Encontrados {len(documentos)} documentos con búsqueda textual")
            return documentos
            
        except Exception as e:
            logging.error(f"Error en búsqueda textual documentos: {e}")
            return []
    
    def busqueda_hibrida_simple(self, consulta: str, chunks_count: int = 5, docs_count: int = 3) -> Dict[str, Any]:
        """Búsqueda híbrida simple usando solo texto (más estable)"""
        
        # Buscar chunks
        chunks = self.busqueda_textual_chunks(consulta, chunks_count)
        
        # Buscar documentos
        documentos = self.busqueda_textual_documentos(consulta, docs_count)
        
        return {
            'chunks': chunks,
            'documentos': documentos,
            'metodo': 'textual_hibrido',
            'total_chunks': len(chunks),
            'total_documentos': len(documentos)
        }
    
    def generar_embedding(self, texto: str) -> Optional[List[float]]:
        """Generar embedding usando Azure OpenAI"""
        if not self.openai_available:
            logging.warning("Azure OpenAI no disponible para embeddings")
            return None
        
        try:
            response = self.openai_client.embeddings.create(
                input=texto,
                model="text-embedding-ada-002"
            )
            return response.data[0].embedding
            
        except Exception as e:
            logging.error(f"Error generando embedding: {e}")
            return None
    
    def busqueda_vectorial_avanzada(self, consulta: str, chunks_count: int = 5) -> List[Dict]:
        """Búsqueda vectorial avanzada (solo si está disponible)"""
        if not self.search_available or not self.openai_available:
            logging.info("Búsqueda vectorial no disponible, usando textual")
            return self.busqueda_textual_chunks(consulta, chunks_count)
        
        try:
            # Generar embedding de la consulta
            embedding = self.generar_embedding(consulta)
            if not embedding:
                return self.busqueda_textual_chunks(consulta, chunks_count)
            
            # Intentar búsqueda vectorial
            try:
                from azure.search.documents.models import Vector
                
                vector = Vector(
                    value=embedding,
                    k=chunks_count,
                    fields="content_vector"
                )
                
                results = self.search_client_chunks.search(
                    search_text=consulta,
                    vectors=[vector],
                    top=chunks_count,
                    select=["content", "expediente_nuc", "tipo_documental", "document_id"]
                )
                
                chunks = []
                for result in results:
                    chunks.append({
                        'content': result.get('content', ''),
                        'expediente_nuc': result.get('expediente_nuc', ''),
                        'tipo_documental': result.get('tipo_documental', ''),
                        'document_id': result.get('document_id', ''),
                        'score': getattr(result, '@search.score', 0.0)
                    })
                
                logging.info(f"🎯 Encontrados {len(chunks)} chunks con búsqueda vectorial")
                return chunks
                
            except ImportError:
                logging.info("Vector no disponible, usando búsqueda textual")
                return self.busqueda_textual_chunks(consulta, chunks_count)
            
        except Exception as e:
            logging.error(f"Error en búsqueda vectorial: {e}")
            return self.busqueda_textual_chunks(consulta, chunks_count)
    
    def obtener_estado(self) -> Dict[str, Any]:
        """Obtener estado del cliente"""
        return {
            'search_disponible': self.search_available,
            'openai_disponible': self.openai_available,
            'endpoint': self.endpoint,
            'indices': {
                'chunks': self.index_chunks,
                'documentos': self.index_docs
            }
        }

# Instancia global
_azure_client = None

def get_azure_search_client():
    """Obtener cliente global de Azure Search"""
    global _azure_client
    if _azure_client is None:
        _azure_client = AzureSearchClientMejorado()
    return _azure_client
