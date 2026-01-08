"""
Parser de Entidades desde campo 'analisis' de JSONs

Extrae personas, organizaciones, lugares y relaciones del análisis
estructurado en Markdown generado por GPT-4.
"""

import re
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class Persona:
    """Representa una persona extraída"""
    nombre: str
    clasificacion: Optional[str] = None  # victima, responsable, defensa, etc.
    documento_id: Optional[str] = None
    contexto: Optional[str] = None


@dataclass
class Organizacion:
    """Representa una organización extraída"""
    nombre: str
    tipo: Optional[str] = None  # fuerza_legitima, fuerza_ilegal, etc.
    documento_id: Optional[str] = None


@dataclass
class Lugar:
    """Representa un lugar mencionado"""
    nombre: str
    tipo: Optional[str] = None  # departamento, municipio, vereda, etc.
    documento_id: Optional[str] = None


@dataclass
class Documento:
    """Representa un documento jurídico"""
    archivo: str
    nuc: Optional[str] = None
    despacho: Optional[str] = None
    cuaderno: Optional[str] = None
    tipo_documental: Optional[str] = None
    fecha_creacion: Optional[str] = None
    entidad_productora: Optional[str] = None


@dataclass
class Relacion:
    """Representa una relación entre entidades"""
    origen: str
    destino: str
    tipo: str  # co_ocurrencia, vinculo_directo, etc.
    documento_id: str
    fuerza: float = 1.0  # Peso de la relación


