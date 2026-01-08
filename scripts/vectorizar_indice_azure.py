#!/usr/bin/env python3
"""
Script para agregar campos vectoriales al índice Azure Cognitive Search
Vectoriza múltiples campos para búsqueda semántica completa
"""

import os
import json
import requests
from typing import Dict, Any
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv('.env.gpt41')

class VectorizadorIndiceAzure:
    def __init__(self):
        self.endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
        self.key = os.getenv('AZURE_SEARCH_KEY')
        self.index_name = os.getenv('AZURE_SEARCH_INDEX_CHUNKS', 'exhaustive-legal-chunks')
        self.api_version = "2023-11-01"
        
        if not all([self.endpoint, self.key]):
            raise ValueError("Faltan credenciales de Azure Search en .env.gpt41")
    
    def obtener_esquema_actual(self) -> Dict[str, Any]:
        """Obtiene el esquema actual del índice"""
        url = f"{self.endpoint}/indexes/{self.index_name}?api-version={self.api_version}"
        headers = {
            'Content-Type': 'application/json',
            'api-key': self.key
        }
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error obteniendo esquema: {response.status_code} - {response.text}")
    
    def crear_esquema_vectorizado(self, esquema_actual: Dict[str, Any]) -> Dict[str, Any]:
        """Crea nuevo esquema con campos vectoriales"""
        
        # Campos vectoriales a agregar
        nuevos_campos_vectoriales = [
            {
                "name": "texto_chunk_vector",
                "type": "Collection(Edm.Single)",
                "searchable": True,
                "filterable": False,
                "retrievable": False,  # Los vectores no se recuperan, solo se usan para búsqueda
                "stored": True,
                "sortable": False,
                "facetable": False,
                "key": False,
                "vectorSearchDimensions": 1536,
                "vectorSearchProfileName": "vector-profile-1536"
            },
            {
                "name": "resumen_chunk_vector",
                "type": "Collection(Edm.Single)",
                "searchable": True,
                "filterable": False,
                "retrievable": False,
                "stored": True,
                "sortable": False,
                "facetable": False,
                "key": False,
                "vectorSearchDimensions": 1536,
                "vectorSearchProfileName": "vector-profile-1536"
            },
            {
                "name": "personas_vector",
                "type": "Collection(Edm.Single)",
                "searchable": True,
                "filterable": False,
                "retrievable": False,
                "stored": True,
                "sortable": False,
                "facetable": False,
                "key": False,
                "vectorSearchDimensions": 1536,
                "vectorSearchProfileName": "vector-profile-1536"
            },
            {
                "name": "contenido_completo_vector",
                "type": "Collection(Edm.Single)",
                "searchable": True,
                "filterable": False,
                "retrievable": False,
                "stored": True,
                "sortable": False,
                "facetable": False,
                "key": False,
                "vectorSearchDimensions": 1536,
                "vectorSearchProfileName": "vector-profile-1536"
            }
        ]
        
        # Configuración de búsqueda vectorial
        vector_search = {
            "algorithms": [
                {
                    "name": "cosine-algorithm",
                    "kind": "hnsw",
                    "hnswParameters": {
                        "metric": "cosine",
                        "m": 4,
                        "efConstruction": 400,
                        "efSearch": 500
                    }
                }
            ],
            "profiles": [
                {
                    "name": "vector-profile-1536",
                    "algorithm": "cosine-algorithm",
                    "vectorizer": None  # Usaremos embeddings externos (Azure OpenAI)
                }
            ]
        }
        
        # Configuración de búsqueda semántica
        semantic_search = {
            "configurations": [
                {
                    "name": "semantic-config",
                    "prioritizedFields": {
                        "titleField": {
                            "fieldName": "resumen_chunk"
                        },
                        "prioritizedContentFields": [
                            {
                                "fieldName": "texto_chunk"
                            }
                        ],
                        "prioritizedKeywordsFields": [
                            {
                                "fieldName": "personas_chunk"
                            },
                            {
                                "fieldName": "lugares_chunk"
                            }
                        ]
                    }
                }
            ]
        }
        
        # Crear nuevo esquema
        nuevo_esquema = esquema_actual.copy()
        
        # Agregar campos vectoriales
        nuevo_esquema['fields'].extend(nuevos_campos_vectoriales)
        
        # Agregar configuraciones
        nuevo_esquema['vectorSearch'] = vector_search
        nuevo_esquema['semantic'] = semantic_search
        
        return nuevo_esquema
    
    def actualizar_indice(self, nuevo_esquema: Dict[str, Any]) -> bool:
        """Actualiza el índice con el nuevo esquema"""
        url = f"{self.endpoint}/indexes/{self.index_name}?api-version={self.api_version}"
        headers = {
            'Content-Type': 'application/json',
            'api-key': self.key
        }
        
        response = requests.put(url, headers=headers, json=nuevo_esquema)
        
        if response.status_code in [200, 201]:
            print(f"✅ Índice '{self.index_name}' actualizado exitosamente")
            return True
        else:
            print(f"❌ Error actualizando índice: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return False
    
    def verificar_actualizacion(self) -> Dict[str, Any]:
        """Verifica que la actualización fue exitosa"""
        try:
            esquema = self.obtener_esquema_actual()
            
            # Verificar campos vectoriales
            campos_vectoriales = [f for f in esquema['fields'] if 'vector' in f['name']]
            
            # Verificar configuraciones
            tiene_vector_search = 'vectorSearch' in esquema
            tiene_semantic = 'semantic' in esquema
            
            return {
                'campos_vectoriales': len(campos_vectoriales),
                'nombres_campos_vectoriales': [c['name'] for c in campos_vectoriales],
                'tiene_vector_search': tiene_vector_search,
                'tiene_semantic': tiene_semantic,
                'esquema_completo': esquema
            }
        except Exception as e:
            return {'error': str(e)}

def main():
    """Función principal"""
    print("🔄 Iniciando vectorización del índice Azure Cognitive Search...")
    
    try:
        # Crear instancia del vectorizador
        vectorizador = VectorizadorIndiceAzure()
        
        print(f"📋 Obteniendo esquema actual del índice '{vectorizador.index_name}'...")
        esquema_actual = vectorizador.obtener_esquema_actual()
        
        print(f"✅ Esquema actual obtenido. Campos actuales: {len(esquema_actual['fields'])}")
        
        print("🔧 Creando nuevo esquema con campos vectoriales...")
        nuevo_esquema = vectorizador.crear_esquema_vectorizado(esquema_actual)
        
        print(f"✅ Nuevo esquema creado. Campos totales: {len(nuevo_esquema['fields'])}")
        
        # Mostrar campos vectoriales que se van a agregar
        campos_vectoriales = [f for f in nuevo_esquema['fields'] if 'vector' in f['name']]
        print(f"🎯 Campos vectoriales a agregar: {len(campos_vectoriales)}")
        for campo in campos_vectoriales:
            print(f"   - {campo['name']} (dimensiones: {campo['vectorSearchDimensions']})")
        
        # Confirmar antes de actualizar
        respuesta = input("\n¿Proceder con la actualización del índice? (s/N): ")
        if respuesta.lower() != 's':
            print("❌ Operación cancelada por el usuario")
            return
        
        print("🔄 Actualizando índice...")
        exito = vectorizador.actualizar_indice(nuevo_esquema)
        
        if exito:
            print("⏳ Verificando actualización...")
            resultado = vectorizador.verificar_actualizacion()
            
            if 'error' in resultado:
                print(f"❌ Error verificando: {resultado['error']}")
            else:
                print(f"✅ Verificación exitosa:")
                print(f"   - Campos vectoriales: {resultado['campos_vectoriales']}")
                print(f"   - Nombres: {resultado['nombres_campos_vectoriales']}")
                print(f"   - Vector Search: {resultado['tiene_vector_search']}")
                print(f"   - Semantic Search: {resultado['tiene_semantic']}")
                
                print("\n🎉 Índice vectorizado exitosamente!")
                print("\n📋 Próximos pasos:")
                print("1. Generar embeddings para los chunks existentes")
                print("2. Actualizar los documentos con los vectores")
                print("3. Probar búsqueda híbrida (texto + vectorial)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
