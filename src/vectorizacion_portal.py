#!/usr/bin/env python3
"""
Vectorización masiva usando el campo content_vector creado en el portal de Azure
Estrategia alternativa para evitar problemas con la librería openai
"""

import os
import sys
import time
import json
import logging
import psycopg2
from typing import List, Dict, Any, Optional
from datetime import datetime
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vectorizacion_portal.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class VectorizadorPortal:
    def __init__(self):
        """Inicializar conexiones y configuraciones"""
        self.conn_postgres = None
        self.azure_config = {
            'endpoint': 'https://fgnfoundrylabo3874907599.cognitiveservices.azure.com/',
            'api_key': '38e7e2e066044f5bb85bbf4b06b95b21',
            'api_version': '2023-05-15',
            'deployment': 'text-embedding-ada-002'
        }
        self.search_config = {
            'endpoint': 'https://fgnfoundrylabo3874907599.search.windows.net',
            'admin_key': 'kCWy8eaGtZIJ8vqRpfILGcBzpJJDCHyp4YtgGVr6YxAzSeDzr5BF',
            'index_name': 'exhaustive-legal-chunks'
        }
        self.batch_size = 10
        self.max_workers = 3
        
    def conectar_postgres(self):
        """Conectar a PostgreSQL"""
        try:
            self.conn_postgres = psycopg2.connect(
                host="localhost",
                database="documentos_juridicos",
                user="docs_user",
                password="docs_password_2025",
                port="5432"
            )
            logger.info("✅ Conexión a PostgreSQL establecida")
            return True
        except Exception as e:
            logger.error(f"❌ Error conectando a PostgreSQL: {e}")
            return False
    
    def generar_embedding_requests(self, texto: str) -> Optional[List[float]]:
        """
        Generar embedding usando requests directamente (sin librería openai)
        """
        try:
            url = f"{self.azure_config['endpoint']}openai/deployments/{self.azure_config['deployment']}/embeddings"
            
            headers = {
                'Content-Type': 'application/json',
                'api-key': self.azure_config['api_key']
            }
            
            data = {
                'input': texto,
                'user': 'vectorization-system'
            }
            
            params = {
                'api-version': self.azure_config['api_version']
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
    
    def obtener_documentos_sin_vector(self, limite: int = None) -> List[Dict]:
        """
        Obtener documentos desde PostgreSQL que necesitan vectorización
        """
        try:
            cursor = self.conn_postgres.cursor()
            
            query = """
            SELECT 
                chunk_id,
                texto_chunk,
                resumen_chunk,
                documento_id,
                posicion_chunk
            FROM chunks_documentos 
            WHERE chunk_id IS NOT NULL 
            AND texto_chunk IS NOT NULL 
            AND LENGTH(texto_chunk) > 10
            ORDER BY documento_id, posicion_chunk
            """
            
            if limite:
                query += f" LIMIT {limite}"
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            documentos = []
            for row in rows:
                doc = {
                    'chunk_id': row[0],
                    'texto_chunk': row[1],
                    'resumen_chunk': row[2] or '',
                    'documento_id': row[3],
                    'posicion_chunk': row[4]
                }
                documentos.append(doc)
            
            cursor.close()
            logger.info(f"📊 Obtenidos {len(documentos)} documentos para vectorizar")
            return documentos
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo documentos: {e}")
            return []
    
    def actualizar_azure_search(self, documentos_vectorizados: List[Dict]) -> bool:
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
            
            response = requests.post(url, headers=headers, json=data, timeout=60)
            
            if response.status_code in [200, 201]:
                result = response.json()
                logger.info(f"✅ Azure Search actualizado: {len(azure_docs)} documentos")
                return True
            else:
                logger.error(f"❌ Error actualizando Azure Search: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error en actualización Azure Search: {e}")
            return False
    
    def procesar_lote(self, lote_documentos: List[Dict]) -> List[Dict]:
        """
        Procesar un lote de documentos para generar embeddings
        """
        documentos_vectorizados = []
        
        for doc in lote_documentos:
            try:
                # Preparar texto para embedding (combinar texto y resumen)
                texto_completo = doc['texto_chunk']
                if doc['resumen_chunk']:
                    texto_completo += f"\n\nResumen: {doc['resumen_chunk']}"
                
                # Generar embedding
                embedding = self.generar_embedding_requests(texto_completo)
                
                if embedding:
                    doc_vectorizado = doc.copy()
                    doc_vectorizado['embedding'] = embedding
                    documentos_vectorizados.append(doc_vectorizado)
                    logger.debug(f"✅ Vector generado para chunk_id: {doc['chunk_id']}")
                else:
                    logger.warning(f"⚠️ No se pudo generar vector para chunk_id: {doc['chunk_id']}")
                
                # Pausa pequeña para evitar rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"❌ Error procesando documento {doc.get('chunk_id', 'unknown')}: {e}")
                continue
        
        return documentos_vectorizados
    
    def vectorizar_masivo(self, limite_documentos: int = None):
        """
        Ejecutar vectorización masiva
        """
        logger.info("🚀 Iniciando vectorización masiva")
        
        # Obtener documentos
        documentos = self.obtener_documentos_sin_vector(limite_documentos)
        if not documentos:
            logger.warning("⚠️ No hay documentos para procesar")
            return
        
        total_documentos = len(documentos)
        documentos_procesados = 0
        documentos_exitosos = 0
        
        # Procesar en lotes
        for i in range(0, total_documentos, self.batch_size):
            lote = documentos[i:i + self.batch_size]
            
            logger.info(f"📦 Procesando lote {i//self.batch_size + 1}: documentos {i+1}-{min(i+self.batch_size, total_documentos)} de {total_documentos}")
            
            # Procesar lote
            documentos_vectorizados = self.procesar_lote(lote)
            
            if documentos_vectorizados:
                # Actualizar Azure Search
                if self.actualizar_azure_search(documentos_vectorizados):
                    documentos_exitosos += len(documentos_vectorizados)
                    logger.info(f"✅ Lote procesado exitosamente: {len(documentos_vectorizados)} documentos")
                else:
                    logger.error(f"❌ Error actualizando lote en Azure Search")
            
            documentos_procesados += len(lote)
            
            # Mostrar progreso
            progreso = (documentos_procesados / total_documentos) * 100
            logger.info(f"📊 Progreso: {documentos_procesados}/{total_documentos} ({progreso:.1f}%) - Exitosos: {documentos_exitosos}")
            
            # Pausa entre lotes
            time.sleep(1)
        
        logger.info(f"🎉 Vectorización completada: {documentos_exitosos}/{total_documentos} documentos vectorizados exitosamente")

def main():
    """Función principal"""
    logger.info("🔧 Iniciando sistema de vectorización portal")
    
    vectorizador = VectorizadorPortal()
    
    # Conectar a PostgreSQL
    if not vectorizador.conectar_postgres():
        logger.error("❌ No se pudo conectar a PostgreSQL")
        return
    
    # Ejecutar vectorización (empezar con pocos documentos para prueba)
    vectorizador.vectorizar_masivo(limite_documentos=20)
    
    # Cerrar conexiones
    if vectorizador.conn_postgres:
        vectorizador.conn_postgres.close()
        logger.info("🔌 Conexión PostgreSQL cerrada")

if __name__ == "__main__":
    main()
