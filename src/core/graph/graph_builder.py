"""
Graph Builder - Poblado masivo del grafo desde JSONs

Toma entidades parseadas y las inserta eficientemente en Apache AGE.
Maneja duplicados, batch inserts, y progress tracking.
"""

import json
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict
from tqdm import tqdm
import time

from .parser import AnalisisParser, Persona, Organizacion, Lugar, Documento, Relacion
from .age_connector import AGEConnector
from .config import GraphConfig


class GraphBuilder:
    """
    Constructor del grafo de documentos jurídicos.

    Responsabilidades:
    - Procesar JSONs en batch
    - Deduplicar entidades
    - Insertar nodos y relaciones eficientemente
    - Reportar progreso y estadísticas
    """

    def __init__(self, config: Optional[GraphConfig] = None):
        """
        Inicializa el builder.

        Args:
            config: Configuración del grafo
        """
        self.config = config or GraphConfig()
        self.parser = AnalisisParser()
        self.connector = AGEConnector(config)

        # Trackers para deduplicación
        self.personas_vistas: Set[str] = set()
        self.organizaciones_vistas: Set[str] = set()
        self.lugares_vistos: Set[str] = set()
        self.documentos_vistos: Set[str] = set()
        self.relaciones_vistas: Set[Tuple[str, str, str]] = set()

        # Tracker para documentos por NUC (para relaciones REFERENCIA_A)
        self.documentos_por_nuc: Dict[str, List[str]] = defaultdict(list)

        # Estadísticas
        self.stats = {
            "documentos_procesados": 0,
            "documentos_con_entidades": 0,
            "documentos_sin_entidades": 0,
            "documentos_nodos_insertados": 0,
            "personas_insertadas": 0,
            "organizaciones_insertadas": 0,
            "lugares_insertados": 0,
            "relaciones_insertadas": 0,
            "errores": 0,
            "tiempo_total": 0.0
        }

    def _normalizar_nombre(self, nombre: str) -> str:
        """
        Normaliza un nombre para deduplicación.

        Args:
            nombre: Nombre a normalizar

        Returns:
            Nombre normalizado (lowercase, stripped)
        """
        return nombre.strip().lower()

    def _crear_nodo_persona(self, persona: Persona, graph_name: str) -> bool:
        """
        Crea un nodo de tipo Persona en el grafo.

        Args:
            persona: Objeto Persona
            graph_name: Nombre del grafo

        Returns:
            True si se creó exitosamente
        """
        nombre_normalizado = self._normalizar_nombre(persona.nombre)

        # Evitar duplicados
        if nombre_normalizado in self.personas_vistas:
            return False

        properties = {
            "nombre": persona.nombre,
            "nombre_normalizado": nombre_normalizado,
            "tipo": "persona"
        }

        if persona.clasificacion:
            properties["clasificacion"] = persona.clasificacion

        if persona.documento_id:
            properties["documentos"] = [persona.documento_id]

        if self.connector.create_node("Persona", properties, graph_name):
            self.personas_vistas.add(nombre_normalizado)
            self.stats["personas_insertadas"] += 1
            return True

        return False

    def _crear_nodo_organizacion(self, org: Organizacion, graph_name: str) -> bool:
        """
        Crea un nodo de tipo Organizacion en el grafo.

        Args:
            org: Objeto Organizacion
            graph_name: Nombre del grafo

        Returns:
            True si se creó exitosamente
        """
        nombre_normalizado = self._normalizar_nombre(org.nombre)

        # Evitar duplicados
        if nombre_normalizado in self.organizaciones_vistas:
            return False

        properties = {
            "nombre": org.nombre,
            "nombre_normalizado": nombre_normalizado,
            "tipo": "organizacion"
        }

        if org.tipo:
            properties["subtipo"] = org.tipo

        if org.documento_id:
            properties["documentos"] = [org.documento_id]

        if self.connector.create_node("Organizacion", properties, graph_name):
            self.organizaciones_vistas.add(nombre_normalizado)
            self.stats["organizaciones_insertadas"] += 1
            return True

        return False

    def _crear_nodo_lugar(self, lugar: Lugar, graph_name: str) -> bool:
        """
        Crea un nodo de tipo Lugar en el grafo.

        Args:
            lugar: Objeto Lugar
            graph_name: Nombre del grafo

        Returns:
            True si se creó exitosamente
        """
        nombre_normalizado = self._normalizar_nombre(lugar.nombre)

        # Evitar duplicados
        if nombre_normalizado in self.lugares_vistos:
            return False

        properties = {
            "nombre": lugar.nombre,
            "nombre_normalizado": nombre_normalizado,
            "tipo": "lugar"
        }

        if lugar.tipo:
            properties["subtipo"] = lugar.tipo

        if lugar.documento_id:
            properties["documentos"] = [lugar.documento_id]

        if self.connector.create_node("Lugar", properties, graph_name):
            self.lugares_vistos.add(nombre_normalizado)
            self.stats["lugares_insertados"] += 1
            return True

        return False

    def _crear_nodo_documento(self, documento: Documento, graph_name: str) -> bool:
        """
        Crea un nodo de tipo Documento en el grafo.

        Args:
            documento: Objeto Documento
            graph_name: Nombre del grafo

        Returns:
            True si se creó exitosamente
        """
        archivo_normalizado = self._normalizar_nombre(documento.archivo)

        # Evitar duplicados
        if archivo_normalizado in self.documentos_vistos:
            return False

        properties = {
            "archivo": documento.archivo,
            "archivo_normalizado": archivo_normalizado,
            "tipo": "documento"
        }

        if documento.nuc:
            properties["nuc"] = documento.nuc
            # Registrar para relaciones REFERENCIA_A posteriores
            self.documentos_por_nuc[documento.nuc].append(documento.archivo)

        if documento.despacho:
            properties["despacho"] = documento.despacho

        if documento.cuaderno:
            properties["cuaderno"] = documento.cuaderno

        if documento.tipo_documental:
            properties["tipo_documental"] = documento.tipo_documental

        if documento.fecha_creacion:
            properties["fecha_creacion"] = documento.fecha_creacion

        if documento.entidad_productora:
            properties["entidad_productora"] = documento.entidad_productora

        if self.connector.create_node("Documento", properties, graph_name):
            self.documentos_vistos.add(archivo_normalizado)
            self.stats["documentos_nodos_insertados"] += 1
            return True

        return False

    def _crear_relacion(self, relacion: Relacion, graph_name: str) -> bool:
        """
        Crea una relación entre dos entidades.

        Args:
            relacion: Objeto Relacion
            graph_name: Nombre del grafo

        Returns:
            True si se creó exitosamente
        """
        # Normalizar para deduplicación
        origen_norm = self._normalizar_nombre(relacion.origen)
        destino_norm = self._normalizar_nombre(relacion.destino)

        # Evitar duplicados (misma relación en ambas direcciones)
        rel_tuple = tuple(sorted([origen_norm, destino_norm]) + [relacion.tipo])
        if rel_tuple in self.relaciones_vistas:
            return False

        # Determinar etiquetas de los nodos (pueden ser Persona, Organizacion o Lugar)
        # Por ahora asumimos que son del mismo tipo o usamos una búsqueda genérica
        # En AGE podemos usar MATCH (n) WHERE n.nombre_normalizado = ...

        # Propiedades de la relación
        rel_props = {
            "tipo_relacion": relacion.tipo,
            "fuerza": relacion.fuerza,
            "documento_id": relacion.documento_id
        }

        # Intentar crear la relación
        # Nota: AGE tiene issues con MATCH en algunos casos, podemos necesitar
        # un approach más robusto posteriormente
        try:
            # Crear usando una query Cypher más flexible
            # Buscar por nombre_normalizado O archivo_normalizado (para documentos)
            cypher = f"""
            MATCH (a) WHERE a.nombre_normalizado = '{origen_norm}' OR a.archivo_normalizado = '{origen_norm}'
            MATCH (b) WHERE b.nombre_normalizado = '{destino_norm}' OR b.archivo_normalizado = '{destino_norm}'
            CREATE (a)-[r:VINCULADO {{tipo_relacion: '{relacion.tipo}', fuerza: {relacion.fuerza}, documento_id: '{relacion.documento_id}'}}]->(b)
            RETURN r
            """

            result = self.connector.execute_cypher(cypher, graph_name=graph_name)

            if result:
                self.relaciones_vistas.add(rel_tuple)
                self.stats["relaciones_insertadas"] += 1
                return True
        except Exception as e:
            # Silenciosamente fallar en relaciones (problema conocido de AGE)
            pass

        return False

    def procesar_documento(self, json_path: Path, graph_name: str) -> Dict:
        """
        Procesa un documento JSON individual.

        Args:
            json_path: Ruta al archivo JSON
            graph_name: Nombre del grafo

        Returns:
            Dict con estadísticas del documento
        """
        try:
            # Usar el parser para procesar el documento
            resultado = self.parser.parse_documento(str(json_path))

            if not resultado:
                self.stats["documentos_sin_entidades"] += 1
                return {"procesado": True, "tiene_entidades": False}

            self.stats["documentos_con_entidades"] += 1

            # Crear nodo de documento si existe
            documento_nodo = None
            if resultado.get("documento"):
                documento_nodo = Documento(**resultado["documento"])
                self._crear_nodo_documento(documento_nodo, graph_name)

            # Convertir dicts de vuelta a objetos para crear nodos
            # Los datos vienen como dicts del parser
            for persona_dict in resultado["personas"]:
                persona = Persona(**persona_dict)
                self._crear_nodo_persona(persona, graph_name)

            for org_dict in resultado["organizaciones"]:
                org = Organizacion(**org_dict)
                self._crear_nodo_organizacion(org, graph_name)

            for lugar_dict in resultado["lugares"]:
                lugar = Lugar(**lugar_dict)
                self._crear_nodo_lugar(lugar, graph_name)

            # Insertar relaciones de co-ocurrencia
            for relacion_dict in resultado["relaciones"]:
                relacion = Relacion(**relacion_dict)
                self._crear_relacion(relacion, graph_name)

            # Crear relaciones tipadas basadas en clasificaciones
            relaciones_clasificacion = self._crear_relaciones_por_clasificacion(
                resultado["personas"],
                resultado["organizaciones"],
                resultado["documento_id"],
                graph_name
            )

            # Crear relaciones documentales (MENCIONADO_EN)
            relaciones_documentales = 0
            if documento_nodo:
                relaciones_documentales = self._crear_relaciones_documentales(
                    resultado["personas"],
                    resultado["organizaciones"],
                    resultado["lugares"],
                    documento_nodo.archivo,
                    graph_name
                )

            # Crear relaciones geográficas (UBICADO_EN, OPERA_EN, PERTENECE_A)
            relaciones_geograficas = self._crear_relaciones_geograficas(
                resultado["personas"],
                resultado["organizaciones"],
                resultado["lugares"],
                resultado["documento_id"],
                graph_name
            )

            self.stats["documentos_procesados"] += 1

            return {
                "procesado": True,
                "tiene_entidades": True,
                "personas": len(resultado["personas"]),
                "organizaciones": len(resultado["organizaciones"]),
                "lugares": len(resultado["lugares"]),
                "relaciones": len(resultado["relaciones"]) + relaciones_clasificacion
            }

        except Exception as e:
            self.stats["errores"] += 1
            return {"procesado": False, "razon": "error", "error": str(e)}

    def construir_desde_directorio(
        self,
        json_dir: Path,
        graph_name: Optional[str] = None,
        limit: Optional[int] = None,
        recrear_grafo: bool = False
    ) -> Dict:
        """
        Construye el grafo procesando todos los JSONs de un directorio.

        Args:
            json_dir: Directorio con archivos JSON
            graph_name: Nombre del grafo (usa config si no se proporciona)
            limit: Límite de documentos a procesar (None = todos)
            recrear_grafo: Si True, elimina y recrea el grafo

        Returns:
            Dict con estadísticas finales
        """
        graph_name = graph_name or self.config.graph_name
        json_dir = Path(json_dir)

        if not json_dir.exists():
            raise ValueError(f"Directorio no existe: {json_dir}")

        # Preparar grafo
        if recrear_grafo:
            print(f"🗑️  Eliminando grafo existente '{graph_name}'...")
            self.connector.drop_graph(graph_name)

        if not self.connector.graph_exists(graph_name):
            print(f"📊 Creando grafo '{graph_name}'...")
            self.connector.create_graph(graph_name)
        else:
            print(f"📊 Usando grafo existente '{graph_name}'")

        # Obtener lista de JSONs
        json_files = list(json_dir.glob("*.json"))

        if limit:
            json_files = json_files[:limit]

        total_files = len(json_files)
        print(f"\n📁 Archivos a procesar: {total_files}")
        print(f"📍 Directorio: {json_dir}")
        print(f"🎯 Grafo: {graph_name}\n")

        # Procesar con progress bar
        start_time = time.time()

        with tqdm(total=total_files, desc="Procesando JSONs", unit="doc") as pbar:
            for json_file in json_files:
                self.procesar_documento(json_file, graph_name)
                pbar.update(1)

                # Actualizar descripción con stats en tiempo real
                pbar.set_postfix({
                    "Personas": self.stats["personas_insertadas"],
                    "Orgs": self.stats["organizaciones_insertadas"],
                    "Lugares": self.stats["lugares_insertados"],
                    "Rels": self.stats["relaciones_insertadas"]
                })

        self.stats["tiempo_total"] = time.time() - start_time

        # Obtener estadísticas finales del grafo
        graph_stats = self.connector.get_graph_stats(graph_name)

        # Reporte final
        self._imprimir_reporte_final(graph_stats)

        return {
            "stats_builder": self.stats,
            "stats_grafo": graph_stats
        }

    def _imprimir_reporte_final(self, graph_stats: Dict) -> None:
        """Imprime reporte final de construcción"""
        print("\n" + "="*60)
        print("📊 REPORTE FINAL DE CONSTRUCCIÓN DEL GRAFO")
        print("="*60)

        print("\n📄 Documentos:")
        print(f"   Procesados:        {self.stats['documentos_procesados']}")
        print(f"   Con entidades:     {self.stats['documentos_con_entidades']}")
        print(f"   Sin entidades:     {self.stats['documentos_sin_entidades']}")
        print(f"   Errores:           {self.stats['errores']}")

        print("\n🏷️  Nodos insertados (únicos):")
        print(f"   Personas:          {self.stats['personas_insertadas']}")
        print(f"   Organizaciones:    {self.stats['organizaciones_insertadas']}")
        print(f"   Lugares:           {self.stats['lugares_insertados']}")
        print(f"   Documentos:        {self.stats['documentos_nodos_insertados']}")
        print(f"   TOTAL:             {self.stats['personas_insertadas'] + self.stats['organizaciones_insertadas'] + self.stats['lugares_insertados'] + self.stats['documentos_nodos_insertados']}")

        print("\n🔗 Relaciones:")
        print(f"   Insertadas:        {self.stats['relaciones_insertadas']}")

        print("\n📊 Estadísticas del grafo (verificadas en AGE):")
        print(f"   Nodos totales:     {graph_stats.get('total_nodes', 0)}")
        print(f"   Relaciones:        {graph_stats.get('total_relationships', 0)}")

        print("\n⏱️  Performance:")
        print(f"   Tiempo total:      {self.stats['tiempo_total']:.2f} segundos")
        if self.stats['documentos_procesados'] > 0:
            docs_por_seg = self.stats['documentos_procesados'] / self.stats['tiempo_total']
            print(f"   Docs/segundo:      {docs_por_seg:.2f}")

        print("\n" + "="*60 + "\n")

    def _crear_relaciones_por_clasificacion(
        self,
        personas: List[Dict],
        organizaciones: List[Dict],
        documento_id: str,
        graph_name: str
    ) -> int:
        """
        Crea relaciones tipadas basadas en las clasificaciones de personas.

        Ejemplos de relaciones:
        - Víctima -> VICTIMIZADO_POR -> Responsable
        - Víctima -> VINCULADO_A -> Organización (fuerza ilegal)
        - Responsable -> MIEMBRO_DE -> Organización (fuerza ilegal)

        Args:
            personas: Lista de diccionarios con personas
            organizaciones: Lista de diccionarios con organizaciones
            documento_id: ID del documento
            graph_name: Nombre del grafo

        Returns:
            Número de relaciones creadas
        """
        relaciones_creadas = 0

        # Separar personas por clasificación
        victimas = [p for p in personas if p.get('clasificacion') == 'victima']
        responsables = [p for p in personas if p.get('clasificacion') == 'responsable']

        # Separar organizaciones por tipo
        fuerzas_ilegales = [o for o in organizaciones if o.get('tipo') == 'fuerza_ilegal']
        fuerzas_legitimas = [o for o in organizaciones if o.get('tipo') == 'fuerza_legitima']

        # 1. Relaciones Víctima -> VICTIMIZADO_POR -> Responsable
        for victima in victimas:
            for responsable in responsables:
                relacion = Relacion(
                    origen=victima['nombre'],
                    destino=responsable['nombre'],
                    tipo='VICTIMIZADO_POR',
                    documento_id=documento_id,
                    fuerza=2.0  # Mayor peso por ser relación tipada
                )
                if self._crear_relacion(relacion, graph_name):
                    relaciones_creadas += 1

        # 2. Relaciones Víctima -> VINCULADO_A -> Organización Ilegal
        for victima in victimas:
            for org in fuerzas_ilegales:
                relacion = Relacion(
                    origen=victima['nombre'],
                    destino=org['nombre'],
                    tipo='VINCULADO_A',
                    documento_id=documento_id,
                    fuerza=1.5
                )
                if self._crear_relacion(relacion, graph_name):
                    relaciones_creadas += 1

        # 3. Relaciones Responsable -> MIEMBRO_DE -> Organización Ilegal
        for responsable in responsables:
            for org in fuerzas_ilegales:
                relacion = Relacion(
                    origen=responsable['nombre'],
                    destino=org['nombre'],
                    tipo='MIEMBRO_DE',
                    documento_id=documento_id,
                    fuerza=2.0
                )
                if self._crear_relacion(relacion, graph_name):
                    relaciones_creadas += 1

        # 4. Relaciones Víctima -> ASISTIDO_POR -> Organización Legítima
        for victima in victimas:
            for org in fuerzas_legitimas:
                relacion = Relacion(
                    origen=victima['nombre'],
                    destino=org['nombre'],
                    tipo='ASISTIDO_POR',
                    documento_id=documento_id,
                    fuerza=1.0
                )
                if self._crear_relacion(relacion, graph_name):
                    relaciones_creadas += 1

        return relaciones_creadas

    def _crear_relaciones_documentales(
        self,
        personas: List[Dict],
        organizaciones: List[Dict],
        lugares: List[Dict],
        archivo_documento: str,
        graph_name: str
    ) -> int:
        """
        Crea relaciones documentales (MENCIONADO_EN) entre entidades y documentos.

        Args:
            personas: Lista de diccionarios con personas
            organizaciones: Lista de diccionarios con organizaciones
            lugares: Lista de diccionarios con lugares
            archivo_documento: Nombre del archivo del documento
            graph_name: Nombre del grafo

        Returns:
            Número de relaciones creadas
        """
        relaciones_creadas = 0

        # Relaciones Persona -> MENCIONADO_EN -> Documento
        for persona in personas:
            relacion = Relacion(
                origen=persona['nombre'],
                destino=archivo_documento,
                tipo='MENCIONADO_EN',
                documento_id=archivo_documento,
                fuerza=1.0
            )
            if self._crear_relacion(relacion, graph_name):
                relaciones_creadas += 1

        # Relaciones Organizacion -> MENCIONADO_EN -> Documento
        for org in organizaciones:
            relacion = Relacion(
                origen=org['nombre'],
                destino=archivo_documento,
                tipo='MENCIONADO_EN',
                documento_id=archivo_documento,
                fuerza=1.0
            )
            if self._crear_relacion(relacion, graph_name):
                relaciones_creadas += 1

        # Relaciones Lugar -> MENCIONADO_EN -> Documento
        for lugar in lugares:
            relacion = Relacion(
                origen=lugar['nombre'],
                destino=archivo_documento,
                tipo='MENCIONADO_EN',
                documento_id=archivo_documento,
                fuerza=1.0
            )
            if self._crear_relacion(relacion, graph_name):
                relaciones_creadas += 1

        return relaciones_creadas

    def _crear_relaciones_geograficas(
        self,
        personas: List[Dict],
        organizaciones: List[Dict],
        lugares: List[Dict],
        documento_id: str,
        graph_name: str
    ) -> int:
        """
        Crea relaciones geográficas entre entidades y lugares.

        Relaciones creadas:
        - Persona -> UBICADO_EN -> Lugar
        - Organizacion -> OPERA_EN -> Lugar
        - Lugar -> PERTENECE_A -> Lugar (jerarquía: municipio -> departamento)

        Args:
            personas: Lista de diccionarios con personas
            organizaciones: Lista de diccionarios con organizaciones
            lugares: Lista de diccionarios con lugares
            documento_id: ID del documento
            graph_name: Nombre del grafo

        Returns:
            Número de relaciones creadas
        """
        relaciones_creadas = 0

        # Si solo hay un lugar, todas las personas y organizaciones están ahí
        if len(lugares) == 1:
            lugar_unico = lugares[0]

            # Persona -> UBICADO_EN -> Lugar
            for persona in personas:
                relacion = Relacion(
                    origen=persona['nombre'],
                    destino=lugar_unico['nombre'],
                    tipo='UBICADO_EN',
                    documento_id=documento_id,
                    fuerza=0.8  # Menor certeza (inferido)
                )
                if self._crear_relacion(relacion, graph_name):
                    relaciones_creadas += 1

            # Organizacion -> OPERA_EN -> Lugar
            for org in organizaciones:
                relacion = Relacion(
                    origen=org['nombre'],
                    destino=lugar_unico['nombre'],
                    tipo='OPERA_EN',
                    documento_id=documento_id,
                    fuerza=0.8
                )
                if self._crear_relacion(relacion, graph_name):
                    relaciones_creadas += 1

        # Crear jerarquías de lugares: municipio -> departamento
        # Agrupar lugares por tipo
        departamentos = [l for l in lugares if l.get('tipo') == 'departamento']
        municipios = [l for l in lugares if l.get('tipo') == 'municipio']

        # Si hay municipios y departamentos, conectarlos
        if departamentos and municipios:
            for municipio in municipios:
                for departamento in departamentos:
                    relacion = Relacion(
                        origen=municipio['nombre'],
                        destino=departamento['nombre'],
                        tipo='PERTENECE_A',
                        documento_id=documento_id,
                        fuerza=1.5  # Alta certeza
                    )
                    if self._crear_relacion(relacion, graph_name):
                        relaciones_creadas += 1

        return relaciones_creadas