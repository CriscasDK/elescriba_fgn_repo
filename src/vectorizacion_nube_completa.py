#!/usr/bin/env python3
"""
Vectorización completamente en la nube:
- Obtiene documentos desde Azure Cognitive Search
- Genera embeddings con Azure OpenAI
- Actualiza vectores en Azure Cognitive Search
NO requiere PostgreSQL local
"""

import os
import sys
import time
import json
import logging
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv('.env.gpt41')

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vectorizacion_nube.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class VectorizadorNube:
    def __init__(self):
        """Inicializar configuraciones para Azure"""
        self.azure_openai_config = {
            'endpoint': os.getenv('AZURE_OPENAI_ENDPOINT'),
            'api_key': os.getenv('AZURE_OPENAI_API_KEY'),
            'api_version': os.getenv('AZURE_OPENAI_API_VERSION', '2024-12-01-preview'),
            'deployment': 'text-embedding-ada-002'
        }
        self.search_config = {
            'endpoint': os.getenv('AZURE_SEARCH_ENDPOINT'),
            'admin_key': os.getenv('AZURE_SEARCH_KEY'),
            'index_name': os.getenv('AZURE_SEARCH_INDEX_CHUNKS', 'exhaustive-legal-chunks')
        }
        self.batch_size = 10  # Regresar al tamaño que funciona
        self.max_workers = 3   # Configuración estable
        
    def obtener_documentos_azure_search(self, skip: int = 0, top: int = 50) -> List[Dict]:
        """
        Obtener documentos desde Azure Cognitive Search que no tienen vectores
        """
        try:
            url = f"{self.search_config['endpoint']}/indexes/{self.search_config['index_name']}/docs/search"
            
            headers = {
                'Content-Type': 'application/json',
                'api-key': self.search_config['admin_key']
            }
            
            # NO usar filtro por content_vector porque no funciona con Collections
            # En su lugar, obtenemos todos los documentos y filtramos después
            data = {
                "search": "*",
                "select": "chunk_id,texto_chunk,resumen_chunk,documento_id,content_vector",
                "skip": skip,
                "top": top,
                "count": True
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                todos_documentos = result.get('value', [])
                total_count = result.get('@odata.count', 0)
                
                # Filtrar documentos que NO tienen content_vector
                documentos = []
                for doc in todos_documentos:
                    vector = doc.get('content_vector')
                    if not vector or len(vector) == 0:
                        # Remover content_vector del doc para limpieza
                        if 'content_vector' in doc:
                            del doc['content_vector']
                        documentos.append(doc)
                
                logger.info(f"📊 Obtenidos {len(documentos)} documentos sin vectorizar de {len(todos_documentos)} documentos consultados (total: {total_count})")
                return documentos, len(documentos)  # Devolver count real de documentos sin vectorizar
            else:
                logger.error(f"❌ Error obteniendo documentos: {response.status_code} - {response.text}")
                return [], 0
                
        except Exception as e:
            logger.error(f"❌ Error en búsqueda Azure Search: {e}")
            return [], 0
    
    def obtener_todos_documentos_azure_search(self, limite: int = None) -> List[Dict]:
        """
        Obtener todos los documentos que necesitan vectorización, manejando paginación
        """
        try:
            url = f"{self.search_config['endpoint']}/indexes/{self.search_config['index_name']}/docs/search"
            
            headers = {
                'Content-Type': 'application/json',
                'api-key': self.search_config['admin_key']
            }
            
            # Obtener todos los documentos (sin filtro problemático)
            data = {
                "search": "*",
                "select": "chunk_id,texto_chunk,resumen_chunk,documento_id,content_vector",
                "top": limite if limite else 50000,  # Procesar todos los documentos
                "count": True
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=30, params={'api-version': '2023-11-01'})
            
            if response.status_code == 200:
                result = response.json()
                todos_documentos = result.get('value', [])
                total_count = result.get('@odata.count', 0)
                
                # Filtrar solo los que realmente necesitan vectorización
                documentos_sin_vector = []
                for doc in todos_documentos:
                    # Verificar si tiene texto y NO tiene vector
                    tiene_texto = doc.get('texto_chunk') and len(doc.get('texto_chunk', '').strip()) > 10
                    vector = doc.get('content_vector')
                    tiene_vector = vector and len(vector) > 0
                    
                    if tiene_texto and not tiene_vector:
                        # Limpiar el campo content_vector para enviar solo los necesarios
                        if 'content_vector' in doc:
                            del doc['content_vector']
                        documentos_sin_vector.append(doc)
                
                logger.info(f"📊 Encontrados {len(documentos_sin_vector)} documentos para vectorizar de {total_count} totales")
                return documentos_sin_vector
            else:
                logger.error(f"❌ Error obteniendo documentos: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error en búsqueda Azure Search: {e}")
            return []
    
    def generar_embedding_azure(self, texto: str) -> Optional[List[float]]:
        """
        Generar embedding usando Azure OpenAI directamente con requests
        """
        try:
            url = f"{self.azure_openai_config['endpoint']}openai/deployments/{self.azure_openai_config['deployment']}/embeddings"
            
            headers = {
                'Content-Type': 'application/json',
                'api-key': self.azure_openai_config['api_key']
            }
            
            data = {
                'input': texto,
                'user': 'vectorization-system'
            }
            
            params = {
                'api-version': self.azure_openai_config['api_version']
            }
            
            response = requests.post(
                url, 
                headers=headers, 
                json=data, 
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                embedding = result['data'][0]['embedding']
                logger.debug(f"✅ Embedding generado: {len(embedding)} dimensiones")
                return embedding
            else:
                logger.error(f"❌ Error en embedding: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error generando embedding: {e}")
            return None
    
    def actualizar_vectores_azure_search(self, documentos_vectorizados: List[Dict]) -> bool:
        """
        Actualizar Azure Cognitive Search con los vectores generados
        """
        try:
            url = f"{self.search_config['endpoint']}/indexes/{self.search_config['index_name']}/docs/index"
            
            headers = {
                'Content-Type': 'application/json',
                'api-key': self.search_config['admin_key']
            }
            
            # Preparar documentos para Azure Search
            azure_docs = []
            for doc in documentos_vectorizados:
                azure_doc = {
                    '@search.action': 'mergeOrUpload',
                    'chunk_id': str(doc['chunk_id']),
                    'content_vector': doc['embedding']
                }
                azure_docs.append(azure_doc)
            
            data = {
                'value': azure_docs
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=60, params={'api-version': '2023-11-01'})
            
            if response.status_code in [200, 201]:
                result = response.json()
                exitosos = sum(1 for r in result.get('value', []) if r.get('statusCode') in [200, 201])
                logger.info(f"✅ Azure Search actualizado: {exitosos}/{len(azure_docs)} documentos exitosos")
                return True
            else:
                logger.error(f"❌ Error actualizando Azure Search: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error en actualización Azure Search: {e}")
            return False
    
    def procesar_lote_documentos(self, lote_documentos: List[Dict]) -> List[Dict]:
        """
        Procesar un lote de documentos para generar embeddings
        """
        documentos_vectorizados = []
        
        for doc in lote_documentos:
            try:
                # Preparar texto para embedding (combinar texto y resumen si existe)
                texto_completo = doc.get('texto_chunk', '')
                if doc.get('resumen_chunk'):
                    texto_completo += f"\n\nResumen: {doc['resumen_chunk']}"
                
                # Verificar que el texto no esté vacío
                if not texto_completo.strip() or len(texto_completo.strip()) < 10:
                    logger.warning(f"⚠️ Texto vacío o muy corto para chunk_id: {doc.get('chunk_id', 'unknown')}")
                    continue
                
                # Generar embedding
                embedding = self.generar_embedding_azure(texto_completo)
                
                if embedding and len(embedding) == 1536:  # Verificar dimensiones correctas
                    doc_vectorizado = doc.copy()
                    doc_vectorizado['embedding'] = embedding
                    documentos_vectorizados.append(doc_vectorizado)
                    logger.debug(f"✅ Vector generado para chunk_id: {doc.get('chunk_id', 'unknown')}")
                else:
                    logger.warning(f"⚠️ Vector inválido para chunk_id: {doc.get('chunk_id', 'unknown')}")
                
                # Pausa pequeña para evitar rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"❌ Error procesando documento {doc.get('chunk_id', 'unknown')}: {e}")
                continue
        
        return documentos_vectorizados
    
    def ejecutar_vectorizacion_masiva(self, limite_documentos: int = None):
        """
        Ejecutar vectorización masiva completamente en la nube
        """
        logger.info("🚀 Iniciando vectorización masiva EN LA NUBE")
        logger.info("📡 Obteniendo documentos desde Azure Cognitive Search...")
        
        # Obtener documentos desde Azure Search
        documentos = self.obtener_todos_documentos_azure_search(limite_documentos)
        if not documentos:
            logger.warning("⚠️ No hay documentos para procesar")
            return
        
        total_documentos = len(documentos)
        documentos_procesados = 0
        documentos_exitosos = 0
        
        logger.info(f"📊 Procesando {total_documentos} documentos en lotes de {self.batch_size}")
        
        # Procesar en lotes
        for i in range(0, total_documentos, self.batch_size):
            lote = documentos[i:i + self.batch_size]
            lote_num = i // self.batch_size + 1
            
            logger.info(f"📦 Procesando lote {lote_num}: documentos {i+1}-{min(i+self.batch_size, total_documentos)} de {total_documentos}")
            
            # Procesar lote
            documentos_vectorizados = self.procesar_lote_documentos(lote)
            
            if documentos_vectorizados:
                # Actualizar Azure Search
                if self.actualizar_vectores_azure_search(documentos_vectorizados):
                    documentos_exitosos += len(documentos_vectorizados)
                    logger.info(f"✅ Lote {lote_num} procesado exitosamente: {len(documentos_vectorizados)} documentos vectorizados")
                else:
                    logger.error(f"❌ Error actualizando lote {lote_num} en Azure Search")
            else:
                logger.warning(f"⚠️ Lote {lote_num} no generó vectores válidos")
            
            documentos_procesados += len(lote)
            
            # Mostrar progreso
            progreso = (documentos_procesados / total_documentos) * 100
            logger.info(f"📊 Progreso: {documentos_procesados}/{total_documentos} ({progreso:.1f}%) - Exitosos: {documentos_exitosos}")
            
            # Pausa entre lotes para evitar rate limiting
            time.sleep(2)
        
        logger.info(f"🎉 Vectorización completada: {documentos_exitosos}/{total_documentos} documentos vectorizados exitosamente")
        logger.info("☁️ Todos los vectores están guardados en Azure Cognitive Search")

    def verificar_configuracion(self) -> bool:
        """
        Verificar que las conexiones a Azure funcionen
        """
        logger.info("🔍 Verificando configuración de Azure...")
        
        # Verificar Azure Search
        try:
            url = f"{self.search_config['endpoint']}/indexes/{self.search_config['index_name']}"
            headers = {'api-key': self.search_config['admin_key']}
            response = requests.get(url, headers=headers, timeout=10, params={'api-version': '2023-11-01'})
            
            if response.status_code == 200:
                logger.info("✅ Azure Cognitive Search: Conexión exitosa")
            else:
                logger.error(f"❌ Azure Search: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ Error Azure Search: {e}")
            return False
        
        # Verificar Azure OpenAI
        try:
            test_embedding = self.generar_embedding_azure("Texto de prueba")
            if test_embedding and len(test_embedding) == 1536:
                logger.info("✅ Azure OpenAI: Conexión exitosa")
                return True
            else:
                logger.error("❌ Azure OpenAI: Error en embedding de prueba")
                return False
        except Exception as e:
            logger.error(f"❌ Error Azure OpenAI: {e}")
            return False

def main():
    """Función principal"""
    logger.info("🌐 Iniciando vectorización COMPLETAMENTE EN LA NUBE")
    
    vectorizador = VectorizadorNube()
    
    # Verificar configuración
    if not vectorizador.verificar_configuracion():
        logger.error("❌ Error en la configuración de Azure")
        return
    
    # Ejecutar vectorización MASIVA - TODOS LOS DOCUMENTOS (sin límite)
    vectorizador.ejecutar_vectorizacion_masiva(limite_documentos=None)

if __name__ == "__main__":
    main()
