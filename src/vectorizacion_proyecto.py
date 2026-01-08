#!/usr/bin/env python3
"""
Sistema de Vectorización que utiliza el Azure OpenAI ya funcional del proyecto
"""

import os
import json
import numpy as np
import psycopg2
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging
from datetime import datetime
import hashlib
import pickle
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class EmbeddingResult:
    """Resultado de embedding con metadatos"""
    vector: List[float]
    texto_original: str
    campo_origen: str
    documento_id: str
    dimensiones: int
    timestamp: datetime
    hash_contenido: str

class VectorizadorProyecto:
    """Sistema de vectorización que usa el Azure OpenAI ya funcional del proyecto"""
    
    def __init__(self, config_file: str = '.env.gpt41'):
        self.config_file = config_file
        self.cache_dir = Path("cache/embeddings")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Cargar configuración
        self._cargar_config()
        
        # Inicializar componentes
        self.postgres_conn = None
        
        # Cache local de embeddings
        self.embedding_cache = {}
        self._cargar_cache_local()
        
        # Estadísticas
        self.stats = {
            'embeddings_generados': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'vectorizaciones_completadas': 0
        }
    
    def _cargar_config(self):
        """Carga configuración desde archivo .env"""
        from dotenv import load_dotenv
        load_dotenv(self.config_file)
        
        self.config = {
            # PostgreSQL
            'postgres_host': os.getenv('POSTGRES_HOST', 'localhost'),
            'postgres_port': int(os.getenv('POSTGRES_PORT', 5432)),
            'postgres_db': os.getenv('POSTGRES_DB'),
            'postgres_user': os.getenv('POSTGRES_USER'),
            'postgres_password': os.getenv('POSTGRES_PASSWORD'),
        }
    
    def _cargar_cache_local(self):
        """Carga cache local de embeddings"""
        cache_file = self.cache_dir / "embeddings_cache.pkl"
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    self.embedding_cache = pickle.load(f)
                logger.info(f"Cache local cargado: {len(self.embedding_cache)} embeddings")
            except Exception as e:
                logger.warning(f"Error cargando cache: {e}")
                self.embedding_cache = {}
    
    def _guardar_cache_local(self):
        """Guarda cache local de embeddings"""
        cache_file = self.cache_dir / "embeddings_cache.pkl"
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(self.embedding_cache, f)
            logger.info(f"Cache local guardado: {len(self.embedding_cache)} embeddings")
        except Exception as e:
            logger.error(f"Error guardando cache: {e}")
    
    def _get_hash_contenido(self, texto: str) -> str:
        """Genera hash del contenido para cache"""
        return hashlib.md5(texto.encode('utf-8')).hexdigest()
    
    def inicializar_postgres(self) -> bool:
        """Inicializa conexión PostgreSQL"""
        try:
            self.postgres_conn = psycopg2.connect(
                host=self.config['postgres_host'],
                port=self.config['postgres_port'],
                database=self.config['postgres_db'],
                user=self.config['postgres_user'],
                password=self.config['postgres_password']
            )
            
            logger.info("✅ PostgreSQL inicializado correctamente")
            return True
            
        except Exception as e:
            logger.error(f"Error conectando PostgreSQL: {e}")
            return False
    
    def generar_embedding_via_interfaz(self, texto: str) -> Optional[List[float]]:
        """Genera embedding usando el sistema que ya funciona en interfaz_fiscales.py"""
        try:
            # Importar y usar la funcionalidad que ya funciona
            import sys
            sys.path.append('.')
            
            # Usar la función RAG que debe tener Azure OpenAI funcionando
            from interfaz_fiscales import consulta_rag
            
            # Hacer una consulta de prueba para verificar que Azure OpenAI funciona
            consulta_prueba = "embedding test"
            respuesta_prueba = consulta_rag(consulta_prueba)
            
            # Si llegamos aquí, el sistema funciona
            # Ahora importar directamente AzureOpenAI que debe estar ya inicializado
            import openai
            from openai import AzureOpenAI
            
            azure_client = AzureOpenAI(
                api_key=os.getenv('AZURE_OPENAI_API_KEY'),
                api_version=os.getenv('AZURE_OPENAI_VERSION', '2024-12-01-preview'),
                azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT')
            )
            
            # Generar embedding
            response = azure_client.embeddings.create(
                input=texto,
                model="text-embedding-ada-002"
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            logger.warning(f"Error generando embedding via interfaz: {e}")
            return None
    
    def generar_embedding(self, texto: str, usar_cache: bool = True) -> Optional[List[float]]:
        """Genera embedding para un texto"""
        if not texto or not texto.strip():
            return None
        
        # Verificar cache
        hash_contenido = self._get_hash_contenido(texto)
        if usar_cache and hash_contenido in self.embedding_cache:
            self.stats['cache_hits'] += 1
            return self.embedding_cache[hash_contenido]['vector']
        
        # Generar nuevo embedding usando la interfaz funcional
        vector = self.generar_embedding_via_interfaz(texto)
        
        if vector:
            # Guardar en cache
            if usar_cache:
                self.embedding_cache[hash_contenido] = {
                    'vector': vector,
                    'texto': texto[:100],  # Solo primeros 100 chars para debug
                    'timestamp': datetime.now().isoformat(),
                    'dimensiones': len(vector)
                }
            
            self.stats['embeddings_generados'] += 1
            self.stats['cache_misses'] += 1
            
            return vector
        
        return None
    
    def obtener_documentos_para_vectorizar(self, limite: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """Obtiene documentos de la base de datos para vectorizar"""
        if not self.postgres_conn:
            if not self.inicializar_postgres():
                return []
        
        query = """
        SELECT 
            d.id as documento_id,
            d.archivo,
            d.nuc,
            d.estado,
            d.cuaderno,
            d.despacho,
            d.entidad_productora,
            d.serie,
            d.subserie,
            d.texto_extraido,
            d.analisis,
            -- Obtener personas asociadas
            (SELECT string_agg(p.nombre, ', ') FROM personas p WHERE p.documento_id = d.id LIMIT 10) as personas_texto,
            -- Obtener organizaciones asociadas  
            (SELECT string_agg(o.nombre, ', ') FROM organizaciones o WHERE o.documento_id = d.id LIMIT 10) as organizaciones_texto,
            -- Obtener lugares asociados
            (SELECT string_agg(al.nombre, ', ') FROM analisis_lugares al WHERE al.documento_id = d.id LIMIT 10) as lugares_texto
        FROM documentos d
        WHERE d.texto_extraido IS NOT NULL 
        AND LENGTH(TRIM(d.texto_extraido)) > 100
        ORDER BY d.id
        LIMIT %s OFFSET %s
        """
        
        try:
            with self.postgres_conn.cursor() as cursor:
                cursor.execute(query, (limite, offset))
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                
                docs = []
                for row in rows:
                    doc = dict(zip(columns, row))
                    docs.append(doc)
                
                return docs
                
        except Exception as e:
            logger.error(f"Error obteniendo documentos: {e}")
            return []
    
    def vectorizar_documento_completo(self, doc_data: Dict[str, Any]) -> Dict[str, List[float]]:
        """Vectoriza todos los campos de un documento"""
        documento_id = doc_data.get('documento_id', 'unknown')
        vectores = {}
        
        # 1. Vector del texto principal (texto_extraido) - resumido
        texto_extraido = doc_data.get('texto_extraido', '')
        if texto_extraido:
            # Tomar una muestra representativa para evitar exceder tokens
            texto_muestra = texto_extraido[:2000]  # Primeros 2000 caracteres
            vector = self.generar_embedding(texto_muestra)
            if vector:
                vectores['texto_extraido_vector'] = vector
        
        # 2. Vector del análisis
        analisis = doc_data.get('analisis', '')
        if analisis:
            vector = self.generar_embedding(analisis)
            if vector:
                vectores['analisis_vector'] = vector
        
        # 3. Vector de personas
        personas_texto = doc_data.get('personas_texto', '')
        if personas_texto:
            vector = self.generar_embedding(f"Personas mencionadas: {personas_texto}")
            if vector:
                vectores['personas_vector'] = vector
        
        # 4. Vector de organizaciones
        organizaciones_texto = doc_data.get('organizaciones_texto', '')
        if organizaciones_texto:
            vector = self.generar_embedding(f"Organizaciones mencionadas: {organizaciones_texto}")
            if vector:
                vectores['organizaciones_vector'] = vector
        
        # 5. Vector de lugares
        lugares_texto = doc_data.get('lugares_texto', '')
        if lugares_texto:
            vector = self.generar_embedding(f"Lugares mencionados: {lugares_texto}")
            if vector:
                vectores['lugares_vector'] = vector
        
        logger.info(f"Documento {documento_id}: {len(vectores)} vectores generados")
        return vectores
    
    def vectorizar_batch_documentos(self, batch_size: int = 3, max_documentos: Optional[int] = None) -> Dict[str, Any]:
        """Vectoriza documentos en lotes pequeños"""
        logger.info(f"Iniciando vectorización en lotes (batch_size={batch_size})")
        
        resultados = {
            'documentos_procesados': 0,
            'vectores_generados': 0,
            'errores': 0,
            'tiempo_inicio': datetime.now(),
            'vectorizaciones': []
        }
        
        offset = 0
        while True:
            # Obtener lote de documentos
            documentos = self.obtener_documentos_para_vectorizar(limite=batch_size, offset=offset)
            
            if not documentos:
                break
            
            logger.info(f"Procesando lote {offset//batch_size + 1}: {len(documentos)} documentos")
            
            # Vectorizar cada documento del lote
            for doc in documentos:
                try:
                    vectores = self.vectorizar_documento_completo(doc)
                    
                    if vectores:
                        vectorizacion = {
                            'documento_id': doc['documento_id'],
                            'archivo': doc.get('archivo', 'unknown'),
                            'vectores': {k: len(v) for k, v in vectores.items()},  # Solo guardar dimensiones para log
                            'timestamp': datetime.now().isoformat(),
                            'num_vectores': len(vectores)
                        }
                        
                        resultados['vectorizaciones'].append(vectorizacion)
                        resultados['vectores_generados'] += len(vectores)
                    
                    resultados['documentos_procesados'] += 1
                    
                    # Guardar cache periódicamente
                    if resultados['documentos_procesados'] % 2 == 0:
                        self._guardar_cache_local()
                    
                except Exception as e:
                    logger.error(f"Error vectorizando documento {doc.get('documento_id', 'unknown')}: {e}")
                    resultados['errores'] += 1
                
                # Verificar límite máximo
                if max_documentos and resultados['documentos_procesados'] >= max_documentos:
                    break
            
            offset += batch_size
            
            # Verificar límite máximo
            if max_documentos and resultados['documentos_procesados'] >= max_documentos:
                break
        
        # Guardar cache final
        self._guardar_cache_local()
        
        resultados['tiempo_fin'] = datetime.now()
        resultados['duracion'] = (resultados['tiempo_fin'] - resultados['tiempo_inicio']).total_seconds()
        
        logger.info(f"Vectorización completada: {resultados['documentos_procesados']} documentos, {resultados['vectores_generados']} vectores")
        
        return resultados
    
    def obtener_estadisticas(self) -> Dict[str, Any]:
        """Obtiene estadísticas del sistema"""
        stats = self.stats.copy()
        stats.update({
            'cache_local_size': len(self.embedding_cache),
            'cache_hit_rate': self.stats['cache_hits'] / max(1, self.stats['cache_hits'] + self.stats['cache_misses']),
            'postgres_disponible': self.postgres_conn is not None,
            'cache_dir': str(self.cache_dir)
        })
        return stats

def main():
    """Función principal para testing"""
    vectorizador = VectorizadorProyecto()
    
    print("🔄 Iniciando sistema de vectorización usando interfaz funcional...")
    
    # Inicializar componentes
    postgres_ok = vectorizador.inicializar_postgres()
    
    print(f"PostgreSQL: {'✅' if postgres_ok else '❌'}")
    
    if not postgres_ok:
        print("❌ No se puede continuar sin PostgreSQL")
        return
    
    # Estadísticas iniciales
    stats = vectorizador.obtener_estadisticas()
    print(f"Cache local: {stats['cache_local_size']} embeddings")
    
    # Vectorizar muestra pequeña
    print("\n🔄 Vectorizando muestra de 2 documentos...")
    resultados = vectorizador.vectorizar_batch_documentos(batch_size=2, max_documentos=2)
    
    print(f"✅ Resultados:")
    print(f"   - Documentos procesados: {resultados['documentos_procesados']}")
    print(f"   - Vectores generados: {resultados['vectores_generados']}")
    print(f"   - Errores: {resultados['errores']}")
    print(f"   - Duración: {resultados['duracion']:.2f}s")
    
    # Mostrar detalles de vectorizaciones exitosas
    for i, v in enumerate(resultados['vectorizaciones'][:3]):
        print(f"   📄 Doc {v['documento_id']}: {v['num_vectores']} vectores")

if __name__ == "__main__":
    main()
