#!/usr/bin/env python3
"""
Script de sincronización PostgreSQL → Apache AGE

Puebla el grafo AGE con datos directamente desde las tablas de PostgreSQL.
Crea nodos Persona desde la tabla 'personas' y relaciones MENCIONADO_EN con documentos.
"""

import sys
import argparse
from pathlib import Path
from typing import Dict, List, Tuple

# Agregar path del proyecto
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.consultas import get_db_connection
from core.graph.age_connector import AGEConnector
from core.graph.config import GraphConfig


class PostgresAGESync:
    """Sincronizador de datos entre PostgreSQL y Apache AGE"""

    def __init__(self, config: GraphConfig = None):
        self.config = config or GraphConfig()
        self.age_connector = AGEConnector(self.config)
        self.pg_conn = get_db_connection()

        # Estadísticas
        self.stats = {
            'personas_procesadas': 0,
            'personas_nuevas': 0,
            'personas_existentes': 0,
            'relaciones_creadas': 0,
            'documentos_vinculados': 0,
            'errores': 0
        }

    def analyze_postgres_data(self) -> Dict:
        """Analiza los datos disponibles en PostgreSQL"""
        print("\n" + "="*60)
        print("📊 ANÁLISIS DE DATOS EN POSTGRESQL")
        print("="*60)

        cur = self.pg_conn.cursor()

        # Tabla personas
        cur.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(DISTINCT nombre) as nombres_unicos,
                COUNT(DISTINCT documento_id) as documentos_relacionados
            FROM personas
            WHERE nombre IS NOT NULL AND LENGTH(TRIM(nombre)) > 0
        """)
        personas_stats = cur.fetchone()

        print(f"\n📋 Tabla 'personas':")
        print(f"   Total registros: {personas_stats[0]}")
        print(f"   Nombres únicos: {personas_stats[1]}")
        print(f"   Documentos relacionados: {personas_stats[2]}")

        # Tabla documentos
        cur.execute("SELECT COUNT(*) FROM documentos")
        docs_total = cur.fetchone()[0]
        print(f"\n📄 Tabla 'documentos':")
        print(f"   Total documentos: {docs_total}")

        # Muestra de nombres
        print(f"\n👥 Muestra de personas (primeros 10):")
        cur.execute("""
            SELECT DISTINCT nombre
            FROM personas
            WHERE nombre IS NOT NULL AND LENGTH(TRIM(nombre)) > 0
            ORDER BY nombre
            LIMIT 10
        """)
        for i, (nombre,) in enumerate(cur.fetchall(), 1):
            print(f"   {i:2}. {nombre}")

        # Buscar Oswaldo Olivo específicamente
        cur.execute("""
            SELECT p.nombre, d.archivo, d.nuc
            FROM personas p
            INNER JOIN documentos d ON p.documento_id = d.id
            WHERE LOWER(p.nombre) LIKE %s
            LIMIT 5
        """, ('%oswaldo%',))
        oswaldo_results = cur.fetchall()

        if oswaldo_results:
            print(f"\n🔍 Búsqueda 'Oswaldo': {len(oswaldo_results)} registros encontrados")
            for nombre, archivo, nuc in oswaldo_results:
                print(f"   - {nombre:40} | {archivo[:45]}")
        else:
            print(f"\n⚠️  No se encontró 'Oswaldo' en la tabla personas")

        cur.close()

        return {
            'total_personas': personas_stats[0],
            'nombres_unicos': personas_stats[1],
            'documentos_relacionados': personas_stats[2],
            'total_documentos': docs_total
        }

    def get_personas_from_postgres(self, limit: int = None) -> List[Tuple]:
        """
        Obtiene lista de personas únicas desde PostgreSQL.
        Filtra nombres inválidos (símbolos, números solos, etc.)

        Returns:
            Lista de tuplas (nombre, lista_documento_ids)
        """
        cur = self.pg_conn.cursor()

        # Filtrar nombres válidos:
        # - Longitud > 2 caracteres
        # - Contiene al menos una letra
        # - No es solo números
        # - No empieza con símbolo
        query = """
            SELECT
                p.nombre,
                ARRAY_AGG(DISTINCT d.archivo) as archivos,
                ARRAY_AGG(DISTINCT d.nuc) as nucs,
                ARRAY_AGG(DISTINCT d.id) as doc_ids,
                COUNT(*) as menciones
            FROM personas p
            INNER JOIN documentos d ON p.documento_id = d.id
            WHERE p.nombre IS NOT NULL
              AND LENGTH(TRIM(p.nombre)) > 2
              AND p.nombre ~ '[A-Za-záéíóúñÁÉÍÓÚÑ]'
              AND NOT (p.nombre ~ '^[0-9]+$')
              AND NOT (p.nombre ~ '^[^A-Za-z]')
            GROUP BY p.nombre
            ORDER BY menciones DESC
        """

        if limit:
            query += f" LIMIT {limit}"

        cur.execute(query)
        results = cur.fetchall()
        cur.close()

        return results

    def sync_relaciones_coocurrencia(self, dry_run: bool = False):
        """
        Crea relaciones CO_OCURRE_CON entre personas que aparecen en el mismo documento.

        Args:
            dry_run: Si True, solo simula sin escribir
        """
        print("\n" + "="*60)
        print(f"🔗 SINCRONIZACIÓN DE RELACIONES CO-OCURRENCIA")
        if dry_run:
            print("   [MODO DRY-RUN - NO SE ESCRIBIRÁ EN AGE]")
        print("="*60)

        cur = self.pg_conn.cursor()

        # Obtener pares de personas que co-ocurren en documentos
        print(f"\n1️⃣  Obteniendo co-ocurrencias desde PostgreSQL...")

        query = """
            SELECT
                p1.nombre as persona1,
                p2.nombre as persona2,
                COUNT(DISTINCT p1.documento_id) as documentos_compartidos
            FROM personas p1
            INNER JOIN personas p2 ON p1.documento_id = p2.documento_id
            WHERE p1.nombre < p2.nombre  -- Evitar duplicados (A-B y B-A)
              AND p1.nombre IS NOT NULL AND LENGTH(TRIM(p1.nombre)) > 2
              AND p2.nombre IS NOT NULL AND LENGTH(TRIM(p2.nombre)) > 2
              AND p1.nombre ~ '[A-Za-záéíóúñÁÉÍÓÚÑ]'
              AND p2.nombre ~ '[A-Za-záéíóúñÁÉÍÓÚÑ]'
            GROUP BY p1.nombre, p2.nombre
            HAVING COUNT(DISTINCT p1.documento_id) >= 1
            ORDER BY documentos_compartidos DESC
        """

        cur.execute(query)
        coocurrencias = cur.fetchall()
        cur.close()

        print(f"   ✅ Obtenidas {len(coocurrencias)} co-ocurrencias")

        if len(coocurrencias) == 0:
            print("   ⚠️  No hay co-ocurrencias para sincronizar")
            return

        # Crear relaciones en AGE
        print(f"\n2️⃣  Creando relaciones en AGE...")

        relaciones_creadas = 0
        errores = 0

        for i, (persona1, persona2, docs_compartidos) in enumerate(coocurrencias, 1):
            if i % 500 == 0:
                print(f"   Procesadas {i}/{len(coocurrencias)} relaciones...")

            try:
                if not dry_run:
                    # Crear relación CO_OCURRE_CON
                    cypher = f"""
                    MATCH (p1:Persona {{nombre: '{self._escape_cypher(persona1)}'}}),
                          (p2:Persona {{nombre: '{self._escape_cypher(persona2)}'}})
                    MERGE (p1)-[r:CO_OCURRE_CON]->(p2)
                    SET r.documentos_compartidos = {docs_compartidos}
                    RETURN r
                    """

                    result = self.age_connector.execute_cypher(
                        cypher,
                        parameters=None,
                        graph_name=self.config.graph_name,
                        column_definitions=["r agtype"]
                    )

                    if result:
                        relaciones_creadas += 1
                else:
                    if i <= 10:  # Mostrar solo las primeras 10 en dry-run
                        print(f"   [DRY-RUN] {persona1} <-> {persona2} ({docs_compartidos} docs)")
                    relaciones_creadas += 1

            except Exception as e:
                if i <= 5:  # Mostrar solo los primeros errores
                    print(f"   ❌ Error: {persona1} <-> {persona2}: {e}")
                errores += 1

        print(f"\n✅ Relaciones sincronizadas")
        print(f"="*60)
        print(f"  Relaciones creadas:   {relaciones_creadas}")
        print(f"  Errores:              {errores}")
        print("="*60)

    def sync_relaciones_llm(self, limit: int = None, dry_run: bool = False):
        """
        Sincroniza relaciones extraídas por LLM desde la tabla relaciones_extraidas.

        Args:
            limit: Límite de relaciones a procesar (None = todas)
            dry_run: Si True, solo simula sin escribir
        """
        print("\n" + "="*60)
        print(f"🤖 SINCRONIZACIÓN DE RELACIONES LLM")
        if dry_run:
            print("   [MODO DRY-RUN - NO SE ESCRIBIRÁ EN AGE]")
        print("="*60)

        cur = self.pg_conn.cursor()

        # Obtener estadísticas de relaciones LLM
        print(f"\n📊 Analizando relaciones LLM...")
        cur.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(DISTINCT tipo_relacion) as tipos_unicos,
                COUNT(DISTINCT entidad_origen) as entidades_origen,
                COUNT(DISTINCT entidad_destino) as entidades_destino
            FROM relaciones_extraidas
            WHERE metodo_extraccion = 'azure_gpt41_extraction'
        """)
        stats = cur.fetchone()

        print(f"   Total relaciones:     {stats[0]:,}")
        print(f"   Tipos únicos:         {stats[1]}")
        print(f"   Entidades origen:     {stats[2]:,}")
        print(f"   Entidades destino:    {stats[3]:,}")

        # Obtener relaciones
        print(f"\n1️⃣  Obteniendo relaciones desde PostgreSQL...")

        query = """
            SELECT
                entidad_origen,
                entidad_destino,
                tipo_relacion,
                contexto,
                confianza
            FROM relaciones_extraidas
            WHERE metodo_extraccion = 'azure_gpt41_extraction'
              AND entidad_origen IS NOT NULL
              AND entidad_destino IS NOT NULL
              AND LENGTH(TRIM(entidad_origen)) > 2
              AND LENGTH(TRIM(entidad_destino)) > 2
            ORDER BY id
        """

        if limit:
            query += f" LIMIT {limit}"

        cur.execute(query)
        relaciones = cur.fetchall()
        cur.close()

        print(f"   ✅ Obtenidas {len(relaciones):,} relaciones")

        if len(relaciones) == 0:
            print("   ⚠️  No hay relaciones LLM para sincronizar")
            return

        # Crear relaciones en AGE
        print(f"\n2️⃣  Creando relaciones en AGE...")

        relaciones_creadas = 0
        errores = 0
        tipos_relacion_counts = {}

        for i, (origen, destino, tipo_rel, contexto, confianza) in enumerate(relaciones, 1):
            if i % 1000 == 0:
                print(f"   Procesadas {i:,}/{len(relaciones):,} relaciones...")

            try:
                # Normalizar tipo de relación para el label de la relación
                # Cypher no permite guiones en labels, reemplazar por underscore
                tipo_label = tipo_rel.upper().replace(' ', '_').replace('-', '_')

                # Trackear tipos de relación
                tipos_relacion_counts[tipo_label] = tipos_relacion_counts.get(tipo_label, 0) + 1

                if not dry_run:
                    # Crear o mergear relación en AGE
                    # Usamos MERGE para evitar duplicados
                    cypher = f"""
                    MATCH (p1:Persona {{nombre: '{self._escape_cypher(origen)}'}}),
                          (p2:Persona {{nombre: '{self._escape_cypher(destino)}'}})
                    MERGE (p1)-[r:{tipo_label}]->(p2)
                    SET r.contexto = '{self._escape_cypher(contexto[:200] if contexto else '')}',
                        r.confianza = {confianza},
                        r.metodo = 'llm',
                        r.tipo_original = '{self._escape_cypher(tipo_rel)}'
                    RETURN r
                    """

                    result = self.age_connector.execute_cypher(
                        cypher,
                        parameters=None,
                        graph_name=self.config.graph_name,
                        column_definitions=["r agtype"]
                    )

                    if result:
                        relaciones_creadas += 1
                else:
                    if i <= 10:  # Mostrar solo las primeras 10 en dry-run
                        print(f"   [DRY-RUN] {origen[:30]} --[{tipo_label}]--> {destino[:30]}")
                    relaciones_creadas += 1

            except Exception as e:
                if errores < 5:  # Mostrar solo los primeros errores
                    print(f"   ❌ Error: {origen[:30]} --[{tipo_label}]--> {destino[:30]}: {e}")
                errores += 1

        print(f"\n✅ Relaciones LLM sincronizadas")
        print(f"="*60)
        print(f"  Relaciones creadas:   {relaciones_creadas:,}")
        print(f"  Errores:              {errores}")
        print(f"\n📊 Top 10 tipos de relación:")
        for tipo, count in sorted(tipos_relacion_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"     {tipo:25} {count:,}")
        print("="*60)

    def sync_personas_to_age(self, limit: int = None, dry_run: bool = False):
        """
        Sincroniza personas de PostgreSQL a AGE.

        Args:
            limit: Límite de personas a procesar (None = todas)
            dry_run: Si True, solo simula sin escribir
        """
        print("\n" + "="*60)
        print(f"🔄 SINCRONIZACIÓN POSTGRESQL → APACHE AGE")
        if dry_run:
            print("   [MODO DRY-RUN - NO SE ESCRIBIRÁ EN AGE]")
        print("="*60)

        # Obtener personas de PostgreSQL
        print(f"\n1️⃣  Obteniendo personas desde PostgreSQL...")
        personas = self.get_personas_from_postgres(limit=limit)
        print(f"   ✅ Obtenidas {len(personas)} personas únicas")

        if len(personas) == 0:
            print("   ⚠️  No hay personas para sincronizar")
            return

        # Procesar cada persona
        print(f"\n2️⃣  Creando nodos en AGE...")
        for i, (nombre, archivos, nucs, doc_ids, menciones) in enumerate(personas, 1):
            if i % 50 == 0:
                print(f"   Procesadas {i}/{len(personas)} personas...")

            try:
                if not dry_run:
                    # Crear nodo Persona (MERGE para evitar duplicados)
                    # AGE no soporta ON CREATE/ON MATCH, así que usamos MERGE simple
                    cypher_create_persona = f"""
                    MERGE (p:Persona {{nombre: '{self._escape_cypher(nombre)}'}})
                    SET p.menciones = {menciones}
                    RETURN id(p) as persona_id
                    """

                    result = self.age_connector.execute_cypher(
                        cypher_create_persona,
                        parameters=None,
                        graph_name=self.config.graph_name,
                        column_definitions=["persona_id agtype"]
                    )

                    if result:
                        self.stats['personas_procesadas'] += 1
                        self.stats['personas_nuevas'] += 1
                    else:
                        self.stats['personas_existentes'] += 1

                else:
                    print(f"   [DRY-RUN] Crearía nodo: {nombre} ({menciones} menciones)")
                    self.stats['personas_procesadas'] += 1

            except Exception as e:
                print(f"   ❌ Error procesando '{nombre}': {e}")
                self.stats['errores'] += 1

        print(f"\n✅ Sincronización completada")
        self._print_stats()

    def _escape_cypher(self, text: str) -> str:
        """Escapa comillas simples para Cypher"""
        if not text:
            return ""
        return text.replace("'", "\\'")

    def _print_stats(self):
        """Imprime estadísticas de la sincronización"""
        print(f"\n📊 ESTADÍSTICAS DE SINCRONIZACIÓN")
        print(f"="*60)
        print(f"  Personas procesadas:  {self.stats['personas_procesadas']}")
        print(f"  Personas nuevas:      {self.stats['personas_nuevas']}")
        print(f"  Personas existentes:  {self.stats['personas_existentes']}")
        print(f"  Relaciones creadas:   {self.stats['relaciones_creadas']}")
        print(f"  Errores:              {self.stats['errores']}")
        print("="*60)

    def close(self):
        """Cierra conexiones"""
        if self.pg_conn:
            self.pg_conn.close()
        # AGEConnector no tiene método close()


