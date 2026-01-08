#!/usr/bin/env python3
"""
Extracción BATCH de relaciones semánticas con Azure OpenAI GPT-4
Versión robusta para procesamiento masivo (miles de documentos)

Características:
- Logging detallado a archivo
- Checkpoint/resume automático
- Rate limiting
- Reintentos con backoff exponencial
- Estimación de progreso y costo
- Manejo robusto de errores
"""

import sys
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Agregar path del proyecto
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.consultas import get_db_connection

# Cargar variables de entorno
load_dotenv()

# Azure OpenAI
from openai import AzureOpenAI
import openai

# Configurar logging
log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = log_dir / f"ai_extraction_{timestamp}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class BatchAIRelationExtractor:
    """Extractor batch con características de producción"""

    def __init__(self, batch_size: int = 100, rate_limit_delay: float = 0.5):
        self.conn = get_db_connection()
        self.batch_size = batch_size
        self.rate_limit_delay = rate_limit_delay  # segundos entre llamadas API

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
            'llamadas_exitosas': 0,
            'llamadas_fallidas': 0,
            'tokens_usados': 0,
            'errores': 0,
            'inicio': datetime.now()
        }

        self.checkpoint_file = log_dir / "extraction_checkpoint.json"

        logger.info("="*70)
        logger.info("🤖 BATCH AI RELATION EXTRACTOR INICIADO")
        logger.info("="*70)
        logger.info(f"Deployment: {self.deployment}")
        logger.info(f"Batch size: {batch_size}")
        logger.info(f"Rate limit: {rate_limit_delay}s entre llamadas")
        logger.info(f"Log file: {log_file}")
        logger.info(f"Checkpoint: {self.checkpoint_file}")

    def load_checkpoint(self) -> Optional[int]:
        """Carga último documento procesado (para resumir)"""
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, 'r') as f:
                    data = json.load(f)
                    last_id = data.get('last_document_id')
                    logger.info(f"📌 Checkpoint encontrado: último ID procesado = {last_id}")
                    return last_id
            except Exception as e:
                logger.warning(f"⚠️  Error leyendo checkpoint: {e}")
        return None

    def save_checkpoint(self, doc_id: int):
        """Guarda checkpoint cada N documentos"""
        try:
            with open(self.checkpoint_file, 'w') as f:
                json.dump({
                    'last_document_id': doc_id,
                    'timestamp': datetime.now().isoformat(),
                    'stats': self.stats_serializable()
                }, f, indent=2)
        except Exception as e:
            logger.error(f"❌ Error guardando checkpoint: {e}")

    def stats_serializable(self) -> dict:
        """Stats serializables a JSON"""
        stats = self.stats.copy()
        stats['inicio'] = stats['inicio'].isoformat()
        return stats

    def extract_relations_with_ai(self, analisis_text: str, doc_id: int, max_retries: int = 3) -> List[Dict]:
        """
        Extrae relaciones con GPT-4 + reintentos automáticos
        """

        if not analisis_text or len(analisis_text) < 100:
            return []

        # Truncar si es muy largo
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
     - SÍ extraer: "víctima de [grupo armado/paramilitares/guerrilla/persona específica]"
     - NO extraer: "víctima de desaparición forzada" (es un hecho, no una relación)
     - NO extraer: "caso investigado por Fiscalía" (investigación ≠ victimización)
     - SÍ extraer SOLO SI: hay evidencia clara de que la entidad fue el victimario directo
     - En Colombia, agentes del Estado SÍ pueden ser victimarios (falsos positivos, desaparición forzada)

4. **Confianza**:
   - 1.0: Relación explícita y clara
   - 0.7-0.9: Relación probable
   - 0.5-0.6: Relación inferida
   - < 0.5: No incluir

**TEXTO:**
{analisis_text}

Retorna JSON válido (sin markdown):
{{
  "relaciones": [
    {{
      "origen": "Nombre completo",
      "destino": "Nombre completo/organización",
      "tipo": "hijo|esposo|miembro_de|victima_de|victimario|etc",
      "confianza": 0.5-1.0,
      "razon": "Frase del texto que soporta"
    }}
  ]
}}

