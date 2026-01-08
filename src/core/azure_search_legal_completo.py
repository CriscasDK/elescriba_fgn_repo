"""
Sistema Azure Search para Documentos Legales con Trazabilidad Extrema
Implementa búsqueda vectorizada con todos los metadatos legales necesarios
Fecha: Agosto 14, 2025
Estado: SISTEMA PRODUCTIVO - TRAZABILIDAD LEGAL COMPLETA
"""

import os
import httpx
import logging
from typing import List, Dict, Optional
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI
from dotenv import load_dotenv

# Importar el enriquecedor de metadatos
try:
    from .enriquecedor_metadatos import get_enriquecedor
except ImportError:
    # Fallback para importación directa
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from enriquecedor_metadatos import get_enriquecedor

# Cargar variables de entorno
load_dotenv('.env.gpt41')

class AzureSearchLegalCompleto:
    """
    Cliente Azure Search especializado para documentos legales
    con trazabilidad extrema y metadatos completos
    """
    
    def __init__(self):
        # Configuración Azure Search
        self.search_endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
        self.search_key = os.getenv('AZURE_SEARCH_KEY')
        self.index_name = os.getenv('AZURE_SEARCH_INDEX_NAME', 'exhaustive-legal-chunks-v2')
        
        # Cliente Azure Search
        self.client = SearchClient(
            endpoint=self.search_endpoint,
            index_name=self.index_name,
            credential=AzureKeyCredential(self.search_key)
        )
        
        # Cliente OpenAI para embeddings
        custom_http_client = httpx.Client()
        self.openai_client = AzureOpenAI(
            api_key=os.getenv('AZURE_OPENAI_API_KEY'),
            api_version=os.getenv('AZURE_OPENAI_API_VERSION', '2024-12-01-preview'),
            azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
            http_client=custom_http_client
        )
        
        logging.info(f"🔍 Azure Search Legal inicializado: {self.search_endpoint}")
        logging.info(f"📋 Índice: {self.index_name}")
    
    def generar_embedding(self, texto: str) -> List[float]:
        """Genera embedding para un texto usando Azure OpenAI"""
        try:
            response = self.openai_client.embeddings.create(
                input=texto,
                model="text-embedding-ada-002"
            )
            return response.data[0].embedding
        except Exception as e:
            logging.error(f"❌ Error generando embedding: {e}")
            raise
    
    def buscar_chunks_con_trazabilidad(self, query: str, top_k: int = 8) -> List[Dict]:
        """
        Busca chunks con TRAZABILIDAD LEGAL EXTREMA
        Retorna TODOS los metadatos necesarios para auditoría legal
        """
        try:
            print(f"🔍 Iniciando búsqueda con trazabilidad legal extrema...")
            print(f"📝 Query: {query}")
            print(f"🎯 Top K: {top_k}")
            
            # Generar embedding de la consulta
            embedding_query = self.generar_embedding(query)
            print(f"🧠 Embedding generado: {len(embedding_query)} dimensiones")
            
            # Configurar búsqueda vectorizada
            vector_query = VectorizedQuery(
                vector=embedding_query,
                k_nearest_neighbors=top_k,
                fields="content_vector"
            )
            
            # Realizar búsqueda - SELECCIONAR TODOS LOS CAMPOS LEGALES
            results = self.client.search(
                search_text=None,
                vector_queries=[vector_query],
                select=[
                    # IDENTIFICACIÓN LEGAL CRÍTICA
                    "chunk_id", "nuc", "documento_id", "nombre_archivo", "tipo_documento",
                    # UBICACIÓN EXACTA EN DOCUMENTO  
                    "pagina", "parrafo", "posicion_en_doc",
                    # CONTENIDO Y ANÁLISIS
                    "texto_chunk", "resumen_chunk", "tamano_chunk",
                    # ENTIDADES EXTRAÍDAS
                    "personas_chunk", "lugares_chunk", "fechas_chunk",
                    # METADATOS DE CALIDAD Y PROCEDENCIA
                    "legal_significance", "chunk_type", "entidad_productora",
                    "fecha_indexacion", "content_vector"
                ],
                top=top_k
            )
            
            # Procesar resultados CON TRAZABILIDAD LEGAL COMPLETA
            chunks_con_trazabilidad = []
            
            for i, result in enumerate(results, 1):
                # Extraer score de relevancia
                score_relevancia = getattr(result, '@search.score', 0.0)
                
                # Construir chunk con TODA la información legal
                chunk_legal = {
                    # ========== IDENTIFICACIÓN LEGAL CRÍTICA ==========
                    'chunk_id': result.get('chunk_id', 'NO_DISPONIBLE'),
                    'nuc': result.get('nuc', 'NO_DISPONIBLE'),
                    'documento_id': result.get('documento_id', 'NO_DISPONIBLE'), 
                    'nombre_archivo': result.get('nombre_archivo', 'NO_DISPONIBLE'),
                    'tipo_documento': result.get('tipo_documento', 'NO_ESPECIFICADO'),
                    'entidad_productora': result.get('entidad_productora', 'NO_ESPECIFICADA'),
                    
                    # ========== UBICACIÓN EXACTA EN DOCUMENTO ==========
                    'pagina': result.get('pagina', 0),
                    'parrafo': result.get('parrafo', 0),
                    'posicion_en_doc': result.get('posicion_en_doc', 0),
                    
                    # ========== CONTENIDO LEGAL ==========
                    'texto_chunk': result.get('texto_chunk', 'CONTENIDO_NO_DISPONIBLE'),
                    'resumen_chunk': result.get('resumen_chunk', ''),
                    'tamano_chunk': result.get('tamano_chunk', 0),
                    
                    # ========== ENTIDADES EXTRAÍDAS ==========
                    'personas_chunk': result.get('personas_chunk', ''),
                    'lugares_chunk': result.get('lugares_chunk', ''),
                    'fechas_chunk': result.get('fechas_chunk', ''),
                    
                    # ========== METADATOS DE CALIDAD ==========
                    'score_relevancia': round(score_relevancia, 4),
                    'legal_significance': result.get('legal_significance', 0.0),
                    'chunk_type': result.get('chunk_type', 'general_content'),
                    'fecha_indexacion': result.get('fecha_indexacion', 'NO_DISPONIBLE'),
                    
                    # ========== INFORMACIÓN DE AUDITORÍA ==========
                    'ranking_busqueda': i,
                    'metodo_busqueda': 'azure_search_vectorizado',
                    'timestamp_consulta': os.environ.get('REQUEST_TIMESTAMP', '2025-08-14'),
                    
                    # ========== COMPATIBILIDAD CON CÓDIGO EXISTENTE ==========
                    'texto': result.get('texto_chunk', ''),  # Para retrocompatibilidad
                    'archivo': result.get('nombre_archivo', ''),  # Para retrocompatibilidad
                    'score': score_relevancia  # Para retrocompatibilidad
                }
                
                chunks_con_trazabilidad.append(chunk_legal)
                
                # Log detallado para auditoría
                print(f"📄 Chunk {i}: {chunk_legal['chunk_id']}")
                print(f"   📋 NUC: {chunk_legal['nuc']}")
                print(f"   📄 Archivo: {chunk_legal['nombre_archivo']}")
                print(f"   📍 Página {chunk_legal['pagina']}, Párrafo {chunk_legal['parrafo']}")
                print(f"   ⭐ Score: {chunk_legal['score_relevancia']}")
                print(f"   📏 Tamaño: {chunk_legal['tamano_chunk']} caracteres")
            
            print(f"✅ Búsqueda completada: {len(chunks_con_trazabilidad)} chunks con trazabilidad legal")
            
            # 🚀 ENRIQUECIMIENTO EN TIEMPO REAL
            print(f"🔍 Iniciando enriquecimiento de metadatos desde PostgreSQL...")
            try:
                enriquecedor = get_enriquecedor()
                chunks_enriquecidos = enriquecedor.enriquecer_lista_resultados(chunks_con_trazabilidad)
                print(f"✅ Enriquecimiento completado: {len(chunks_enriquecidos)} chunks con metadatos completos")
                return chunks_enriquecidos
            except Exception as e:
                print(f"⚠️ Error en enriquecimiento, devolviendo resultados originales: {e}")
                return chunks_con_trazabilidad
            
        except Exception as e:
            print(f"❌ Error en búsqueda con trazabilidad legal: {str(e)}")
            logging.error(f"Error detallado: {e}")
            return []
    
    def generar_respuesta_con_trazabilidad(self, pregunta: str, chunks: List[Dict]) -> Dict:
        """
        Genera respuesta incluyendo TODA la trazabilidad legal
        """
        try:
            if not chunks:
                return {
                    'respuesta': 'No se encontraron documentos relevantes para esta consulta.',
                    'trazabilidad_completa': [],
                    'resumen_trazabilidad': 'Sin documentos encontrados',
                    'metadatos_consulta': {
                        'total_chunks': 0,
                        'total_documentos': 0,
                        'score_promedio': 0.0
                    }
                }
            
            # ========== CONSTRUIR CONTEXTO CON TRAZABILIDAD ==========
            contexto_con_trazabilidad = "DOCUMENTOS LEGALES ENCONTRADOS CON TRAZABILIDAD COMPLETA:\n\n"
            
            trazabilidad_completa = []
            documentos_unicos = set()
            
            for i, chunk in enumerate(chunks, 1):
                # Agregar a trazabilidad completa
                info_trazabilidad = {
                    'ranking': i,
                    'chunk_id': chunk['chunk_id'],
                    'nuc': chunk['nuc'],
                    'documento': chunk['nombre_archivo'],
                    'tipo_documento': chunk['tipo_documento'],
                    'pagina': chunk['pagina'],
                    'parrafo': chunk['parrafo'],
                    'score_relevancia': chunk['score_relevancia'],
                    'legal_significance': chunk['legal_significance'],
                    'texto_chunk': chunk['texto_chunk'][:200] + '...' if len(chunk['texto_chunk']) > 200 else chunk['texto_chunk'],
                    'entidades_personas': chunk['personas_chunk'],
                    'entidades_lugares': chunk['lugares_chunk'],
                    'entidades_fechas': chunk['fechas_chunk']
                }
                trazabilidad_completa.append(info_trazabilidad)
                documentos_unicos.add(chunk['nombre_archivo'])
                
                # Construir contexto para el LLM
                contexto_con_trazabilidad += f"DOCUMENTO {i}:\n"
                contexto_con_trazabilidad += f"• NUC: {chunk['nuc']}\n"
                contexto_con_trazabilidad += f"• Archivo: {chunk['nombre_archivo']}\n"
                contexto_con_trazabilidad += f"• Tipo: {chunk['tipo_documento']}\n"
                contexto_con_trazabilidad += f"• Ubicación: Página {chunk['pagina']}, Párrafo {chunk['parrafo']}\n"
                contexto_con_trazabilidad += f"• Score de Relevancia: {chunk['score_relevancia']}\n"
                contexto_con_trazabilidad += f"• Significancia Legal: {chunk['legal_significance']}\n"
                if chunk['personas_chunk']:
                    contexto_con_trazabilidad += f"• Personas Mencionadas: {chunk['personas_chunk']}\n"
                if chunk['lugares_chunk']:
                    contexto_con_trazabilidad += f"• Lugares Mencionados: {chunk['lugares_chunk']}\n"
                if chunk['fechas_chunk']:
                    contexto_con_trazabilidad += f"• Fechas Mencionadas: {chunk['fechas_chunk']}\n"
                contexto_con_trazabilidad += f"• CONTENIDO: {chunk['texto_chunk']}\n"
                contexto_con_trazabilidad += "-" * 100 + "\n\n"
            
            # ========== GENERAR RESPUESTA CON LLM ==========
            prompt_legal = f"""
Eres un experto analista de documentos jurídicos especializizado en crímenes de lesa humanidad y violaciones de derechos humanos.

INSTRUCCIONES CRÍTICAS PARA TRAZABILIDAD LEGAL:
1. SIEMPRE menciona la fuente exacta: NUC, archivo, página y párrafo
2. Cita textualmente cuando sea relevante
3. Indica el score de relevancia de cada fuente
4. Mantén total objetividad y rigor legal
5. Si algo no está en los documentos, no lo inventes

PREGUNTA DEL USUARIO:
{pregunta}

DOCUMENTOS LEGALES CON TRAZABILIDAD COMPLETA:
{contexto_con_trazabilidad}

GENERA UNA RESPUESTA QUE:
- Responda directamente a la pregunta
- Cite las fuentes específicas (NUC, archivo, página, párrafo)
- Use citas textuales cuando sea relevante
- Indique el nivel de relevancia de cada fuente
- Mantenga rigor legal y objetividad

RESPUESTA:
"""

            response = self.openai_client.chat.completions.create(
                model=os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4'),
                messages=[
                    {"role": "system", "content": "Eres un experto analista jurídico especializado en documentos de crímenes de lesa humanidad. Siempre citas fuentes exactas y mantienes rigor legal absoluto."},
                    {"role": "user", "content": prompt_legal}
                ],
                max_tokens=2000,
                temperature=0.2  # Baja temperatura para máxima precisión
            )
            
            respuesta_generada = response.choices[0].message.content
            
            # ========== CALCULAR MÉTRICAS ==========
            scores = [chunk['score_relevancia'] for chunk in chunks]
            score_promedio = sum(scores) / len(scores) if scores else 0.0
            
            # ========== CONSTRUIR RESPUESTA COMPLETA ==========
            resultado_completo = {
                'respuesta': respuesta_generada,
                'trazabilidad_completa': trazabilidad_completa,
                'resumen_trazabilidad': {
                    'total_chunks_analizados': len(chunks),
                    'total_documentos_unicos': len(documentos_unicos),
                    'score_relevancia_promedio': round(score_promedio, 4),
                    'score_relevancia_maximo': max(scores) if scores else 0.0,
                    'score_relevancia_minimo': min(scores) if scores else 0.0,
                    'documentos_fuente': list(documentos_unicos),
                    'metodo_busqueda': 'azure_search_vectorizado_con_trazabilidad_legal'
                },
                'metadatos_consulta': {
                    'pregunta_original': pregunta,
                    'timestamp_procesamiento': '2025-08-14T' + str(os.times().elapsed),
                    'tokens_usados': response.usage.total_tokens if hasattr(response, 'usage') else 0,
                    'modelo_utilizado': os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4')
                }
            }
            
            return resultado_completo
            
        except Exception as e:
            logging.error(f"❌ Error generando respuesta con trazabilidad: {e}")
            return {
                'respuesta': f'Error generando respuesta: {str(e)}',
                'trazabilidad_completa': [],
                'resumen_trazabilidad': 'Error en procesamiento',
                'metadatos_consulta': {'error': str(e)}
            }

    def consulta_completa_con_trazabilidad(self, pregunta: str, top_k: int = 8) -> Dict:
        """
        Método principal que combina búsqueda y generación con trazabilidad completa
        """
        print(f"\n{'='*80}")
        print(f"🔍 CONSULTA LEGAL CON TRAZABILIDAD EXTREMA")
        print(f"{'='*80}")
        print(f"📝 Pregunta: {pregunta}")
        print(f"🎯 Chunks a buscar: {top_k}")
        
        # Buscar chunks con trazabilidad
        chunks = self.buscar_chunks_con_trazabilidad(pregunta, top_k)
        
        # Generar respuesta con trazabilidad
        resultado = self.generar_respuesta_con_trazabilidad(pregunta, chunks)
        
        print(f"✅ Consulta completada con {len(chunks)} chunks analizados")
        print(f"{'='*80}\n")
        
        return resultado

