#!/usr/bin/env python3
"""
Sistema RAG para búsqueda semántica en documentos jurídicos vectorizados
- Utiliza el índice vectorizado 'exhaustive-legal-chunks-v2'
- Búsqueda semántica por similitud de vectores
- Retorna chunks, páginas y documentos relevantes
- Mantiene trazabilidad completa para sistema legal
"""

import os
import requests
import logging
from datetime import datetime
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv
import json

# Cargar variables de entorno
load_dotenv('.env.gpt41')

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RAGVectorizado:
    def __init__(self):
        """Inicializar el sistema RAG con índice vectorizado"""
        
        # Configuración Azure Search
        self.endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
        self.key = os.getenv('AZURE_SEARCH_KEY')
        self.index_vectorizado = "exhaustive-legal-chunks-v2"
        
        # Configuración Azure OpenAI para embeddings
        self.openai_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        self.openai_key = os.getenv('AZURE_OPENAI_KEY')
        self.deployment_embedding = "text-embedding-ada-002"
        
        # Cliente de búsqueda vectorizada
        self.search_client = SearchClient(
            endpoint=self.endpoint,
            index_name=self.index_vectorizado,
            credential=AzureKeyCredential(self.key)
        )
        
        logger.info(f"🚀 RAG Vectorizado inicializado")
        logger.info(f"📋 Índice: {self.index_vectorizado}")
        
    def generar_embedding_consulta(self, consulta):
        """Generar embedding para la consulta del usuario"""
        headers = {
            "Content-Type": "application/json",
            "api-key": self.openai_key
        }
        
        data = {
            "input": consulta
        }
        
        try:
            response = requests.post(
                f"{self.openai_endpoint}openai/deployments/{self.deployment_embedding}/embeddings?api-version=2023-05-15",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["data"][0]["embedding"]
            else:
                logger.error(f"❌ Error generando embedding: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Excepción al generar embedding: {str(e)}")
            return None
    
    def busqueda_semantica(self, consulta, top_k=10, threshold_score=0.7):
        """
        Realizar búsqueda semántica en el índice vectorizado
        
        Args:
            consulta: Texto de la consulta del usuario
            top_k: Número máximo de resultados a retornar
            threshold_score: Umbral mínimo de similitud (0-1)
        
        Returns:
            Lista de chunks relevantes con metadatos completos
        """
        logger.info(f"🔍 Búsqueda semántica: '{consulta}'")
        
        # Generar embedding para la consulta
        embedding_consulta = self.generar_embedding_consulta(consulta)
        if not embedding_consulta:
            logger.error("❌ No se pudo generar embedding para la consulta")
            return []
        
        try:
            # Búsqueda vectorial en Azure Search
            results = self.search_client.search(
                search_text="",  # Búsqueda puramente vectorial
                vector_queries=[{
                    "kind": "vector",
                    "vector": embedding_consulta,
                    "k_nearest_neighbors": top_k,
                    "fields": "content_vector"
                }],
                select=[
                    "chunk_id", "documento_id", "pagina", "parrafo",
                    "texto_chunk", "resumen_chunk", "nombre_archivo",
                    "nuc", "tipo_documento", "entidad_productora",
                    "personas_chunk", "lugares_chunk", "fechas_chunk",
                    "legal_significance", "fecha_indexacion"
                ],
                top=top_k
            )
            
            chunks_relevantes = []
            for resultado in results:
                # El score de similitud viene en @search.score
                score = resultado.get('@search.score', 0)
                
                # Filtrar por umbral de similitud
                if score >= threshold_score:
                    chunk_info = {
                        'chunk_id': resultado.get('chunk_id'),
                        'documento_id': resultado.get('documento_id'),
                        'pagina': resultado.get('pagina'),
                        'parrafo': resultado.get('parrafo'),
                        'texto_chunk': resultado.get('texto_chunk'),
                        'resumen_chunk': resultado.get('resumen_chunk'),
                        'nombre_archivo': resultado.get('nombre_archivo'),
                        'nuc': resultado.get('nuc'),
                        'tipo_documento': resultado.get('tipo_documento'),
                        'entidad_productora': resultado.get('entidad_productora'),
                        'personas_chunk': resultado.get('personas_chunk'),
                        'lugares_chunk': resultado.get('lugares_chunk'),
                        'fechas_chunk': resultado.get('fechas_chunk'),
                        'legal_significance': resultado.get('legal_significance'),
                        'fecha_indexacion': resultado.get('fecha_indexacion'),
                        'similarity_score': score
                    }
                    chunks_relevantes.append(chunk_info)
            
            logger.info(f"✅ Encontrados {len(chunks_relevantes)} chunks relevantes (umbral: {threshold_score})")
            return chunks_relevantes
            
        except Exception as e:
            logger.error(f"❌ Error en búsqueda semántica: {str(e)}")
            return []
    
    def obtener_contexto_documento(self, documento_id, pagina_objetivo=None):
        """
        Obtener contexto adicional del documento
        
        Args:
            documento_id: ID del documento
            pagina_objetivo: Página específica (opcional)
        
        Returns:
            Lista de chunks del documento/página para contexto
        """
        try:
            filtro = f"documento_id eq '{documento_id}'"
            if pagina_objetivo:
                filtro += f" and pagina eq {pagina_objetivo}"
            
            results = self.search_client.search(
                search_text="*",
                filter=filtro,
                select=[
                    "chunk_id", "pagina", "parrafo", "texto_chunk",
                    "posicion_en_doc"
                ],
                order_by=["posicion_en_doc asc"],
                top=50  # Limitar contexto
            )
            
            contexto = []
            for resultado in results:
                contexto.append({
                    'chunk_id': resultado.get('chunk_id'),
                    'pagina': resultado.get('pagina'),
                    'parrafo': resultado.get('parrafo'),
                    'texto_chunk': resultado.get('texto_chunk'),
                    'posicion_en_doc': resultado.get('posicion_en_doc')
                })
            
            return sorted(contexto, key=lambda x: x['posicion_en_doc'])
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo contexto: {str(e)}")
            return []
    
    def busqueda_rag_completa(self, consulta, incluir_contexto=True, top_k=5):
        """
        Búsqueda RAG completa con contexto de documentos
        
        Args:
            consulta: Consulta del usuario
            incluir_contexto: Si incluir contexto adicional del documento
            top_k: Número de chunks principales a retornar
        
        Returns:
            Diccionario con resultados y contexto
        """
        logger.info(f"🎯 RAG Completo: '{consulta}'")
        
        # Búsqueda semántica principal
        chunks_principales = self.busqueda_semantica(consulta, top_k=top_k)
        
        if not chunks_principales:
            return {
                'consulta': consulta,
                'chunks_principales': [],
                'contexto_documentos': {},
                'resumen': 'No se encontraron resultados relevantes',
                'timestamp': datetime.now().isoformat()
            }
        
        # Obtener contexto de documentos si se solicita
        contexto_documentos = {}
        if incluir_contexto:
            documentos_procesados = set()
            
            for chunk in chunks_principales:
                doc_id = chunk['documento_id']
                pagina = chunk['pagina']
                
                # Evitar duplicados
                clave_doc = f"{doc_id}_{pagina}"
                if clave_doc not in documentos_procesados:
                    contexto = self.obtener_contexto_documento(doc_id, pagina)
                    if contexto:
                        contexto_documentos[clave_doc] = {
                            'documento_id': doc_id,
                            'pagina': pagina,
                            'chunks_contexto': contexto
                        }
                    documentos_procesados.add(clave_doc)
        
        # Preparar resumen
        resumen = self._generar_resumen_resultados(chunks_principales)
        
        resultado_completo = {
            'consulta': consulta,
            'chunks_principales': chunks_principales,
            'contexto_documentos': contexto_documentos,
            'resumen': resumen,
            'estadisticas': {
                'total_chunks_encontrados': len(chunks_principales),
                'documentos_diferentes': len(set(c['documento_id'] for c in chunks_principales)),
                'score_promedio': sum(c['similarity_score'] for c in chunks_principales) / len(chunks_principales),
                'score_maximo': max(c['similarity_score'] for c in chunks_principales)
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return resultado_completo
    
    def _generar_resumen_resultados(self, chunks):
        """Generar resumen de los resultados encontrados"""
        if not chunks:
            return "No se encontraron resultados relevantes."
        
        documentos = set(c['nombre_archivo'] for c in chunks)
        nucs = set(c['nuc'] for c in chunks if c['nuc'])
        tipos_doc = set(c['tipo_documento'] for c in chunks if c['tipo_documento'])
        
        resumen = f"Se encontraron {len(chunks)} fragmentos relevantes en {len(documentos)} documento(s). "
        
        if nucs:
            resumen += f"NUCs relacionados: {', '.join(list(nucs)[:3])}. "
        
        if tipos_doc:
            resumen += f"Tipos de documento: {', '.join(tipos_doc)}. "
        
        score_promedio = sum(c['similarity_score'] for c in chunks) / len(chunks)
        resumen += f"Relevancia promedio: {score_promedio:.2f}"
        
        return resumen
    
    def verificar_estado_indice(self):
        """Verificar el estado del índice vectorizado"""
        try:
            results = self.search_client.search(
                search_text="*",
                include_total_count=True,
                top=1
            )
            
            total_docs = results.get_count()
            
            # Verificar si hay documentos con vectores
            sample = list(results)
            tiene_vectores = len(sample) > 0 and sample[0].get('content_vector') is not None
            
            logger.info(f"📊 Estado del índice:")
            logger.info(f"   📋 Total documentos: {total_docs:,}")
            logger.info(f"   🔢 Vectorización: {'✅ Activa' if tiene_vectores else '❌ Inactiva'}")
            
            return {
                'total_documentos': total_docs,
                'vectorizacion_activa': tiene_vectores,
                'indice_disponible': True
            }
            
        except Exception as e:
            logger.error(f"❌ Error verificando índice: {str(e)}")
            return {
                'total_documentos': 0,
                'vectorizacion_activa': False,
                'indice_disponible': False
            }

def test_rag_vectorizado():
    """Función de prueba del sistema RAG"""
    rag = RAGVectorizado()
    
    # Verificar estado del índice
    estado = rag.verificar_estado_indice()
    print(f"📊 Estado del índice: {estado}")
    
    if not estado['indice_disponible']:
        print("❌ Índice no disponible")
        return
    
    # Pruebas de búsqueda
    consultas_prueba = [
        "acuerdo de terminación anticipada",
        "medidas cautelares",
        "derechos fundamentales"
    ]
    
    for consulta in consultas_prueba:
        print(f"\n🔍 Probando: '{consulta}'")
        resultado = rag.busqueda_rag_completa(consulta, top_k=3)
        
        if 'estadisticas' in resultado:
            print(f"📈 {resultado['estadisticas']['total_chunks_encontrados']} chunks encontrados")
            print(f"📄 {resultado['estadisticas']['documentos_diferentes']} documentos diferentes")
            print(f"⭐ Score promedio: {resultado['estadisticas']['score_promedio']:.3f}")
            
            for i, chunk in enumerate(resultado['chunks_principales'], 1):
                print(f"   {i}. {chunk['nombre_archivo']} (p.{chunk['pagina']}) - Score: {chunk['similarity_score']:.3f}")
        else:
            print(f"❌ Error en búsqueda: {resultado.get('resumen', 'Error desconocido')}")

if __name__ == "__main__":
    test_rag_vectorizado()