Si no hay relaciones claras: {{"relaciones": []}}
"""

        # Reintentos con backoff exponencial
        for attempt in range(max_retries):
            try:
                # Rate limiting
                time.sleep(self.rate_limit_delay)

                response = self.client.chat.completions.create(
                    model=self.deployment,
                    messages=[
                        {"role": "system", "content": "Eres un experto en análisis de relaciones en documentos jurídicos. Retornas solo JSON válido."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=1500,
                    response_format={"type": "json_object"}
                )

                self.stats['llamadas_api'] += 1
                self.stats['llamadas_exitosas'] += 1
                self.stats['tokens_usados'] += response.usage.total_tokens

                # Parsear respuesta
                content = response.choices[0].message.content
                data = json.loads(content)

                relaciones = data.get('relaciones', [])

                # Validar y limpiar
                relaciones_validadas = []
                for rel in relaciones:
                    if not all(k in rel for k in ['origen', 'destino', 'tipo', 'confianza']):
                        continue

                    if rel['confianza'] < 0.5:
                        continue

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
                        'razon': rel.get('razon', '')[:500],
                        'doc_id': doc_id
                    })

                return relaciones_validadas

            except openai.RateLimitError as e:
                wait_time = (2 ** attempt) * 5  # 5, 10, 20 segundos
                logger.warning(f"⚠️  Rate limit hit. Esperando {wait_time}s...")
                time.sleep(wait_time)
                self.stats['llamadas_fallidas'] += 1

            except json.JSONDecodeError as e:
                logger.warning(f"⚠️  Error parseando JSON (intento {attempt+1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    self.stats['errores'] += 1
                    return []

            except Exception as e:
                logger.error(f"❌ Error en API (intento {attempt+1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    self.stats['errores'] += 1
                    self.stats['llamadas_fallidas'] += 1
                    return []
                time.sleep(2 ** attempt)

        return []

    def _clean_name(self, name: str) -> str:
        """Limpia nombre de entidad"""
        if not name:
            return ""

        name = name.strip().strip('",\'()[]{}')

        if name.isupper() or name.islower():
            name = name.title()

        return name.strip()

    def get_pending_documents(self, resume_from_id: Optional[int] = None) -> List[tuple]:
        """Obtiene documentos pendientes de procesar"""
        cur = self.conn.cursor()

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
        """

        if resume_from_id:
            query += f" AND d.id > {resume_from_id}"

        query += " ORDER BY d.id"

        cur.execute(query)
        docs = cur.fetchall()
        cur.close()

        return docs

    def process_batch(self, resume: bool = True):
        """
        Procesa todos los documentos pendientes en batches
        """

        # Checkpoint
        last_id = None
        if resume:
            last_id = self.load_checkpoint()

        # Obtener documentos
        documentos = self.get_pending_documents(resume_from_id=last_id)
        total_docs = len(documentos)

        if total_docs == 0:
            logger.info("✅ No hay documentos pendientes")
            return

        # Estimaciones
        tokens_estimados = total_docs * 1766
        costo_estimado = tokens_estimados * 0.03 / 1000
        tiempo_estimado = total_docs * (3 + self.rate_limit_delay)

        logger.info("")
        logger.info("📊 ESTADÍSTICAS INICIALES:")
        logger.info(f"  Documentos pendientes:      {total_docs:,}")
        logger.info(f"  Tokens estimados:           {tokens_estimados:,}")
        logger.info(f"  Costo estimado:             ~${costo_estimado:.2f} USD")
        logger.info(f"  Tiempo estimado:            ~{tiempo_estimado/3600:.1f} horas")
        logger.info("")
        logger.info("🚀 INICIANDO PROCESAMIENTO...")
        logger.info("="*70)

        # Procesar por batches
        for i, (doc_id, archivo, analisis) in enumerate(documentos, 1):
            try:
                # Progress
                if i % 10 == 0:
                    elapsed = (datetime.now() - self.stats['inicio']).total_seconds()
                    docs_per_sec = i / elapsed if elapsed > 0 else 0
                    eta_seconds = (total_docs - i) / docs_per_sec if docs_per_sec > 0 else 0
                    eta = timedelta(seconds=int(eta_seconds))

                    logger.info(f"[{i:,}/{total_docs:,}] Progreso: {i/total_docs*100:.1f}% | ETA: {eta}")

                # Extraer relaciones
                relations = self.extract_relations_with_ai(analisis, doc_id)

                if relations:
                    # Insertar en BD
                    cur = self.conn.cursor()
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
                            rel['razon'],
                            rel['confianza'],
                            'gpt4_from_analisis'
                        ))
                        self.stats['relaciones_insertadas'] += 1

                    self.conn.commit()
                    cur.close()

                    logger.debug(f"  ✅ {archivo[:50]}: {len(relations)} relaciones")

                self.stats['documentos_procesados'] += 1
                self.stats['relaciones_extraidas'] += len(relations)

                # Checkpoint cada 100 docs
                if i % 100 == 0:
                    self.save_checkpoint(doc_id)
                    logger.info(f"📌 Checkpoint guardado (ID: {doc_id})")

            except Exception as e:
                logger.error(f"❌ Error procesando doc {doc_id}: {e}")
                self.stats['errores'] += 1
                self.conn.rollback()

        # Checkpoint final
        self.save_checkpoint(documentos[-1][0] if documentos else 0)

        logger.info("")
        logger.info("="*70)
        logger.info("✅ PROCESAMIENTO COMPLETADO")
        logger.info("="*70)
        self._print_stats()

    def _print_stats(self):
        """Imprime estadísticas finales"""
        elapsed = datetime.now() - self.stats['inicio']
        costo_real = self.stats['tokens_usados'] * 0.03 / 1000

        logger.info("")
        logger.info("📊 ESTADÍSTICAS FINALES:")
        logger.info("="*70)
        logger.info(f"  Documentos procesados:      {self.stats['documentos_procesados']:,}")
        logger.info(f"  Relaciones extraídas:       {self.stats['relaciones_extraidas']:,}")
        logger.info(f"  Relaciones insertadas:      {self.stats['relaciones_insertadas']:,}")
        logger.info(f"  Llamadas API totales:       {self.stats['llamadas_api']:,}")
        logger.info(f"  Llamadas exitosas:          {self.stats['llamadas_exitosas']:,}")
        logger.info(f"  Llamadas fallidas:          {self.stats['llamadas_fallidas']:,}")
        logger.info(f"  Tokens usados:              {self.stats['tokens_usados']:,}")
        logger.info(f"  Costo real:                 ${costo_real:.2f} USD")
        logger.info(f"  Errores:                    {self.stats['errores']:,}")
        logger.info(f"  Tiempo total:               {elapsed}")
        logger.info(f"  Velocidad:                  {self.stats['documentos_procesados']/elapsed.total_seconds():.2f} docs/seg")
        logger.info("="*70)

    def close(self):
        """Cierra conexión"""
        if self.conn:
            self.conn.close()
        logger.info("🔒 Conexión cerrada")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Extracción BATCH con Azure OpenAI GPT-4"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Tamaño de batch para commits (default: 100)"
    )
    parser.add_argument(
        "--rate-limit",
        type=float,
        default=0.5,
        help="Delay entre llamadas API en segundos (default: 0.5)"
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="No resumir desde checkpoint (empezar de cero)"
    )

    args = parser.parse_args()

    try:
        extractor = BatchAIRelationExtractor(
            batch_size=args.batch_size,
            rate_limit_delay=args.rate_limit
        )

        extractor.process_batch(resume=not args.no_resume)
        extractor.close()

        return 0

    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrupción por usuario (Ctrl+C)")
        logger.info("💾 Checkpoint guardado. Puedes resumir más tarde.")
        return 130

    except Exception as e:
        logger.error(f"\n❌ Error fatal: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
