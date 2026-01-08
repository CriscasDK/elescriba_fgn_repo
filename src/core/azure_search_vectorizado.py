"""
Sistema RAG Vectorizado con Azure Cognitive Search
Implementa búsqueda semántica usando embeddings para documentos jurídicos
"""

import os
import asyncio
import logging
import httpx
from typing import List, Dict, Optional
from dataclasses import dataclass
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI

@dataclass
class DocumentoCompleto:
    """Representa un documento completo con metadatos para filtrado"""
    id: str
    expediente_nuc: str
    tipo_documental: str
    nombre_archivo: str
    fecha_documento: str
    departamento: str
    municipio: str
    ubicacion: str
    organizacion_responsable: str
    contenido_completo: str
    score: float
    metadata: Dict

@dataclass
class DocumentoChunk:
    """Representa un chunk de documento con metadatos"""
    id: str
    expediente_nuc: str
    tipo_documental: str
    nombre_archivo: str
    contenido: str
    analisis: str
    score: float
    metadata: Dict

class AzureSearchVectorizado:
    """Cliente para búsqueda vectorizada en Azure Cognitive Search con búsqueda cruzada"""
    
    def __init__(self):
        self.search_endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
        self.search_key = os.getenv('AZURE_SEARCH_KEY')
        
        # Índices disponibles
        self.index_chunks = os.getenv('AZURE_SEARCH_INDEX_NAME', 'exhaustive-legal-chunks-v2')
        self.index_documentos = 'exhaustive-legal-index'  # Índice de documentos completos
        
        # Cliente OpenAI para embeddings con HTTP client personalizado
        custom_http_client = httpx.Client()
        self.openai_client = AzureOpenAI(
            api_key=os.getenv('AZURE_OPENAI_API_KEY'),
            api_version=os.getenv('AZURE_OPENAI_API_VERSION', '2024-12-01-preview'),
            azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
            http_client=custom_http_client
        )
        
        # Clientes Azure Search para ambos índices
        self.search_client_chunks = SearchClient(
            endpoint=self.search_endpoint,
            index_name=self.index_chunks,
            credential=AzureKeyCredential(self.search_key)
        )
        
        self.search_client_documentos = SearchClient(
            endpoint=self.search_endpoint,
            index_name=self.index_documentos,
            credential=AzureKeyCredential(self.search_key)
        )
        
        # Para compatibilidad hacia atrás
        self.search_client = self.search_client_chunks
        self.index_name = self.index_chunks
        
        logging.info(f"Azure Search inicializado: {self.search_endpoint}")
        logging.info(f"Índice chunks: {self.index_chunks}")
        logging.info(f"Índice documentos: {self.index_documentos}")
    
    async def generar_embedding(self, texto: str) -> List[float]:
        """Genera embedding para un texto usando Azure OpenAI"""
        try:
            response = self.openai_client.embeddings.create(
                input=texto,
                model="text-embedding-ada-002"  # Modelo de embeddings
            )
            return response.data[0].embedding
        except Exception as e:
            logging.error(f"Error generando embedding: {e}")
            raise
    
    async def buscar_semanticamente(self, pregunta: str, top_k: int = 10) -> List[DocumentoChunk]:
        """Realiza búsqueda semántica usando embeddings"""
        try:
            # Generar embedding de la pregunta
            pregunta_embedding = await self.generar_embedding(pregunta)
            
            # Crear consulta vectorizada
            vector_query = VectorizedQuery(
                vector=pregunta_embedding,
                k_nearest_neighbors=top_k,
                fields="content_vector"  # Campo vector en el índice
            )
            
            # Ejecutar búsqueda
            results = self.search_client.search(
                search_text=pregunta,
                vector_queries=[vector_query],
                select=[
                    "chunk_id", "nuc", "tipo_documento", "nombre_archivo",
                    "texto_chunk", "resumen_chunk", "pagina", "parrafo"
                ],
                top=top_k
            )
            
            # Procesar resultados
            chunks = []
            for result in results:
                chunk = DocumentoChunk(
                    id=result.get("chunk_id", ""),
                    expediente_nuc=result.get("nuc", ""),
                    tipo_documental=result.get("tipo_documento", ""),
                    nombre_archivo=result.get("nombre_archivo", ""),
                    contenido=result.get("texto_chunk", "")[:1000],  # Limitar tamaño
                    analisis=result.get("resumen_chunk", "")[:500],
                    score=result.get("@search.score", 0.0),
                    metadata={
                        "pagina": result.get("pagina"),
                        "parrafo": result.get("parrafo"),
                        "search_score": result.get("@search.score")
                    }
                )
                chunks.append(chunk)
            
            logging.info(f"Búsqueda semántica completada: {len(chunks)} chunks encontrados")
            return chunks
            
        except Exception as e:
            logging.error(f"Error en búsqueda semántica: {e}")
            raise
    
    async def buscar_hibrida(self, pregunta: str, filtros: Dict = None, top_k: int = 10) -> List[DocumentoChunk]:
        """Búsqueda híbrida: semántica + palabras clave + filtros"""
        try:
            # Generar embedding
            pregunta_embedding = await self.generar_embedding(pregunta)
            
            # Consulta vectorizada
            vector_query = VectorizedQuery(
                vector=pregunta_embedding,
                k_nearest_neighbors=top_k,
                fields="content_vector"
            )
            
            # Construir filtro OData si se especifica
            filter_expression = None
            if filtros:
                filter_parts = []
                if "expediente" in filtros:
                    filter_parts.append(f"expediente_nuc eq '{filtros['expediente']}'")
                if "expedientes_multiples" in filtros:
                    filter_parts.append(filtros["expedientes_multiples"])
                if "tipo_documental" in filtros:
                    filter_parts.append(f"tipo_documental eq '{filtros['tipo_documental']}'")
                if "fecha_inicio" in filtros and "fecha_fin" in filtros:
                    filter_parts.append(f"fecha_documento ge {filtros['fecha_inicio']} and fecha_documento le {filtros['fecha_fin']}")
                
                if filter_parts:
                    filter_expression = " and ".join(filter_parts)
            
            # Ejecutar búsqueda híbrida
            results = self.search_client.search(
                search_text=pregunta,
                vector_queries=[vector_query],
                filter=filter_expression,
                select=[
                    "chunk_id", "nuc", "tipo_documento", "nombre_archivo", "archivo",
                    "texto_chunk", "resumen_chunk", "pagina", "parrafo"
                ],
                top=top_k,
                search_mode="all"  # Combina texto y vectores
            )
            
            # Procesar resultados
            chunks = []
            for result in results:
                # Debug: imprimir campos disponibles en el primer resultado
                if len(chunks) == 0:
                    logging.info(f"Campos disponibles en Azure Search: {list(result.keys())}")
                
                chunk = DocumentoChunk(
                    id=result.get("chunk_id", ""),
                    expediente_nuc=result.get("nuc", ""),
                    tipo_documental=result.get("tipo_documento", ""),
                    nombre_archivo=result.get("nombre_archivo", result.get("archivo", "")),  # Fallback a 'archivo'
                    contenido=result.get("texto_chunk", "")[:1000],
                    analisis=result.get("resumen_chunk", "")[:500],
                    score=result.get("@search.score", 0.0),
                    metadata={
                        "pagina": result.get("pagina"),
                        "parrafo": result.get("parrafo"),
                        "search_score": result.get("@search.score"),
                        "filtros_aplicados": filtros
                    }
                )
                chunks.append(chunk)
            
            logging.info(f"Búsqueda híbrida completada: {len(chunks)} chunks con filtros {filtros}")
            return chunks
            
        except Exception as e:
            logging.error(f"Error en búsqueda híbrida: {e}")
            raise
    
    def construir_contexto_rag(self, chunks: List[DocumentoChunk]) -> str:
        """Construye contexto para el LLM a partir de los chunks relevantes"""
        if not chunks:
            return "No se encontraron documentos relevantes."
        
        contexto = "DOCUMENTOS RELEVANTES ENCONTRADOS:\n\n"
        
        for i, chunk in enumerate(chunks, 1):
            contexto += f"DOCUMENTO {i}:\n"
            contexto += f"Expediente: {chunk.expediente_nuc}\n"
            contexto += f"Tipo: {chunk.tipo_documental}\n"
            contexto += f"Relevancia: {chunk.score:.3f}\n"
            
            # Priorizar análisis si está disponible
            if chunk.analisis and chunk.analisis.strip():
                contexto += f"Análisis: {chunk.analisis}\n"
            elif chunk.contenido and chunk.contenido.strip():
                contexto += f"Contenido: {chunk.contenido}\n"
            
            contexto += "-" * 80 + "\n\n"
        
        return contexto
    
    async def generar_respuesta_rag(self, pregunta: str, contexto: str) -> str:
        """Genera respuesta usando LLM con contexto de documentos"""
        try:
            prompt = f"""
Eres un experto analista de documentos jurídicos especializizado en crímenes de lesa humanidad.

PREGUNTA DEL USUARIO:
{pregunta}

CONTEXTO DE DOCUMENTOS RELEVANTES:
{contexto}

INSTRUCCIONES:
1. Analiza el contexto proporcionado de los documentos jurídicos
2. Responde la pregunta de forma clara y precisa
3. Cita información específica de los documentos cuando sea relevante
4. Si no hay información suficiente, indícalo claramente
5. Mantén un tono profesional y objetivo

RESPUESTA:
"""

            response = self.openai_client.chat.completions.create(
                model=os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4'),
                messages=[
                    {"role": "system", "content": "Eres un experto analista jurídico especializado en documentos de crímenes de lesa humanidad."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logging.error(f"Error generando respuesta RAG: {e}")
            raise

        return respuesta

    async def buscar_documentos_completos(self, pregunta: str, filtros: Optional[Dict] = None, top_k: int = 10) -> List[DocumentoCompleto]:
        """Busca en el índice de documentos completos para obtener metadatos de filtrado"""
        try:
            # Generar embedding para la pregunta
            embedding_response = self.openai_client.embeddings.create(
                input=pregunta,
                model="text-embedding-ada-002"
            )
            embedding = embedding_response.data[0].embedding
            
            # Configurar consulta vectorial
            vector_query = VectorizedQuery(
                vector=embedding,
                k_nearest_neighbors=top_k,
                fields="content_vector"  # Campo vector correcto del índice
            )
            
            # Construir filtro OData si se especifica
            filter_expression = None
            if filtros:
                filter_parts = []
                if "expediente" in filtros:
                    filter_parts.append(f"metadatos_nuc eq '{filtros['expediente']}'")
                if "tipo_documental" in filtros:
                    filter_parts.append(f"search.ismatch('{filtros['tipo_documental']}', 'tipo_documento')")
                if "organizacion" in filtros:
                    filter_parts.append(f"search.ismatch('{filtros['organizacion']}', 'metadatos_entidad_productora')")
                if "fecha_inicio" in filtros:
                    filter_parts.append(f"metadatos_fecha_creacion ge '{filtros['fecha_inicio']}'")
                if "fecha_fin" in filtros:
                    filter_parts.append(f"metadatos_fecha_creacion le '{filtros['fecha_fin']}'")
                if "lugares_hechos" in filtros:
                    filter_parts.append(f"search.ismatch('{filtros['lugares_hechos']}', 'lugares_hechos')")
                
                if filter_parts:
                    filter_expression = " and ".join(filter_parts)
            
            # Ejecutar búsqueda en índice de documentos completos
            results = self.search_client_documentos.search(
                search_text=pregunta,
                vector_queries=[vector_query],
                filter=filter_expression,
                select=[
                    "id", "metadatos_nuc", "tipo_documento", "archivo",
                    "metadatos_fecha_creacion", "metadatos_entidad_productora", 
                    "lugares_hechos", "fechas_hechos", "texto_extraido", "analisis"
                ],
                top=top_k,
                search_mode="all"
            )
            
            # Procesar resultados
            documentos = []
            for result in results:
                # Debug: imprimir campos disponibles en el primer resultado
                if len(documentos) == 0:
                    logging.info(f"Campos disponibles en exhaustive-legal-index: {list(result.keys())}")
                
                documento = DocumentoCompleto(
                    id=result.get("id", ""),
                    expediente_nuc=result.get("metadatos_nuc", ""),  # Campo real: metadatos_nuc
                    tipo_documental=result.get("tipo_documento", ""),  # Campo real: tipo_documento
                    nombre_archivo=result.get("archivo", ""),  # Campo real: archivo
                    fecha_documento=result.get("metadatos_fecha_creacion", ""),  # Campo real: metadatos_fecha_creacion
                    departamento=result.get("lugares_hechos", ""),  # Usar lugares_hechos como departamento por ahora
                    municipio=result.get("lugares_hechos", ""),  # Usar lugares_hechos como municipio por ahora
                    ubicacion=result.get("lugares_hechos", ""),  # Campo real: lugares_hechos
                    organizacion_responsable=result.get("metadatos_entidad_productora", ""),  # Campo real: metadatos_entidad_productora
                    contenido_completo=result.get("texto_extraido", "")[:2000] if result.get("texto_extraido") else result.get("analisis", "")[:2000],
                    score=result.get("@search.score", 0.0),
                    metadata={
                        "search_score": result.get("@search.score"),
                        "filtros_aplicados": filtros,
                        "lugares_hechos": result.get("lugares_hechos"),
                        "fechas_hechos": result.get("fechas_hechos")
                    }
                )
                documentos.append(documento)
            
            logging.info(f"Búsqueda en documentos completos: {len(documentos)} docs con filtros {filtros}")
            return documentos
            
        except Exception as e:
            logging.error(f"Error en búsqueda de documentos completos: {e}")
            raise

    async def busqueda_cruzada(self, pregunta: str, filtros_documento: Optional[Dict] = None, 
                               filtros_chunk: Optional[Dict] = None, top_k_docs: int = 20, 
                               top_k_chunks: int = 5) -> tuple[List[DocumentoCompleto], List[DocumentoChunk]]:
        """
        Realiza búsqueda cruzada entre índice de documentos completos y chunks
        
        1. Busca en documentos completos para obtener filtros y metadatos
        2. Usa esos documentos para filtrar chunks relevantes
        3. Retorna ambos conjuntos de resultados
        """
        try:
            # Paso 1: Buscar documentos completos relevantes
            documentos_relevantes = await self.buscar_documentos_completos(
                pregunta, filtros_documento, top_k_docs
            )
            
            # Paso 2: Extraer expedientes de documentos relevantes para filtrar chunks
            expedientes_relevantes = list(set([doc.expediente_nuc for doc in documentos_relevantes if doc.expediente_nuc]))
            
            # Paso 3: Construir filtros mejorados para chunks basados en documentos encontrados
            if isinstance(filtros_chunk, dict):
                filtros_chunk_mejorados = filtros_chunk.copy()
            elif filtros_chunk:
                # Si filtros_chunk es un string u otro tipo, crear diccionario vacío
                logging.warning(f"filtros_chunk esperaba dict pero recibió {type(filtros_chunk)}: {filtros_chunk}")
                filtros_chunk_mejorados = {}
            else:
                filtros_chunk_mejorados = {}
            
            # Si encontramos expedientes relevantes, filtrar chunks por estos expedientes
            if expedientes_relevantes and len(expedientes_relevantes) <= 10:  # Evitar filtros demasiado largos
                expedientes_filter = " or ".join([f"nuc eq '{exp}'" for exp in expedientes_relevantes])
                if "expediente" in filtros_chunk_mejorados:
                    filtros_chunk_mejorados["expedientes_multiples"] = f"({expedientes_filter})"
                else:
                    filtros_chunk_mejorados["expedientes_multiples"] = f"({expedientes_filter})"
            
            # Paso 4: Buscar chunks con filtros mejorados
            chunks_relevantes = await self.buscar_semanticamente(
                pregunta, filtros_chunk_mejorados, top_k_chunks
            )
            
            logging.info(f"Búsqueda cruzada completada: {len(documentos_relevantes)} docs, {len(chunks_relevantes)} chunks")
            return documentos_relevantes, chunks_relevantes
            
        except Exception as e:
            logging.error(f"Error en búsqueda cruzada: {e}")
            raise

    def obtener_metadatos_filtrado(self, documentos: List[DocumentoCompleto]) -> Dict:
        """Extrae metadatos únicos de documentos para construir filtros dinámicos"""
        metadatos = {
            "expedientes": list(set([doc.expediente_nuc for doc in documentos if doc.expediente_nuc])),
            "tipos_documentales": list(set([doc.tipo_documental for doc in documentos if doc.tipo_documental])),
            "lugares": list(set([doc.ubicacion for doc in documentos if doc.ubicacion])),  # lugares_hechos
            "organizaciones": list(set([doc.organizacion_responsable for doc in documentos if doc.organizacion_responsable])),
            "fechas": list(set([doc.fecha_documento for doc in documentos if doc.fecha_documento]))
        }
        
        # Limitar listas muy largas para performance
        for key in metadatos:
            if len(metadatos[key]) > 50:
                metadatos[key] = metadatos[key][:50]
        
        return metadatos

# Función principal para testing
async def test_azure_search():
    """Función de prueba del sistema vectorizado"""
    try:
        azure_search = AzureSearchVectorizado()
        
        # Pregunta de prueba
        pregunta = "¿Qué patrones criminales se reconocen en los documentos?"
        
        print(f"🔍 Probando búsqueda vectorizada...")
        print(f"Pregunta: {pregunta}")
        
        # Búsqueda semántica
        chunks = await azure_search.buscar_semanticamente(pregunta, top_k=5)
        print(f"✅ Encontrados {len(chunks)} chunks relevantes")
        
        # Construir contexto
        contexto = azure_search.construir_contexto_rag(chunks)
        print(f"📄 Contexto construido: {len(contexto)} caracteres")
        
        # Generar respuesta
        respuesta = await azure_search.generar_respuesta_rag(pregunta, contexto)
        print(f"🤖 Respuesta generada:")
        print("-" * 80)
        print(respuesta)
        print("-" * 80)
        
    except Exception as e:
        print(f"❌ Error en prueba: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_azure_search())
