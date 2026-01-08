#!/usr/bin/env python3
"""
Extrae relaciones semánticas del campo 'analisis' usando Azure OpenAI GPT-4.1.

Procesa cada documento y usa GPT-4.1 para extraer relaciones estructuradas
del análisis en formato JSON.
"""

import sys
import json
from pathlib import Path
from typing import List, Dict
import time
import os
from dotenv import load_dotenv

# Agregar path del proyecto
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.consultas import get_db_connection

# Cargar variables de entorno desde .env.gpt41
env_path = Path(__file__).parent.parent / '.env.gpt41'
load_dotenv(env_path)

# Importar Azure OpenAI
try:
    from openai import AzureOpenAI
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False
    print("⚠️  Azure OpenAI no disponible. Instalar con: pip install openai")


EXTRACTION_PROMPT = """Analiza el siguiente texto de análisis de un documento judicial y extrae TODAS las relaciones entre personas y organizaciones mencionadas.

Formato de respuesta (JSON):
{{
  "relaciones": [
    {{
      "origen": "Nombre Persona/Organización",
      "destino": "Nombre Persona/Organización",
      "tipo": "tipo_relacion",
      "contexto": "breve contexto donde se menciona"
    }}
  ]
}}

Tipos de relación válidos:
- familiar: hijo, hija, hermano, hermana, padre, madre, esposo, esposa, primo, tío, sobrino
- organizacional: miembro_de, fundador_de, director_de, representante_de
- activismo: militante_de, activista_de, líder_de
- colaboración: junto_con, acompañado_de, colaborador_de
- victimización: victima_de, desaparecido_con, asesinado_con
- legal: acusado_de, investigado_por, defendido_por

Reglas:
1. Solo extraer relaciones entre NOMBRES PROPIOS de personas u organizaciones específicas
2. NO extraer relaciones genéricas como "miembro de un partido" (debe ser nombre específico del partido)
3. Si el análisis dice "X, hermana de Y", extraer: origen=X, destino=Y, tipo=hermana
4. Incluir contexto corto (máximo 100 caracteres)
5. Si no hay relaciones claras, retornar array vacío

ANÁLISIS A PROCESAR:
---
{analisis_text}
---

Responde SOLO con el JSON, sin explicaciones adicionales."""