def main():
    parser = argparse.ArgumentParser(
        description="Sincronizar datos de PostgreSQL a Apache AGE"
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Solo analizar datos, no sincronizar"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Límite de personas a procesar (default: todas)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simular sin escribir en AGE"
    )
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="No pedir confirmación"
    )
    parser.add_argument(
        "--relaciones",
        action="store_true",
        help="Sincronizar también las relaciones de co-ocurrencia"
    )
    parser.add_argument(
        "--llm",
        action="store_true",
        help="Sincronizar relaciones extraídas por LLM"
    )

    args = parser.parse_args()

    # Banner
    print("\n" + "="*60)
    print("🔄 SINCRONIZACIÓN POSTGRESQL → APACHE AGE")
    print("="*60)

    try:
        syncer = PostgresAGESync()

        # Analizar datos
        stats = syncer.analyze_postgres_data()

        if args.analyze:
            print("\n✅ Análisis completado. Use --sync para sincronizar.")
            return 0

        # Confirmar sincronización
        if not args.yes and not args.dry_run:
            print(f"\n⚠️  Se procesarán {stats['nombres_unicos']} personas únicas")
            respuesta = input("¿Continuar con la sincronización? (s/n): ")
            if respuesta.lower() != 's':
                print("❌ Operación cancelada")
                return 1

        # Sincronizar personas
        syncer.sync_personas_to_age(limit=args.limit, dry_run=args.dry_run)

        # Sincronizar relaciones si se solicitó
        if args.relaciones:
            syncer.sync_relaciones_coocurrencia(dry_run=args.dry_run)

        # Sincronizar relaciones LLM si se solicitó
        if args.llm:
            syncer.sync_relaciones_llm(limit=args.limit, dry_run=args.dry_run)

        syncer.close()
        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