class AnalisisParser:
    """
    Parser del campo 'analisis' de los JSONs procesados.

    Extrae entidades estructuradas desde el texto Markdown generado por GPT-4.
    """

    def __init__(self):
        self.stats = {
            "documentos_procesados": 0,
            "personas_extraidas": 0,
            "organizaciones_extraidas": 0,
            "lugares_extraidos": 0,
            "relaciones_generadas": 0,
            "errores": 0
        }

    def parse_documento(self, json_path: str) -> Optional[Dict]:
        """
        Parsea un documento JSON y extrae todas las entidades.

        Args:
            json_path: Ruta al archivo JSON

        Returns:
            Dict con entidades extraídas o None si hay error
        """
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            archivo = data.get("archivo", Path(json_path).stem)
            analisis = data.get("analisis", "")

            if not analisis:
                return None

            # Extraer entidades
            personas = self._extraer_personas(analisis, archivo)
            organizaciones = self._extraer_organizaciones(analisis, archivo)
            lugares = self._extraer_lugares(analisis, archivo)
            documento = self._extraer_documento(data, archivo)

            # Generar relaciones de co-ocurrencia
            relaciones = self._generar_relaciones_coocurrencia(
                personas, organizaciones, archivo
            )

            # Actualizar estadísticas
            self.stats["documentos_procesados"] += 1
            self.stats["personas_extraidas"] += len(personas)
            self.stats["organizaciones_extraidas"] += len(organizaciones)
            self.stats["lugares_extraidos"] += len(lugares)
            self.stats["relaciones_generadas"] += len(relaciones)

            return {
                "documento_id": archivo,
                "documento": asdict(documento) if documento else None,
                "personas": [asdict(p) for p in personas],
                "organizaciones": [asdict(o) for o in organizaciones],
                "lugares": [asdict(l) for l in lugares],
                "relaciones": [asdict(r) for r in relaciones]
            }

        except Exception as e:
            self.stats["errores"] += 1
            print(f"Error procesando {json_path}: {e}")
            return None

    def _extraer_personas(self, analisis: str, doc_id: str) -> List[Persona]:
        """Extrae personas de la sección PERSONAS del análisis"""
        personas = []

        # Buscar sección de personas (puede ser ### PERSONAS o #### A. PERSONAS)
        personas_match = re.search(
            r'####?\s*\*?\*?[^\n]*[A-Z]\.\s*PERSONAS\*?\*?[^\n]*\n(.*?)(?=####|\Z)',
            analisis,
            re.DOTALL | re.IGNORECASE
        )

        if not personas_match:
            return personas

        seccion_personas = personas_match.group(1)

        # Extraer lista general de personas
        # Patrón flexible: "Lista general" con o sin "de personas mencionadas"
        # Acepta tanto "- **Lista" como "1. **Lista"
        lista_match = re.search(
            r'\d+\.\s*\*\*Lista general[^:]*:\*\*?\s*\n(.*?)(?:\n\d+\.\s*\*\*|\Z)',
            seccion_personas,
            re.DOTALL | re.IGNORECASE
        )

        if lista_match:
            lista_texto = lista_match.group(1)

            # Patrón mejorado para capturar:
            # - **Nombre** (Alias: xxx) o - **Nombre**
            # Evita capturar "Lista general" como nombre
            nombres = re.findall(
                r'-\s*\*\*([^*\n]+?)\*\*(?:\s*\(([^)]+)\))?',
                lista_texto
            )

            for match in nombres:
                nombre = match[0].strip()
                contexto = match[1].strip() if match[1] else None

                # Filtros: no capturar títulos como "Lista general"
                if (nombre and
                    len(nombre) > 2 and
                    'Lista general' not in nombre and
                    'Clasificación' not in nombre):
                    personas.append(Persona(
                        nombre=nombre,
                        documento_id=doc_id,
                        contexto=contexto if contexto else None
                    ))

        # Extraer clasificaciones (víctimas, responsables, etc.)
        clasificaciones = self._extraer_clasificaciones_personas(seccion_personas)

        # Actualizar clasificaciones en personas ya extraídas
        for persona in personas:
            for tipo, nombres_tipo in clasificaciones.items():
                if any(nombre.lower() in persona.nombre.lower() or
                       persona.nombre.lower() in nombre.lower()
                       for nombre in nombres_tipo):
                    persona.clasificacion = tipo
                    break

        return personas

    def _extraer_clasificaciones_personas(self, seccion: str) -> Dict[str, List[str]]:
        """Extrae clasificaciones de personas (víctimas, responsables, etc.)"""
        clasificaciones = {}

        # Buscar subsección de clasificación
        clasificacion_match = re.search(
            r'-\s*\*\*Clasificación.*?:\s*\n(.*?)(?=####|\Z)',
            seccion,
            re.DOTALL | re.IGNORECASE
        )

        if not clasificacion_match:
            return clasificaciones

        texto_clasificacion = clasificacion_match.group(1)

        # Buscar cada tipo de clasificación
        tipos = {
            "victima": r'-\s*\*\*Víctimas.*?:\s*(.*?)(?=-\s*\*\*|\Z)',
            "responsable": r'-\s*\*\*Victimarios.*?:\s*(.*?)(?=-\s*\*\*|\Z)',
            "defensa": r'-\s*\*\*Defensa.*?:\s*(.*?)(?=-\s*\*\*|\Z)',
            "actor_politico": r'-\s*\*\*Actores políticos.*?:\s*(.*?)(?=-\s*\*\*|\Z)',
        }

        for tipo, patron in tipos.items():
            match = re.search(patron, texto_clasificacion, re.DOTALL | re.IGNORECASE)
            if match:
                texto_tipo = match.group(1)
                # Extraer nombres de esta clasificación
                nombres = re.findall(r'\*\*([^*]+)\*\*', texto_tipo)
                clasificaciones[tipo] = [n.strip() for n in nombres if n.strip()]

        return clasificaciones

    def _extraer_organizaciones(self, analisis: str, doc_id: str) -> List[Organizacion]:
        """Extrae organizaciones/instituciones del análisis"""
        organizaciones = []

        # Buscar sección de organizaciones (puede ser ### o #### B. ORGANIZACIONES)
        org_match = re.search(
            r'####?\s*\*?\*?[^\n]*[B-Z]\.\s*ORGANIZACIONES[^\n]*\*?\*?[^\n]*\n(.*?)(?=####|\Z)',
            analisis,
            re.DOTALL | re.IGNORECASE
        )

        if not org_match:
            return organizaciones

        seccion_org = org_match.group(1)

        # Extraer lista general
        lista_match = re.search(
            r'-\s*\*\*Lista general.*?:\s*\n(.*?)(?=-\s*\*\*Clasificación|\Z)',
            seccion_org,
            re.DOTALL | re.IGNORECASE
        )

        if lista_match:
            lista_texto = lista_match.group(1)
            # Buscar patrones: con o sin numeración
            nombres = re.findall(r'(?:\d+\.|\-)\s*\*\*([^*\(]+)\*\*', lista_texto)

            for nombre in nombres:
                nombre = nombre.strip()
                if nombre and len(nombre) > 1:
                    organizaciones.append(Organizacion(
                        nombre=nombre,
                        documento_id=doc_id
                    ))

        # Extraer clasificaciones (fuerzas legítimas/ilegales)
        clasificacion_match = re.search(
            r'-\s*\*\*Clasificación.*?:\s*\n(.*?)(?=####|\Z)',
            seccion_org,
            re.DOTALL | re.IGNORECASE
        )

        if clasificacion_match:
            texto_clasificacion = clasificacion_match.group(1)

            # Fuerzas legítimas
            legitimas_match = re.search(
                r'-\s*\*\*Fuerzas legítimas.*?:\s*(.*?)(?=-\s*\*\*|\Z)',
                texto_clasificacion,
                re.DOTALL | re.IGNORECASE
            )
            if legitimas_match:
                nombres_leg = re.findall(r'\*\*([^*]+)\*\*', legitimas_match.group(1))
                for org in organizaciones:
                    if any(n.lower() in org.nombre.lower() for n in nombres_leg):
                        org.tipo = "fuerza_legitima"

            # Fuerzas ilegales
            ilegales_match = re.search(
                r'-\s*\*\*Fuerzas ilegales.*?:\s*(.*?)(?=-\s*\*\*|\Z)',
                texto_clasificacion,
                re.DOTALL | re.IGNORECASE
            )
            if ilegales_match:
                nombres_ileg = re.findall(r'\*\*([^*]+)\*\*', ilegales_match.group(1))
                for org in organizaciones:
                    if any(n.lower() in org.nombre.lower() for n in nombres_ileg):
                        org.tipo = "fuerza_ilegal"

        return organizaciones

    def _extraer_lugares(self, analisis: str, doc_id: str) -> List[Lugar]:
        """Extrae lugares mencionados del análisis"""
        lugares = []

        # Buscar sección de lugares (puede ser C. o similar)
        lugar_match = re.search(
            r'####\s*\*?\*?[^\n]*[C-Z]\.\s*LUGARES[^\n]*\*?\*?[^\n]*\n(.*?)(?=####|\Z)',
            analisis,
            re.DOTALL | re.IGNORECASE
        )

        if not lugar_match:
            return lugares

        seccion_lugares = lugar_match.group(1)

        # Patrones más flexibles para extraer lugares
        # Formato: - **Departamento:** Santander
        # Formato: - Ortega, Tolima: Lugar donde fue capturado
        patrones = [
            # Patrón 1: - **Departamento:** Nombre
            (r'-\s*\*\*Departamento\*?\*?:\s*([A-ZÁ-Ú][a-zá-ú\s]+)', 'departamento'),
            (r'-\s*\*\*Municipio\*?\*?:\s*([A-ZÁ-Ú][a-zá-ú\s]+)', 'municipio'),
            (r'-\s*\*\*Ciudad\*?\*?:\s*([A-ZÁ-Ú][a-zá-ú\s]+)', 'municipio'),

            # Patrón 2: - Nombre, Departamento: descripción
            (r'-\s*\*?\*?([A-ZÁ-Ú][a-zá-ú\s]+),\s+([A-ZÁ-Ú][a-zá-ú]+)\*?\*?:\s*[Ll]ugar', 'lugar_especifico'),

            # Patrón 3: vereda Nombre
            (r'[Vv]ereda\s+([A-ZÁ-Ú][a-zá-ú\s]+)', 'vereda'),
        ]

        for patron, tipo in patrones:
            matches = re.findall(patron, seccion_lugares)
            for match in matches:
                if isinstance(match, tuple):
                    # Si hay tupla, el primer elemento es el lugar principal
                    nombre = match[0].strip()
                else:
                    nombre = match.strip()

                # Limpiar y validar
                nombre = nombre.rstrip('.,;:')
                if nombre and len(nombre) > 2 and nombre not in ['No', 'Si', 'En']:
                    # Evitar duplicados
                    if not any(l.nombre.lower() == nombre.lower() for l in lugares):
                        lugares.append(Lugar(
                            nombre=nombre,
                            tipo=tipo,
                            documento_id=doc_id
                        ))

        return lugares

    def _generar_relaciones_coocurrencia(
        self,
        personas: List[Persona],
        organizaciones: List[Organizacion],
        doc_id: str
    ) -> List[Relacion]:
        """
        Genera relaciones de co-ocurrencia entre entidades del mismo documento.

        Si dos entidades aparecen en el mismo documento, existe una relación.
        """
        relaciones = []

        # Relaciones persona-persona
        for i, p1 in enumerate(personas):
            for p2 in personas[i+1:]:
                relaciones.append(Relacion(
                    origen=p1.nombre,
                    destino=p2.nombre,
                    tipo="co_ocurrencia_persona",
                    documento_id=doc_id,
                    fuerza=1.0
                ))

        # Relaciones persona-organización
        for persona in personas:
            for org in organizaciones:
                relaciones.append(Relacion(
                    origen=persona.nombre,
                    destino=org.nombre,
                    tipo="co_ocurrencia_persona_org",
                    documento_id=doc_id,
                    fuerza=1.0
                ))

        # Relaciones organización-organización
        for i, o1 in enumerate(organizaciones):
            for o2 in organizaciones[i+1:]:
                relaciones.append(Relacion(
                    origen=o1.nombre,
                    destino=o2.nombre,
                    tipo="co_ocurrencia_org",
                    documento_id=doc_id,
                    fuerza=1.0
                ))

        return relaciones

    def _extraer_documento(self, data: Dict, archivo: str) -> Optional[Documento]:
        """
        Extrae información del documento desde los metadatos.

        Args:
            data: Diccionario con todos los datos del JSON
            archivo: Nombre del archivo

        Returns:
            Objeto Documento con metadatos o None
        """
        metadatos = data.get("metadatos", {})

        # Extraer NUC (puede estar en diferentes formatos)
        nuc = metadatos.get("NUC") or metadatos.get("nuc") or data.get("nuc")

        # Extraer despacho
        despacho = metadatos.get("Despacho") or metadatos.get("despacho") or data.get("despacho")

        # Extraer cuaderno
        cuaderno = metadatos.get("Cuaderno") or metadatos.get("cuaderno")

        # Extraer tipo documental
        tipo_documental = metadatos.get("Detalle") or metadatos.get("detalle")

        # Extraer fecha de creación
        fecha_creacion = metadatos.get("Fecha de creación") or metadatos.get("fecha_creacion")

        # Extraer entidad productora
        entidad_productora = metadatos.get("Entidad productora") or metadatos.get("entidad_productora")

        return Documento(
            archivo=archivo,
            nuc=nuc,
            despacho=despacho,
            cuaderno=cuaderno,
            tipo_documental=tipo_documental,
            fecha_creacion=fecha_creacion,
            entidad_productora=entidad_productora
        )

    def get_stats(self) -> Dict:
        """Retorna estadísticas del parsing"""
        return self.stats.copy()