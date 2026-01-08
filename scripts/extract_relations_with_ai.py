#!/usr/bin/env python3
"""
Extrae relaciones semánticas usando Azure OpenAI GPT-4
en lugar de regex, para mayor precisión.

Lee el campo 'analisis' y usa IA para identificar relaciones reales.
"""

import sys
import json
from pathlib import Path
from typing import List, Dict
import os
from dotenv import load_dotenv

# Agregar path del proyecto
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.consultas import get_db_connection

# Cargar variables de entorno
load_dotenv()

# Azure OpenAI
from openai import AzureOpenAI

class AIRelationExtractor:
    """Extrae relaciones usando Azure OpenAI GPT-4"""

    def __init__(self):
        self.conn = get_db_connection()

        # Cliente Azure OpenAI
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version="2024-02-15-preview",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )

        self.deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4")

        self.stats = {
            'documentos_procesados': 0,
            'relaciones_extraidas': 0,
            'relaciones_insertadas': 0,
            'llamadas_api': 0,
            'errores': 0
        }

    def extract_relations_with_ai(self, analisis_text: str, doc_id: int) -> List[Dict]:
        """
        Extrae relaciones usando GPT-4 con prompt estructurado
        """

        if not analisis_text or len(analisis_text) < 100:
            return []

        # Truncar si es muy largo (max 4000 chars para dejar espacio a respuesta)
        if len(analisis_text) > 4000:
            analisis_text = analisis_text[:4000] + "..."

        prompt = f"""Eres un experto en análisis de documentos jurídicos colombianos sobre violencia política.

Del siguiente resumen de un documento, extrae SOLO las relaciones semánticas VERDADERAS y DIRECTAS entre personas, organizaciones y grupos.

**REGLAS CRÍTICAS:**

1. **Relaciones familiares**: hijo, hija, esposo, esposa, hermano, hermana, padre, madre, pareja
   - Ejemplo: "Omar, hijo de María" → {{"origen": "Omar", "destino": "María", "tipo": "hijo"}}

2. **Membresía organizacional**: miembro_de, militante_de, simpatizante_de
   - Solo si la persona ERA miembro activo
   - Ejemplo: "Omar, militante de la Unión Patriótica" → {{"origen": "Omar", "destino": "Unión Patriótica", "tipo": "militante_de"}}

3. **Relaciones victima-victimario**: victima_de, victimario
   - **MUY IMPORTANTE**:
     - SÍ extraer: "víctima de [grupo armado/paramilitares/guerrilla/persona]"
     - NO extraer: "víctima de desaparición forzada" (es un hecho, no una relación)
     - NO extraer: "caso investigado por Fiscalía" (la Fiscalía investiga, no es victimario)
     - SÍ extraer SOLO SI: hay evidencia clara de que la institución/persona fue el victimario directo

4. **Confianza**:
   - 1.0: Relación explícita y clara
   - 0.7-0.9: Relación probable pero no explícita
   - 0.5-0.6: Relación inferida
   - < 0.5: No incluir

**TEXTO A ANALIZAR:**
{analisis_text}

Retorna SOLO un objeto JSON válido (sin markdown, sin explicaciones):
{{
  "relaciones": [
    {{
      "origen": "Nombre completo persona",
      "destino": "Nombre completo persona/organización",
      "tipo": "hijo|esposo|miembro_de|victima_de|victimario|etc",
      "confianza": 0.5-1.0,
      "razon": "Frase del texto que soporta esta relación"
    }}
  ]
}}

Si no hay relaciones claras, retorna: {{"relaciones": []}}
"""

        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": "Eres un experto en análisis de relaciones en documentos jurídicos. Retornas solo JSON válido."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Baja temperatura para consistencia
                max_tokens=1500,
                response_format={"type": "json_object"}  # Forzar JSON
            )

            self.stats['llamadas_api'] += 1

            # Parsear respuesta
            content = response.choices[0].message.content
            data = json.loads(content)

            relaciones = data.get('relaciones', [])

            # Validar y limpiar
            relaciones_validadas = []
            for rel in relaciones:
                # Validar campos requeridos
                if not all(k in rel for k in ['origen', 'destino', 'tipo', 'confianza']):
                    continue

                # Validar confianza mínima
                if rel['confianza'] < 0.5:
                    continue

                # Limpiar nombres
                origen = self._clean_name(rel['origen'])
                destino = self._clean_name(rel['destino'])

                if not origen or not destino:
                    continue

                if len(origen) < 3 or len(destino) < 3:
                    continue

                relaciones_validadas.append({
                    'origen': origen,
                    'destino': destino,
                    'tipo': rel['tipo'].lower().replace(' ', '_'),
                    'confianza': float(rel['confianza']),
                    'razon': rel.get('razon', '')[:500],  # Max 500 chars
                    'doc_id': doc_id
                })

            return relaciones_validadas

        except json.JSONDecodeError as e:
            print(f"   ⚠️  Error parseando JSON de GPT: {e}")
            return []
        except Exception as e:
            print(f"   ❌ Error llamando a GPT: {e}")
            self.stats['errores'] += 1
            return []

    def _clean_name(self, name: str) -> str:
        """Limpia nombre de entidad"""
        if not name:
            return ""

        name = name.strip()

        # Remover comillas, paréntesis extras
        name = name.strip('",\'()[]{}')

        # Capitalizar correctamente
        # (solo si está todo en mayúsculas o minúsculas)
        if name.isupper() or name.islower():
            name = name.title()

        return name.strip()

    def process_documents(self, limit: int = None, dry_run: bool = False):
        """
        Procesa documentos y extrae relaciones con IA

        Args:
            limit: Límite de documentos a procesar
            dry_run: Si True, solo simula sin escribir
        """
        print("\n" + "="*70)
        print("🤖 EXTRAYENDO RELACIONES CON AZURE OPENAI GPT-4")
        if dry_run:
            print("   [MODO DRY-RUN - NO SE ESCRIBIRÁ EN BD]")
        print("="*70)

        cur = self.conn.cursor()

        # Obtener documentos con análisis
        # Priorizar documentos que NO tienen relaciones extraídas por IA
        query = """
            SELECT d.id, d.archivo, d.analisis
            FROM documentos d
            WHERE d.analisis IS NOT NULL
              AND LENGTH(d.analisis) > 100
              AND NOT EXISTS (
                  SELECT 1 FROM relaciones_extraidas re
                  WHERE re.documento_id = d.id
                    AND re.metodo_extraccion = 'gpt4_from_analisis'
              )
            ORDER BY d.id
        """

        if limit:
            query += f" LIMIT {limit}"

        cur.execute(query)
        documentos = cur.fetchall()

        print(f"\n📄 Documentos a procesar: {len(documentos)}")

        if len(documentos) == 0:
            print("✅ No hay documentos pendientes (todos ya procesados con IA)")
            cur.close()
            return

        # Procesar cada documento
        for i, (doc_id, archivo, analisis) in enumerate(documentos, 1):
            print(f"\n[{i}/{len(documentos)}] Procesando: {archivo[:50]}...")

            try:
                # Extraer relaciones con IA
                relations = self.extract_relations_with_ai(analisis, doc_id)

                if relations:
                    print(f"   ✅ {len(relations)} relaciones encontradas:")
                    for rel in relations[:3]:  # Mostrar max 3
                        print(f"      {rel['origen']} --[{rel['tipo']}]--> {rel['destino']} (confianza: {rel['confianza']:.2f})")
                    if len(relations) > 3:
                        print(f"      ... y {len(relations)-3} más")
                else:
                    print(f"   ℹ️  Sin relaciones extraídas")

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
                            rel['razon'],  # Razón como contexto
                            rel['confianza'],
                            'gpt4_from_analisis'
                        ))
                        self.stats['relaciones_insertadas'] += 1

                    self.conn.commit()

                self.stats['documentos_procesados'] += 1
                self.stats['relaciones_extraidas'] += len(relations)

            except Exception as e:
                print(f"   ❌ Error procesando documento: {e}")
                self.stats['errores'] += 1
                if not dry_run:
                    self.conn.rollback()

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
        print(f"  Llamadas API GPT-4:       {self.stats['llamadas_api']}")
        print(f"  Errores:                  {self.stats['errores']}")
        print("="*70)

    def compare_methods(self, sample_size: int = 5):
        """Compara relaciones extraídas por regex vs IA"""
        print("\n" + "="*70)
        print("🔍 COMPARACIÓN: Regex vs IA")
        print("="*70)

        cur = self.conn.cursor()

        # Documentos con ambos métodos
        cur.execute(f"""
            SELECT DISTINCT documento_id
            FROM relaciones_extraidas
            WHERE metodo_extraccion IN ('regex_from_analisis', 'gpt4_from_analisis')
            LIMIT {sample_size}
        """)

        doc_ids = [row[0] for row in cur.fetchall()]

        for doc_id in doc_ids:
            cur.execute("SELECT archivo FROM documentos WHERE id = %s", (doc_id,))
            archivo = cur.fetchone()[0]

            print(f"\n📄 Documento: {archivo}")

            # Regex
            cur.execute("""
                SELECT entidad_origen, tipo_relacion, entidad_destino
                FROM relaciones_extraidas
                WHERE documento_id = %s AND metodo_extraccion = 'regex_from_analisis'
                LIMIT 5
            """, (doc_id,))

            print("  📝 Regex:")
            for origen, tipo, destino in cur.fetchall():
                print(f"     {origen} --[{tipo}]--> {destino}")

            # IA
            cur.execute("""
                SELECT entidad_origen, tipo_relacion, entidad_destino, confianza
                FROM relaciones_extraidas
                WHERE documento_id = %s AND metodo_extraccion = 'gpt4_from_analisis'
                LIMIT 5
            """, (doc_id,))

            print("  🤖 IA (GPT-4):")
            for origen, tipo, destino, conf in cur.fetchall():
                print(f"     {origen} --[{tipo}]--> {destino} (confianza: {conf:.2f})")

        cur.close()

    def close(self):
        """Cierra conexión"""
        if self.conn:
            self.conn.close()


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Extraer relaciones con Azure OpenAI GPT-4"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Límite de documentos a procesar (default: 10 para pruebas)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simular sin escribir en BD"
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Comparar métodos regex vs IA"
    )

    args = parser.parse_args()

    try:
        extractor = AIRelationExtractor()

        if args.compare:
            extractor.compare_methods()
        else:
            extractor.process_documents(limit=args.limit, dry_run=args.dry_run)

        extractor.close()
        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
