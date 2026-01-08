"""Utilidades para extracción de entidades de consultas."""

import re
from typing import List
from config.constants import ENTIDADES_NO_PERSONAS


def extraer_entidades_de_consulta(consulta: str) -> List[str]:
    """
    Extrae nombres de entidades (personas, organizaciones) de una consulta.
    Reutiliza la lógica de clasificar_consulta() en core/consultas.py línea 830.

    Args:
        consulta: Texto de la consulta del usuario

    Returns:
        Lista de nombres de entidades encontradas
    """
    # Mismo regex que en clasificar_consulta() línea 830
    nombres_propios = re.findall(
        r'\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*\b',
        consulta
    )

    # Filtrar nombres que NO son entidades geográficas/conceptuales
    nombres_entidades = []
    for nombre in nombres_propios:
        if nombre.lower() not in ENTIDADES_NO_PERSONAS:
            nombres_entidades.append(nombre)

    return nombres_entidades