# Función de testing
def test_sistema_legal_completo():
    """Prueba del sistema con trazabilidad legal extrema"""
    try:
        sistema = AzureSearchLegalCompleto()
        
        # Consulta de prueba
        pregunta = "¿Qué información hay sobre víctimas del conflicto armado?"
        
        resultado = sistema.consulta_completa_con_trazabilidad(pregunta, top_k=5)
        
        print("🔍 RESULTADO CON TRAZABILIDAD LEGAL EXTREMA:")
        print("-" * 80)
        print("📝 RESPUESTA:")
        print(resultado['respuesta'])
        print("-" * 80)
        print("📋 RESUMEN DE TRAZABILIDAD:")
        print(f"• Total chunks analizados: {resultado['resumen_trazabilidad']['total_chunks_analizados']}")
        print(f"• Documentos únicos: {resultado['resumen_trazabilidad']['total_documentos_unicos']}")
        print(f"• Score promedio: {resultado['resumen_trazabilidad']['score_relevancia_promedio']}")
        print("-" * 80)
        print("📄 FUENTES DETALLADAS:")
        for i, fuente in enumerate(resultado['trazabilidad_completa'][:3], 1):
            print(f"{i}. NUC: {fuente['nuc']} | Archivo: {fuente['documento']}")
            print(f"   Página {fuente['pagina']}, Párrafo {fuente['parrafo']} | Score: {fuente['score_relevancia']}")
            print(f"   Texto: {fuente['texto_chunk'][:100]}...")
            print()
        
    except Exception as e:
        print(f"❌ Error en prueba: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sistema_legal_completo()
