#!/usr/bin/env python3
"""
Sistema de Vectorización Completa para RAG Semántico
Implementa vectorización de múltiples campos con fallback local
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
    chunk_id: str
    dimensiones: int
    timestamp: datetime
    hash_contenido: str

@dataclass
class ConsultaVectorial:
    """Configuración para consulta vectorial"""
    texto_consulta: str
    campos_objetivo: List[str]  # ['texto_chunk', 'resumen_chunk', 'personas_chunk', 'contenido_completo']
    k_resultados: int = 10
    umbral_similitud: float = 0.7
    filtros_adicionales: Optional[Dict[str, Any]] = None
    usar_hibrido: bool = True  # Combinar texto + vector

class VectorizadorCompleto:
    """Sistema completo de vectorización para RAG semántico"""
    
    def __init__(self, config_file: str = '.env.gpt41'):
        self.config_file = config_file
        self.cache_dir = Path("cache/embeddings")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Cargar configuración
        self._cargar_config()
        
        # Inicializar componentes
        self.azure_openai = None
        self.azure_search = None
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
            # Azure OpenAI
            'azure_openai_key': os.getenv('AZURE_OPENAI_API_KEY'),  # Usar AZURE_OPENAI_API_KEY como en interfaz_fiscales.py
            'azure_openai_endpoint': os.getenv('AZURE_OPENAI_ENDPOINT'),
            'azure_openai_deployment': os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4.1'),
            'azure_openai_api_version': os.getenv('AZURE_OPENAI_API_VERSION', '2024-12-01-preview'),
            
            # PostgreSQL
            'postgres_host': os.getenv('POSTGRES_HOST', 'localhost'),
            'postgres_port': int(os.getenv('POSTGRES_PORT', 5432)),
            'postgres_db': os.getenv('POSTGRES_DB'),
            'postgres_user': os.getenv('POSTGRES_USER'),
            'postgres_password': os.getenv('POSTGRES_PASSWORD'),
            
            # Azure Search
            'azure_search_endpoint': os.getenv('AZURE_SEARCH_ENDPOINT'),
            'azure_search_key': os.getenv('AZURE_SEARCH_KEY'),
            'azure_search_index_chunks': os.getenv('AZURE_SEARCH_INDEX_CHUNKS', 'exhaustive-legal-chunks'),
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
    
    def inicializar_azure_openai(self) -> bool:
        """Inicializa cliente Azure OpenAI con la misma configuración que interfaz_fiscales.py"""
        try:
            import openai
            # Verificar si la versión soporta AzureOpenAI
            if hasattr(openai, 'AzureOpenAI'):
                from openai import AzureOpenAI
                
                # Verificar que las credenciales están disponibles
                api_key = self.config['azure_openai_key']
                endpoint = self.config['azure_openai_endpoint']
                
                if not api_key or not endpoint:
                    logger.warning("⚠️ Credenciales de Azure OpenAI no configuradas")
                    return False
                
                # Usar la misma configuración exacta que en interfaz_fiscales.py
                self.azure_openai = AzureOpenAI(
                    api_key=api_key,
                    api_version=self.config['azure_openai_api_version'],
                    azure_endpoint=endpoint
                )
                
                # Probar conectividad con embedding simple
                response = self.azure_openai.embeddings.create(
                    input="test",
                    model="text-embedding-ada-002"
                )
                
                logger.info("✅ Azure OpenAI inicializado correctamente")
                return True
            else:
                logger.warning("⚠️ Versión de openai no soporta AzureOpenAI")
                return False
            
        except Exception as e:
            logger.warning(f"⚠️ Azure OpenAI no disponible: {e}")
            return False
    
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
    
    def generar_embedding(self, texto: str, usar_cache: bool = True) -> Optional[List[float]]:
        """Genera embedding para un texto"""
        if not texto or not texto.strip():
            return None
        
        # Verificar cache
        hash_contenido = self._get_hash_contenido(texto)
        if usar_cache and hash_contenido in self.embedding_cache:
            self.stats['cache_hits'] += 1
            return self.embedding_cache[hash_contenido]['vector']
        
        # Generar nuevo embedding
        try:
            if not self.azure_openai:
                if not self.inicializar_azure_openai():
                    return None
            
            response = self.azure_openai.embeddings.create(
                input=texto,
                model="text-embedding-ada-002"
            )
            
            vector = response.data[0].embedding
            
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
            
        except Exception as e:
            logger.error(f"Error generando embedding: {e}")
            return None
    
    def vectorizar_documento_completo(self, doc_data: Dict[str, Any]) -> Dict[str, List[float]]:
        """Vectoriza todos los campos de un documento"""
        documento_id = doc_data.get('documento_id', 'unknown')
        vectores = {}
        
        # 1. Vector del texto principal (texto_extraido)
        texto_extraido = doc_data.get('texto_extraido', '')
        if texto_extraido:
            vector = self.generar_embedding(texto_extraido)
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
            vector = self.generar_embedding(personas_texto)
            if vector:
                vectores['personas_vector'] = vector
        
        # 4. Vector de organizaciones
        organizaciones_texto = doc_data.get('organizaciones_texto', '')
        if organizaciones_texto:
            vector = self.generar_embedding(organizaciones_texto)
            if vector:
                vectores['organizaciones_vector'] = vector
        
        # 5. Vector de lugares
        lugares_texto = doc_data.get('lugares_texto', '')
        if lugares_texto:
            vector = self.generar_embedding(lugares_texto)
            if vector:
                vectores['lugares_vector'] = vector
        
        # 6. Vector de contenido completo (combinado)
        contenido_completo = self._crear_contenido_documento_completo(doc_data)
        if contenido_completo:
            vector = self.generar_embedding(contenido_completo)
            if vector:
                vectores['contenido_completo_vector'] = vector
        
        logger.info(f"Documento {documento_id}: {len(vectores)} vectores generados")
        return vectores
    
    def _crear_contenido_documento_completo(self, doc_data: Dict[str, Any]) -> str:
        """Crea contenido completo combinando múltiples campos del documento"""
        partes = []
        
        # Información del documento
        archivo = doc_data.get('archivo', '')
        if archivo:
            partes.append(f"Archivo: {archivo}")
        
        # NUC y caso
        nuc = doc_data.get('nuc', '')
        if nuc:
            partes.append(f"NUC: {nuc}")
        
        # Entidad productora
        entidad = doc_data.get('entidad_productora', '')
        if entidad:
            partes.append(f"Entidad: {entidad}")
        
        # Despacho
        despacho = doc_data.get('despacho', '')
        if despacho:
            partes.append(f"Despacho: {despacho}")
        
        # Texto principal
        texto = doc_data.get('texto_extraido', '')
        if texto:
            partes.append(f"Contenido: {texto[:1000]}")  # Primeros 1000 chars
        
        # Análisis
        analisis = doc_data.get('analisis', '')
        if analisis:
            partes.append(f"Análisis: {analisis}")
        
        # Personas mencionadas
        personas = doc_data.get('personas_texto', '')
        if personas:
            partes.append(f"Personas: {personas}")
        
        # Organizaciones mencionadas
        organizaciones = doc_data.get('organizaciones_texto', '')
        if organizaciones:
            partes.append(f"Organizaciones: {organizaciones}")
        
        # Lugares mencionados
        lugares = doc_data.get('lugares_texto', '')
        if lugares:
            partes.append(f"Lugares: {lugares}")
        
        return "\n".join(partes)
    
    def obtener_documentos_para_vectorizar(self, limite: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
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
            (SELECT string_agg(p.nombre, ', ') FROM personas p WHERE p.documento_id = d.id) as personas_texto,
            -- Obtener organizaciones asociadas  
            (SELECT string_agg(o.nombre, ', ') FROM organizaciones o WHERE o.documento_id = d.id) as organizaciones_texto,
            -- Obtener lugares asociados
            (SELECT string_agg(al.nombre, ', ') FROM analisis_lugares al WHERE al.documento_id = d.id) as lugares_texto
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
                
                chunks = []
                for row in rows:
                    doc = dict(zip(columns, row))
                    chunks.append(doc)
                
                return chunks
                
        except Exception as e:
            logger.error(f"Error obteniendo documentos: {e}")
            return []
    
    def vectorizar_batch_documentos(self, batch_size: int = 10, max_documentos: Optional[int] = None) -> Dict[str, Any]:
        """Vectoriza documentos en lotes"""
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
                            'vectores': vectores,
                            'timestamp': datetime.now().isoformat(),
                            'num_vectores': len(vectores)
                        }
                        
                        resultados['vectorizaciones'].append(vectorizacion)
                        resultados['vectores_generados'] += len(vectores)
                    
                    resultados['documentos_procesados'] += 1
                    
                    # Guardar cache periódicamente
                    if resultados['documentos_procesados'] % 5 == 0:
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
    
    def buscar_vectorial_local(self, consulta: str, campos_objetivo: List[str], k: int = 10) -> List[Dict[str, Any]]:
        """Búsqueda vectorial usando cache local"""
        # Generar embedding de la consulta
        vector_consulta = self.generar_embedding(consulta)
        if not vector_consulta:
            return []
        
        # Buscar en cache local
        resultados = []
        
        for hash_content, cached_item in self.embedding_cache.items():
            if 'vector' not in cached_item:
                continue
            
            # Calcular similitud coseno
            vector_cached = cached_item['vector']
            similitud = self._calcular_similitud_coseno(vector_consulta, vector_cached)
            
            resultado = {
                'hash': hash_content,
                'similitud': similitud,
                'texto': cached_item.get('texto', ''),
                'timestamp': cached_item.get('timestamp', ''),
                'dimensiones': cached_item.get('dimensiones', 0)
            }
            
            resultados.append(resultado)
        
        # Ordenar por similitud descendente
        resultados.sort(key=lambda x: x['similitud'], reverse=True)
        
        return resultados[:k]
    
    def _calcular_similitud_coseno(self, vector1: List[float], vector2: List[float]) -> float:
        """Calcula similitud coseno entre dos vectores"""
        try:
            vec1 = np.array(vector1)
            vec2 = np.array(vector2)
            
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return float(dot_product / (norm1 * norm2))
            
        except Exception as e:
            logger.error(f"Error calculando similitud: {e}")
            return 0.0
    
    def obtener_estadisticas(self) -> Dict[str, Any]:
        """Obtiene estadísticas del sistema"""
        stats = self.stats.copy()
        stats.update({
            'cache_local_size': len(self.embedding_cache),
            'cache_hit_rate': self.stats['cache_hits'] / max(1, self.stats['cache_hits'] + self.stats['cache_misses']),
            'azure_openai_disponible': self.azure_openai is not None,
            'postgres_disponible': self.postgres_conn is not None,
            'cache_dir': str(self.cache_dir)
        })
        return stats

def main():
    """Función principal para testing"""
    vectorizador = VectorizadorCompleto()
    
    print("🔄 Inicializando sistema de vectorización completa...")
    
    # Inicializar componentes
    azure_ok = vectorizador.inicializar_azure_openai()
    postgres_ok = vectorizador.inicializar_postgres()
    
    print(f"Azure OpenAI: {'✅' if azure_ok else '❌'}")
    print(f"PostgreSQL: {'✅' if postgres_ok else '❌'}")
    
    if not postgres_ok:
        print("❌ No se puede continuar sin PostgreSQL")
        return
    
    # Estadísticas iniciales
    stats = vectorizador.obtener_estadisticas()
    print(f"Cache local: {stats['cache_local_size']} embeddings")
    
    # Vectorizar muestra pequeña
    print("\n🔄 Vectorizando muestra de 3 documentos...")
    resultados = vectorizador.vectorizar_batch_documentos(batch_size=3, max_documentos=3)
    
    print(f"✅ Resultados:")
    print(f"   - Documentos procesados: {resultados['documentos_procesados']}")
    print(f"   - Vectores generados: {resultados['vectores_generados']}")
    print(f"   - Errores: {resultados['errores']}")
    print(f"   - Duración: {resultados['duracion']:.2f}s")
    
    # Probar búsqueda vectorial local
    if vectorizador.embedding_cache:
        print("\n🔍 Probando búsqueda vectorial local...")
        resultados_busqueda = vectorizador.buscar_vectorial_local("homicidio", [], k=3)
        
        print(f"Encontrados {len(resultados_busqueda)} resultados:")
        for i, resultado in enumerate(resultados_busqueda, 1):
            print(f"   {i}. Similitud: {resultado['similitud']:.4f} | {resultado['texto']}")

if __name__ == "__main__":
    main()
