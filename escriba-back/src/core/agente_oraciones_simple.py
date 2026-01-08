#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agente Simplificado con Análisis por Oraciones
"""

import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

class TipoOracion(Enum):
    CONSULTA_DATOS = "consulta_datos"
    FILTRO_GEOGRAFICO = "filtro_geografico"
    ANALISIS_CONCEPTUAL = "analisis_conceptual"

class EstrategiaOracion(Enum):
    BD_DIRECTA = "bd_directa"
    RAG_SEMANTICO = "rag_semantico"
    FILTRO_APLICADO = "filtro_aplicado"

@dataclass
class OracionAnalizada:
    texto_original: str
    tipo: TipoOracion
    estrategia: EstrategiaOracion
    entidades_detectadas: Dict[str, Any]
    confianza: float

@dataclass
class PlanEjecucionCombinado:
    consulta_original: str
    oraciones_analizadas: List[OracionAnalizada]
    estrategia_principal: str
    filtros_combinados: Dict[str, Any]
    necesita_bd: bool
    necesita_rag: bool
    confianza_total: float = 0.0

class AgenteAnalisisOracionesSimple:
    
    def descomponer_en_oraciones(self, consulta: str) -> List[str]:
        """Descompone consulta en oraciones"""
        consulta = consulta.strip()
        
        # Separar por conectores
        separadores = [" y ", " que ", ", "]
        oraciones = [consulta]
        
        for sep in separadores:
            nuevas_oraciones = []
            for oracion in oraciones:
                partes = oracion.split(sep)
                nuevas_oraciones.extend([p.strip() for p in partes if p.strip()])
            oraciones = nuevas_oraciones
        
        # Filtrar oraciones válidas
        oraciones_validas = [o for o in oraciones if len(o.split()) >= 2]
        return oraciones_validas
    
    def extraer_nombre_persona(self, oracion: str) -> Optional[str]:
        """
        Extrae nombre de persona de consultas como:
        - "Quien es Ana Matilde Guzman"
        - "información de Juan Perez"
        - "menciones de Maria Lopez"
        - "victimas como Pedro Rodriguez"
        """
        oracion_lower = oracion.lower()

        # Patrones de consulta sobre personas
        patrones_persona = [
            r'quien\s+es\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)+)',
            r'quién\s+es\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)+)',
            r'información\s+de\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)+)',
            r'menciones\s+de\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)+)',
            r'víctima\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)+)',
            r'victima\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)+)',
            r'datos\s+de\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)+)',
        ]

        for patron in patrones_persona:
            match = re.search(patron, oracion, re.IGNORECASE)
            if match:
                nombre = match.group(1).strip()
                # Validar que tenga al menos 2 palabras
                if len(nombre.split()) >= 2:
                    return nombre

        return None

    def analizar_oracion_individual(self, oracion: str) -> OracionAnalizada:
        """Analiza una oración individual"""
        oracion_lower = oracion.lower()

        # Extraer entidades
        entidades = {}

        # 1. Detectar nombres de personas PRIMERO
        nombre_persona = self.extraer_nombre_persona(oracion)
        if nombre_persona:
            entidades['nombre_persona'] = nombre_persona
            tipo = TipoOracion.CONSULTA_DATOS
            estrategia = EstrategiaOracion.BD_DIRECTA
        # 2. Detectar análisis conceptuales
        elif any(palabra in oracion_lower for palabra in ['analiza', 'patrón', 'patron', 'patrones']):
            tipo = TipoOracion.ANALISIS_CONCEPTUAL
            estrategia = EstrategiaOracion.RAG_SEMANTICO
        # 3. Detectar filtros geográficos
        elif any(geo in oracion_lower for geo in ['antioquia', 'bogotá', 'cali']):
            tipo = TipoOracion.FILTRO_GEOGRAFICO
            estrategia = EstrategiaOracion.FILTRO_APLICADO
        # 4. Por defecto: consulta de datos
        else:
            tipo = TipoOracion.CONSULTA_DATOS
            estrategia = EstrategiaOracion.BD_DIRECTA

        # Extraer ubicaciones
        ubicaciones = ['antioquia', 'bogotá', 'cali']
        for ubi in ubicaciones:
            if ubi in oracion_lower:
                entidades['departamento'] = ubi.title()
                break

        return OracionAnalizada(
            texto_original=oracion,
            tipo=tipo,
            estrategia=estrategia,
            entidades_detectadas=entidades,
            confianza=0.85
        )
    
    def analizar_consulta_completa(self, consulta: str, filtros_externos: Dict[str, Any] = None) -> PlanEjecucionCombinado:
        """Análisis completo"""
        if filtros_externos is None:
            filtros_externos = {}
        
        try:
            # Descomponer
            oraciones_texto = self.descomponer_en_oraciones(consulta)
            print(f"🔍 Oraciones: {oraciones_texto}")
            
            # Analizar cada oración
            oraciones_analizadas = []
            for oracion_texto in oraciones_texto:
                oracion_analizada = self.analizar_oracion_individual(oracion_texto)
                oraciones_analizadas.append(oracion_analizada)
            
            # Combinar filtros
            filtros_combinados = filtros_externos.copy()
            for oracion in oraciones_analizadas:
                if oracion.entidades_detectadas:
                    filtros_combinados.update(oracion.entidades_detectadas)
            
            # Determinar estrategia principal
            estrategias = [o.estrategia for o in oraciones_analizadas]
            tiene_bd = any(e in [EstrategiaOracion.BD_DIRECTA, EstrategiaOracion.FILTRO_APLICADO] for e in estrategias)
            tiene_rag = any(e == EstrategiaOracion.RAG_SEMANTICO for e in estrategias)
            
            if tiene_bd and tiene_rag:
                estrategia_principal = "HIBRIDO"
            elif tiene_rag:
                estrategia_principal = "RAG_SEMANTICO"
            else:
                estrategia_principal = "BD_DIRECTA"
            
            # Confianza
            confianza_total = sum(o.confianza for o in oraciones_analizadas) / len(oraciones_analizadas) if oraciones_analizadas else 0.5
            
            return PlanEjecucionCombinado(
                consulta_original=consulta,
                oraciones_analizadas=oraciones_analizadas,
                estrategia_principal=estrategia_principal,
                filtros_combinados=filtros_combinados,
                necesita_bd=tiene_bd,
                necesita_rag=tiene_rag,
                confianza_total=confianza_total
            )
            
        except Exception as e:
            print(f"Error: {e}")
            return PlanEjecucionCombinado(
                consulta_original=consulta,
                oraciones_analizadas=[],
                estrategia_principal="BD_DIRECTA",
                filtros_combinados=filtros_externos,
                necesita_bd=True,
                necesita_rag=False,
                confianza_total=0.5
            )

def crear_agente_oraciones_simple() -> AgenteAnalisisOracionesSimple:
    return AgenteAnalisisOracionesSimple()

if __name__ == "__main__":
    agente = AgenteAnalisisOracionesSimple()
    consulta = "dame la lista de víctimas de Antioquia y analiza los patrones"
    plan = agente.analizar_consulta_completa(consulta)
    
    print(f"Consulta: {consulta}")
    print(f"Estrategia: {plan.estrategia_principal}")
    print(f"Filtros: {plan.filtros_combinados}")
    for i, oracion in enumerate(plan.oraciones_analizadas, 1):
        print(f"  {i}. '{oracion.texto_original}' → {oracion.tipo.value} → {oracion.estrategia.value}")
