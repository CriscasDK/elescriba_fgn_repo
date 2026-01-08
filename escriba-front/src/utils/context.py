"""Utilidades para reescritura contextual de consultas."""

import re
from typing import Tuple, List, Dict, Any


def reescribir_query_con_contexto(consulta_actual: str, history_data: Dict[str, Any]) -> Tuple[str, bool, List[str], int]:
    """
    Reescribe una query contextual agregando entidades del historial.

    Esta función soluciona la limitación del RAG con preguntas secuenciales:
    - Pregunta 1: "Oswaldo Olivo" → RAG busca chunks sobre Oswaldo
    - Pregunta 2: "su relación con Rosa Edith Sierra" → RAG NO encuentra la conexión

    Con reescritura:
    - Pregunta 2 se convierte en: "Oswaldo Olivo y su relación con Rosa Edith Sierra"

    LÍMITE DE SECUENCIA:
    - Después de 3 reescrituras consecutivas, toma SOLO la última entidad
    - Esto evita acumulación de entidades y drift semántico
    - Ejemplo: "Juan y María y Pedro" → Después de 3, solo "Pedro"

    Args:
        consulta_actual: La consulta del usuario que puede tener referencias contextuales
        history_data: Diccionario con historial de conversaciones

    Returns:
        tuple: (query_reescrita, fue_reescrita, entidades_agregadas, consecutive_rewrites)
    """
    # Detectar si la consulta tiene referencias contextuales
    referencias_contextuales = [
        'su ', 'sus ', 'él', 'ella', 'ellos', 'ellas',
        'esa persona', 'ese caso', 'esa organización',
        'la anterior', 'el anterior', 'lo anterior',
        'mencionado', 'mencionada', 'de esa', 'de ese'
    ]

    consulta_lower = consulta_actual.lower()
    tiene_referencia = any(ref in consulta_lower for ref in referencias_contextuales)

    if not tiene_referencia:
        # No es una pregunta contextual, retornar sin cambios
        return (consulta_actual, False, [], 0)

    # ✅ NUEVO: Contar reescrituras consecutivas para evitar drift
    consecutive_rewrites = 0
    if history_data and history_data.get('history'):
        for conv in reversed(history_data['history'][-5:]):  # Revisar últimas 5
            if conv.get('query_rewritten', False):
                consecutive_rewrites += 1
            else:
                break  # Se encontró una consulta NO reescrita, detener conteo

    # Extraer entidades de las últimas 2 conversaciones
    entidades_contexto = []
    if history_data and history_data.get('history'):
        ultimas_conversaciones = history_data['history'][-2:]  # Últimas 2

        for conv in ultimas_conversaciones:
            user_query = conv.get('user_query', '')
            # Extraer nombres propios de la consulta previa
            nombres = re.findall(
                r'\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)+\b',
                user_query
            )
            for nombre in nombres:
                if nombre not in entidades_contexto:
                    entidades_contexto.append(nombre)

    if not entidades_contexto:
        # No hay entidades en el contexto, retornar sin cambios
        return (consulta_actual, False, [], consecutive_rewrites)

    # ✅ LÍMITE: Después de 3 reescrituras, tomar SOLO la última entidad
    if consecutive_rewrites >= 3:
        print(f"⚠️  LÍMITE DE SECUENCIA ALCANZADO ({consecutive_rewrites} reescrituras consecutivas)")
        print(f"   Tomando SOLO última entidad para evitar drift semántico")
        entidades_contexto = entidades_contexto[-1:]  # Solo la última

    # Reescribir query agregando entidades del contexto
    # Estrategia: agregar entidades al inicio
    entidades_str = " y ".join(entidades_contexto)
    query_reescrita = f"{entidades_str}: {consulta_actual}"

    print(f"🔄 REESCRITURA DE QUERY (secuencia #{consecutive_rewrites + 1}):")
    print(f"   Original: '{consulta_actual}'")
    print(f"   Reescrita: '{query_reescrita}'")
    print(f"   Entidades agregadas: {entidades_contexto}")

    return (query_reescrita, True, entidades_contexto, consecutive_rewrites + 1)


# ❌ DESACTIVADA: Secuenciación SQL
# Razón: Demasiado compleja, casos ambiguos causan resultados incorrectos
# Ejemplo: "víctimas en Antioquia" → "de esos en Medellín" → 0 resultados
# Se mantiene solo reescritura RAG que cubre el 80% de casos
#
# def detectar_referencia_sql(consulta: str, history_data: dict) -> tuple:
#     """
#     Detecta referencias a resultados SQL previos en la consulta actual.
#     DESACTIVADA - Ver razones arriba
#     """
#     return (False, [], None)
