#!/usr/bin/env python3
"""
Script para vectorizar el índice de Azure Cognitive Search
Agrega campos vectoriales y configura búsqueda híbrida
"""

import os
import json
import requests
from typing import Dict, Any
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv('/home/lab4/scripts/documentos_judiciales/.env.gpt41')

class AzureSearchVectorizer:
    def __init__(self):
        self.endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
        self.key = os.getenv('AZURE_SEARCH_KEY')
        self.index_name = os.getenv('AZURE_SEARCH_INDEX_CHUNKS', 'exhaustive-legal-chunks')
        self.api_version = "2023-11-01"
        
        if not all([self.endpoint, self.key]):
            raise ValueError("Faltan credenciales de Azure Search en .env")
    
    def get_headers(self) -> Dict[str, str]:
        """Headers para las requests a Azure Search"""
        return {
            'Content-Type': 'application/json',
            'api-key': self.key
        }
    
    def get_current_index_schema(self) -> Dict[str, Any]:
        """Obtiene el esquema actual del índice"""
        url = f"{self.endpoint}/indexes/{self.index_name}?api-version={self.api_version}"
        
        response = requests.get(url, headers=self.get_headers())
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error obteniendo esquema: {response.status_code} - {response.text}")
    
    def create_vectorized_schema(self, current_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Crea el nuevo esquema con campos vectoriales"""
        
        # Agregar campos vectoriales
        vector_fields = [
            {
                "name": "texto_chunk_vector",
                "type": "Collection(Edm.Single)",
                "searchable": True,
                "filterable": False,
                "retrievable": False,
                "stored": True,
                "sortable": False,
                "facetable": False,
                "key": False,
                "dimensions": 1536,
                "vectorSearchProfile": "vector-profile-1536"
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
                "dimensions": 1536,
                "vectorSearchProfile": "vector-profile-1536"
            }
        ]
        
        # Agregar los campos vectoriales al esquema existente
        current_schema['fields'].extend(vector_fields)
        
        # Configurar búsqueda vectorial
        current_schema['vectorSearch'] = {
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
                    "algorithm": "cosine-algorithm"
                }
            ]
        }
        
        # Configurar búsqueda semántica
        current_schema['semantic'] = {
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
        
        return current_schema
    
    def update_index_schema(self, new_schema: Dict[str, Any]) -> bool:
        """Actualiza el esquema del índice"""
        url = f"{self.endpoint}/indexes/{self.index_name}?api-version={self.api_version}"
        
        response = requests.put(url, headers=self.get_headers(), json=new_schema)
        
        if response.status_code == 200:
            print("✅ Índice actualizado correctamente")
            return True
        else:
            print(f"❌ Error actualizando índice: {response.status_code}")
            print(response.text)
            return False
    
    def backup_current_schema(self, schema: Dict[str, Any]) -> str:
        """Hace backup del esquema actual"""
        backup_file = f"/home/lab4/scripts/documentos_judiciales/scripts/backup_schema_{self.index_name}.json"
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(schema, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Backup guardado en: {backup_file}")
        return backup_file
    
    def vectorize_index(self) -> bool:
        """Proceso principal de vectorización"""
        try:
            print("🔍 Obteniendo esquema actual...")
            current_schema = self.get_current_index_schema()
            
            print("💾 Creando backup del esquema actual...")
            self.backup_current_schema(current_schema)
            
            print("🔧 Creando nuevo esquema vectorizado...")
            new_schema = self.create_vectorized_schema(current_schema)
            
            print("📤 Actualizando índice en Azure...")
            success = self.update_index_schema(new_schema)
            
            if success:
                print("🎉 ¡Índice vectorizado exitosamente!")
                print("\n📋 Nuevos campos agregados:")
                print("  - texto_chunk_vector (1536 dimensiones)")
                print("  - resumen_chunk_vector (1536 dimensiones)")
                print("\n⚙️ Configuraciones agregadas:")
                print("  - Vector Search con algoritmo HNSW + cosine similarity")
                print("  - Semantic Search configurado")
                return True
            else:
                return False
                
        except Exception as e:
            print(f"❌ Error durante vectorización: {e}")
            return False

def main():
    """Función principal"""
    print("🚀 Iniciando vectorización del índice Azure Search...")
    print("=" * 60)
    
    vectorizer = AzureSearchVectorizer()
    success = vectorizer.vectorize_index()
    
    if success:
        print("\n✅ Proceso completado exitosamente!")
        print("\n📝 Próximos pasos:")
        print("1. Generar embeddings para chunks existentes")
        print("2. Poblar campos vectoriales")
        print("3. Actualizar cliente de búsqueda para usar vectores")
    else:
        print("\n❌ Proceso falló. Revisa los logs arriba.")

if __name__ == "__main__":
    main()