class AzureLLMRelationExtractor:
    """Extrae relaciones usando Azure OpenAI GPT-4.1"""

    def __init__(self):
        self.conn = get_db_connection()

        if not AZURE_AVAILABLE:
            raise Exception("Azure OpenAI library not installed")

        # Configurar Azure OpenAI
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )

        self.deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1")

        print(f"✅ Azure OpenAI configurado:")
        print(f"   Endpoint: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
        print(f"   Deployment: {self.deployment}")

        self.stats = {
            'documentos_procesados': 0,
            'relaciones_extraidas': 0,
            'relaciones_insertadas': 0,
            'errores': 0,
            'tokens_usados': 0
        }

    def extract_relations_with_llm(self, analisis_text: str, doc_id: int, archivo: str) -> List[Dict]:
        """
        Extrae relaciones usando Azure OpenAI GPT-4.1.
        """
        if not analisis_text or len(analisis_text) < 100:
            return []

        try:
            # Truncar análisis si es muy largo (max 6000 chars ≈ 1500 tokens)
            analisis_truncado = analisis_text[:6000]

            # Llamar a Azure OpenAI
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": "Eres un experto en extracción de relaciones de textos judiciales. Respondes SOLO en formato JSON válido."},
                    {"role": "user", "content": EXTRACTION_PROMPT.format(analisis_text=analisis_truncado)}
                ],
                temperature=0.1,
                max_tokens=1000
            )

            # Parsear respuesta (limpiar posibles markdown)
            result_text = response.choices[0].message.content

            if not result_text:
                print(f"  ⚠️  Respuesta vacía de GPT para {archivo}")
                return []

            result_text = result_text.strip()

            # Remover posibles marcadores de código markdown
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]

            result_text = result_text.strip()

            result_json = json.loads(result_text)

            # Validar que sea un dict
            if not isinstance(result_json, dict):
                print(f"  ⚠️  Respuesta no es dict para {archivo}: {type(result_json)}")
                return []

            # Actualizar estadísticas
            if hasattr(response, 'usage'):
                self.stats['tokens_usados'] += response.usage.total_tokens

            # Procesar relaciones extraídas
            relaciones = []
            for rel in result_json.get('relaciones', []):
                if not rel.get('origen') or not rel.get('destino'):
                    continue

                relaciones.append({
                    'origen': rel['origen'].strip()[:500],
                    'destino': rel['destino'].strip()[:500],
                    'tipo': rel['tipo'].strip()[:200],
                    'contexto': rel.get('contexto', '')[:500],
                    'doc_id': doc_id,
                    'archivo': archivo
                })

            return relaciones

        except json.JSONDecodeError as e:
            print(f"  ⚠️  Error parsing JSON para {archivo}: {e}")
            print(f"      Respuesta recibida: {result_text[:200]}...")
            self.stats['errores'] += 1
            return []
        except Exception as e:
            print(f"  ⚠️  Error LLM para {archivo}: {e}")
            if 'result_text' in locals():
                print(f"      Respuesta recibida: {result_text[:200]}...")
            self.stats['errores'] += 1
            return []

    def process_documents(self, limit: int = None, offset: int = 0, dry_run: bool = False, batch_size: int = 10, auto_confirm: bool = False):
        """
        Procesa documentos y extrae relaciones con LLM.

        Args:
            limit: Límite de documentos a procesar
            offset: Offset para continuar desde un punto
            dry_run: Si True, solo simula sin escribir
            batch_size: Documentos a procesar antes de commit
            auto_confirm: Si True, no pide confirmación
        """
        print("\n" + "="*70)
        print("🤖 EXTRAYENDO RELACIONES CON AZURE OPENAI GPT-4.1")
        if dry_run:
            print("   [MODO DRY-RUN - NO SE ESCRIBIRÁ EN BD]")
        print("="*70)

        cur = self.conn.cursor()

        # Obtener documentos con analisis
        query = """
            SELECT id, archivo, analisis
            FROM documentos
            WHERE analisis IS NOT NULL AND LENGTH(analisis) > 100
            ORDER BY id
        """

        if limit:
            query += f" LIMIT {limit} OFFSET {offset}"

        cur.execute(query)
        documentos = cur.fetchall()

        print(f"\n📄 Documentos a procesar: {len(documentos)} (offset: {offset})")

        if len(documentos) == 0:
            print("⚠️  No hay documentos para procesar")
            cur.close()
            return

        if not dry_run and not auto_confirm:
            confirm = input(f"\n¿Continuar con el procesamiento? (s/n): ")
            if confirm.lower() != 's':
                print("❌ Cancelado")
                return

        # Procesar en batches
        for i, (doc_id, archivo, analisis) in enumerate(documentos, 1):
            if i % 10 == 0:
                print(f"   Procesados {i}/{len(documentos)} documentos... "
                      f"({self.stats['tokens_usados']:,} tokens)")

            try:
                # Extraer relaciones con LLM
                relations = self.extract_relations_with_llm(analisis, doc_id, archivo)

                if dry_run and relations:
                    print(f"\n   📄 {archivo} ({len(relations)} relaciones):")
                    for rel in relations[:3]:  # Mostrar solo 3
                        print(f"      {rel['origen'][:30]} --[{rel['tipo']}]--> {rel['destino'][:30]}")

                # Insertar en BD
                if not dry_run and relations:
                    for rel in relations:
                        cur.execute("""
                            INSERT INTO relaciones_extraidas
                            (entidad_origen, entidad_destino, tipo_relacion,
                             documento_id, contexto, confianza, metodo_extraccion)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, (
                            rel['origen'],
                            rel['destino'],
                            rel['tipo'],
                            rel['doc_id'],
                            rel['contexto'],
                            0.9,  # Alta confianza en LLM
                            'azure_gpt41_extraction'
                        ))
                        self.stats['relaciones_insertadas'] += 1

                    # Commit cada batch_size documentos
                    if i % batch_size == 0:
                        self.conn.commit()

                self.stats['documentos_procesados'] += 1
                self.stats['relaciones_extraidas'] += len(relations)

                # Rate limiting ligero
                if i % 50 == 0:
                    time.sleep(0.5)

            except Exception as e:
                print(f"   ❌ Error procesando {archivo}: {e}")
                self.stats['errores'] += 1
                if not dry_run:
                    self.conn.rollback()

        # Commit final
        if not dry_run:
            self.conn.commit()

        cur.close()

        print("\n✅ Extracción completada")
        self._print_stats()

    def _print_stats(self):
        """Imprime estadísticas"""
        print(f"\n📊 ESTADÍSTICAS")
        print("="*70)
        print(f"  Documentos procesados:    {self.stats['documentos_procesados']}")
        print(f"  Relaciones extraídas:     {self.stats['relaciones_extraidas']}")
        print(f"  Relaciones insertadas:    {self.stats['relaciones_insertadas']}")
        print(f"  Errores:                  {self.stats['errores']}")
        print(f"  Tokens usados:            {self.stats['tokens_usados']:,}")
        print("="*70)

    def close(self):
        """Cierra conexión"""
        if self.conn:
            self.conn.close()


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Extraer relaciones con Azure OpenAI GPT-4.1"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Límite de documentos a procesar"
    )
    parser.add_argument(
        "--offset",
        type=int,
        default=0,
        help="Offset para continuar desde un punto"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simular sin escribir en BD"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Documentos a procesar antes de commit"
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Confirmar procesamiento automáticamente (sin prompt)"
    )

    args = parser.parse_args()

    if not AZURE_AVAILABLE:
        print("❌ Error: Azure OpenAI library not installed")
        print("   Install with: pip install openai")
        return 1

    try:
        extractor = AzureLLMRelationExtractor()
        extractor.process_documents(
            limit=args.limit,
            offset=args.offset,
            dry_run=args.dry_run,
            batch_size=args.batch_size,
            auto_confirm=args.yes
        )
        extractor.close()
        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
