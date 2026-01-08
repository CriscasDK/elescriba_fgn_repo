#!/usr/bin/env python3
"""
Extrae relaciones semánticas del campo 'analisis' de los documentos
y las almacena en una tabla relaciones_extraidas.

El campo 'analisis' contiene texto estructurado con relaciones como:
- "Patricia Caicedo Siachoque" → hermana → "Pablo Caicedo Siachoque"
- "Edgar Caicedo" → miembro → "Partido Comunista"
"""

import sys
import re
from pathlib import Path
from typing import List, Dict, Tuple

# Agregar path del proyecto
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.consultas import get_db_connection


class RelationExtractor:
    """Extrae relaciones semánticas del campo analisis"""

    def __init__(self):
        self.conn = get_db_connection()
        self.stats = {
            'documentos_procesados': 0,
            'relaciones_extraidas': 0,
            'relaciones_insertadas': 0,
            'errores': 0
        }

    def create_table(self):
        """Crea tabla relaciones_extraidas si no existe"""
        print("\n" + "="*60)
        print("📋 CREANDO TABLA relaciones_extraidas")
        print("="*60)

        cur = self.conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS relaciones_extraidas (
                id SERIAL PRIMARY KEY,
                entidad_origen VARCHAR(500),
                entidad_destino VARCHAR(500),
                tipo_relacion VARCHAR(200),
                documento_id INTEGER REFERENCES documentos(id),
                contexto TEXT,
                confianza FLOAT DEFAULT 1.0,
                metodo_extraccion VARCHAR(100) DEFAULT 'regex_from_analisis',
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)

        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_rel_ext_origen
            ON relaciones_extraidas(entidad_origen);
        """)

        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_rel_ext_destino
            ON relaciones_extraidas(entidad_destino);
        """)

        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_rel_ext_tipo
            ON relaciones_extraidas(tipo_relacion);
        """)

        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_rel_ext_doc
            ON relaciones_extraidas(documento_id);
        """)

        self.conn.commit()
        cur.close()

        print("✅ Tabla creada exitosamente")

    def extract_relations_from_text(self, analisis_text: str, doc_id: int) -> List[Dict]:
        """
        Extrae relaciones del texto de análisis usando patrones.

        Busca patrones como:
        - "X es hijo de Y"
        - "X, hermana de Y"
        - "X, miembro de Y"
        - "X fue victima de Y"
        - "X, esposa de Y"
        """
        relations = []

        if not analisis_text:
            return relations

        # Patrones para detectar relaciones
        patterns = [
            # "X es/fue [relación] de Y"
            (r'([A-ZÁÉÍÓÚÑ][a-záéíóúñA-ZÁÉÍÓÚÑ\s]{2,60}?)\s+(?:es|fue|era|siendo)\s+(hijo|hija|hermana|hermano|esposa|esposo|padre|madre|miembro activo|miembro|víctima|victimario|profesor)\s+de\s+(?:la|el|los|las)?\s*([A-ZÁÉÍÓÚÑ][a-záéíóúñA-ZÁÉÍÓÚÑ\s]{2,60})',
             lambda m: (m.group(1).strip(), m.group(3).strip(), m.group(2))),

            # "X, [relación] de Y"
            (r'([A-ZÁÉÍÓÚÑ][a-záéíóúñA-ZÁÉÍÓÚÑ\s]{2,60}?),\s+(hijo|hija|hermana|hermano|esposa|esposo|padre|madre|miembro activo|miembro)\s+de\s+(?:la|el|los|las)?\s*([A-ZÁÉÍÓÚÑ][a-záéíóúñA-ZÁÉÍÓÚÑ\s]{2,60})',
             lambda m: (m.group(1).strip(), m.group(3).strip(), m.group(2))),

            # "X junto con Y" o "junto con X"
            (r'([A-ZÁÉÍÓÚÑ][a-záéíóúñA-ZÁÉÍÓÚÑ\s]{3,50}?)\s+junto (?:con|a)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñA-ZÁÉÍÓÚÑ\s]{3,50})',
             lambda m: (m.group(1).strip(), m.group(2).strip(), 'junto_con')),

            # "desaparecido junto con X"
            (r'desapareci(?:ó|do|endo)\s+junto (?:con|a)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñA-ZÁÉÍÓÚÑ\s]{3,50})',
             lambda m: ('', m.group(1).strip(), 'desaparecido_con')),

            # "miembro del/de la [organización]"
            (r'([A-ZÁÉÍÓÚÑ][a-záéíóúñA-ZÁÉÍÓÚÑ\s]{2,60}?)(?:,\s+|\s+)miembro\s+(?:del|de la|de|activo de la?)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñA-ZÁÉÍÓÚÑ\s]{3,60})',
             lambda m: (m.group(1).strip(), m.group(2).strip(), 'miembro_de')),

            # "participó en/con"
            (r'([A-ZÁÉÍÓÚÑ][a-záéíóúñA-ZÁÉÍÓÚÑ\s]{3,50}?)\s+particip(?:ó|aba|ando)\s+(?:en|con)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñA-ZÁÉÍÓÚÑ\s]{3,50})',
             lambda m: (m.group(1).strip(), m.group(2).strip(), 'participo_en')),

            # "vinculado a/al"
            (r'([A-ZÁÉÍÓÚÑ][a-záéíóúñA-ZÁÉÍÓÚÑ\s]{3,50}?)\s+vincul(?:ó|ado|ada)\s+(?:a|al|a la)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñA-ZÁÉÍÓÚÑ\s]{3,50})',
             lambda m: (m.group(1).strip(), m.group(2).strip(), 'vinculado_a')),
        ]

        for pattern, extractor in patterns:
            for match in re.finditer(pattern, analisis_text, re.IGNORECASE):
                try:
                    origen, destino, tipo = extractor(match)

                    # Limpiar nombres
                    origen = self._clean_entity_name(origen)
                    destino = self._clean_entity_name(destino)

                    # Validar longitud
                    if origen and (len(origen) < 3 or len(origen) > 100):
                        continue
                    if len(destino) < 3 or len(destino) > 100:
                        continue

                    # Skip si destino parece ser un tipo y no un nombre
                    skip_words = ['colegios', 'universidades', 'universidad', 'colegio', 'evento',
                                  'acto político', 'congreso', 'ciudad', 'trabajo político']
                    if any(skip in destino.lower() for skip in skip_words):
                        continue

                    # Contexto (70 chars antes y después)
                    start = max(0, match.start() - 70)
                    end = min(len(analisis_text), match.end() + 70)
                    contexto = analisis_text[start:end].strip()

                    relations.append({
                        'origen': origen if origen else None,
                        'destino': destino,
                        'tipo': tipo,
                        'contexto': contexto,
                        'doc_id': doc_id
                    })

                except Exception as e:
                    # Silenciar errores en dry-run
                    continue

        return relations

    def _clean_entity_name(self, name: str) -> str:
        """Limpia nombre de entidad"""
        # Remover caracteres al inicio/final
        name = name.strip('.,;:()[]{}\"\'*- ')

        # Remover prefijos comunes
        prefixes = ['señor', 'señora', 'sr', 'sra', 'doctor', 'dr', 'general', 'coronel']
        for prefix in prefixes:
            if name.lower().startswith(prefix + ' '):
                name = name[len(prefix):].strip()

        return name.strip()

    def process_documents(self, limit: int = None, dry_run: bool = False):
        """
        Procesa documentos y extrae relaciones del campo analisis.

        Args:
            limit: Límite de documentos a procesar
            dry_run: Si True, solo simula sin escribir
        """
        print("\n" + "="*60)
        print("🔍 EXTRAYENDO RELACIONES DESDE CAMPO 'analisis'")
        if dry_run:
            print("   [MODO DRY-RUN - NO SE ESCRIBIRÁ EN BD]")
        print("="*60)

        cur = self.conn.cursor()

        # Obtener documentos con campo analisis
        query = """
            SELECT id, archivo, analisis
            FROM documentos
            WHERE analisis IS NOT NULL AND LENGTH(analisis) > 100
            ORDER BY id
        """

        if limit:
            query += f" LIMIT {limit}"

        cur.execute(query)
        documentos = cur.fetchall()

        print(f"\n📄 Documentos a procesar: {len(documentos)}")

        if len(documentos) == 0:
            print("⚠️  No hay documentos con campo 'analisis' para procesar")
            cur.close()
            return

        # Procesar cada documento
        for i, (doc_id, archivo, analisis) in enumerate(documentos, 1):
            if i % 10 == 0:
                print(f"   Procesados {i}/{len(documentos)} documentos...")

            try:
                # Extraer relaciones del análisis
                relations = self.extract_relations_from_text(analisis, doc_id)

                if dry_run and relations:
                    print(f"\n   📄 {archivo}:")
                    for rel in relations[:3]:  # Mostrar solo 3 primeras
                        print(f"      {rel['origen']} --[{rel['tipo']}]--> {rel['destino']}")

                # Insertar relaciones en BD
                if not dry_run:
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
                            1.0,
                            'regex_from_analisis'
                        ))
                        self.stats['relaciones_insertadas'] += 1

                    if relations:
                        self.conn.commit()

                self.stats['documentos_procesados'] += 1
                self.stats['relaciones_extraidas'] += len(relations)

            except Exception as e:
                print(f"   ❌ Error procesando documento {archivo}: {e}")
                self.stats['errores'] += 1
                if not dry_run:
                    self.conn.rollback()

        cur.close()

        print("\n✅ Extracción completada")
        self._print_stats()

    def _print_stats(self):
        """Imprime estadísticas"""
        print(f"\n📊 ESTADÍSTICAS")
        print("="*60)
        print(f"  Documentos procesados:    {self.stats['documentos_procesados']}")
        print(f"  Relaciones extraídas:     {self.stats['relaciones_extraidas']}")
        print(f"  Relaciones insertadas:    {self.stats['relaciones_insertadas']}")
        print(f"  Errores:                  {self.stats['errores']}")
        print("="*60)

    def show_sample_relations(self, limit: int = 20):
        """Muestra muestra de relaciones extraídas"""
        print("\n" + "="*60)
        print("🔍 MUESTRA DE RELACIONES EXTRAÍDAS")
        print("="*60)

        cur = self.conn.cursor()

        cur.execute(f"""
            SELECT
                entidad_origen,
                tipo_relacion,
                entidad_destino,
                COUNT(*) as frecuencia
            FROM relaciones_extraidas
            GROUP BY entidad_origen, tipo_relacion, entidad_destino
            ORDER BY frecuencia DESC
            LIMIT {limit}
        """)

        for i, (origen, tipo, destino, freq) in enumerate(cur.fetchall(), 1):
            print(f"  {i:2}. {origen:30} --[{tipo:15}]--> {destino:30} ({freq}x)")

        cur.close()

    def close(self):
        """Cierra conexión"""
        if self.conn:
            self.conn.close()


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Extraer relaciones semánticas del campo 'analisis'"
    )
    parser.add_argument(
        "--create-table",
        action="store_true",
        help="Crear tabla relaciones_extraidas"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Límite de documentos a procesar"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simular sin escribir en BD"
    )
    parser.add_argument(
        "--show-sample",
        action="store_true",
        help="Mostrar muestra de relaciones extraídas"
    )

    args = parser.parse_args()

    try:
        extractor = RelationExtractor()

        if args.create_table:
            extractor.create_table()

        if not args.show_sample:
            extractor.process_documents(limit=args.limit, dry_run=args.dry_run)

        if args.show_sample:
            extractor.show_sample_relations()

        extractor.close()
        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
