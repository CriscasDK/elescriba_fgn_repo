"""
Módulo de Filtrado Universal para Sistema RAG Jurídico
Aplica filtros tanto a consultas de base de datos como a Azure Search
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date

class FiltroUniversal:
    """Maneja filtros que se aplican tanto a BD como a Azure Search"""
    
    def __init__(self):
        self.filtros_activos = {}
    
    def procesar_filtros_interfaz(self, session_state) -> Dict[str, Any]:
        """Extrae filtros activos desde la interfaz de Streamlit"""
        filtros = {}
        
        # 1. Filtro NUCs - solo aplicar si hay NUCs específicos seleccionados
        # Lista vacía = "Todos los NUCs" (no aplicar filtro)
        if hasattr(session_state, 'nucs_filtro') and session_state.nucs_filtro and len(session_state.nucs_filtro) > 0:
            filtros['nucs'] = session_state.nucs_filtro
        
        # 2. Filtro fechas
        if hasattr(session_state, 'fecha_inicio') and session_state.fecha_inicio:
            filtros['fecha_inicio'] = session_state.fecha_inicio
        if hasattr(session_state, 'fecha_fin') and session_state.fecha_fin:
            filtros['fecha_fin'] = session_state.fecha_fin
        
        # 3. Filtro departamento
        if hasattr(session_state, 'departamento_filtro') and session_state.departamento_filtro != "Todos":
            filtros['departamento'] = session_state.departamento_filtro
        
        # 4. Filtro municipio
        if hasattr(session_state, 'municipio_filtro') and session_state.municipio_filtro != "Todos":
            filtros['municipio'] = session_state.municipio_filtro
        
        # 5. Filtro tipo documento
        if hasattr(session_state, 'tipo_doc_filtro') and session_state.tipo_doc_filtro != "Todos":
            filtros['tipo_documento'] = session_state.tipo_doc_filtro
        
        # 6. Filtro despacho
        if hasattr(session_state, 'despacho_filtro') and session_state.despacho_filtro != "Todos":
            filtros['despacho'] = session_state.despacho_filtro
        
        self.filtros_activos = filtros
        return filtros
    
    def aplicar_filtros_bd(self, sql_base: str, params_base: List, filtros: Dict[str, Any]) -> Tuple[str, List]:
        """Aplica filtros a consulta SQL de PostgreSQL"""
        sql = sql_base
        params = params_base.copy()
        
        # NUCs - múltiples valores
        if 'nucs' in filtros and filtros['nucs']:
            placeholders = ','.join(['%s'] * len(filtros['nucs']))
            sql += f" AND m.nuc IN ({placeholders})"
            params.extend(filtros['nucs'])
        
        # Fechas
        if 'fecha_inicio' in filtros:
            sql += " AND m.fecha >= %s"
            params.append(filtros['fecha_inicio'])
        
        if 'fecha_fin' in filtros:
            sql += " AND m.fecha <= %s"
            params.append(filtros['fecha_fin'])
        
        # Despacho
        if 'despacho' in filtros:
            sql += " AND m.despacho ILIKE %s"
            params.append(f"%{filtros['despacho']}%")
        
        # Tipo documento
        if 'tipo_documento' in filtros:
            sql += " AND m.detalle ILIKE %s"
            params.append(f"%{filtros['tipo_documento']}%")
        
        # Departamento - usar metadatos existentes en lugar de analisis_lugares
        if 'departamento' in filtros:
            # Buscar en campos de metadatos que contengan información de lugar
            sql += " AND (m.resumen ILIKE %s OR m.detalle ILIKE %s OR m.analisis ILIKE %s)"
            dept_param = f"%{filtros['departamento']}%"
            params.extend([dept_param, dept_param, dept_param])
        
        # Municipio - usar metadatos existentes en lugar de analisis_lugares
        if 'municipio' in filtros:
            # Buscar en campos de metadatos que contengan información de lugar
            sql += " AND (m.resumen ILIKE %s OR m.detalle ILIKE %s OR m.analisis ILIKE %s)"
            mun_param = f"%{filtros['municipio']}%"
            params.extend([mun_param, mun_param, mun_param])
        
        return sql, params
    
    def aplicar_filtros_azure_search(self, filtros: Dict[str, Any]) -> str:
        """Construye filtro OData para Azure Search"""
        filtro_partes = []
        
        # NUCs - múltiples valores
        if 'nucs' in filtros and filtros['nucs']:
            # Convertir lista a filtro OR
            nuc_filtros = [f"nuc eq '{nuc}'" for nuc in filtros['nucs']]
            if len(nuc_filtros) == 1:
                filtro_partes.append(nuc_filtros[0])
            else:
                filtro_partes.append(f"({' or '.join(nuc_filtros)})")
        
        # Fechas - convertir a string ISO
        if 'fecha_inicio' in filtros:
            fecha_inicio_str = filtros['fecha_inicio'].strftime('%Y-%m-%d')
            filtro_partes.append(f"fecha ge '{fecha_inicio_str}'")
        
        if 'fecha_fin' in filtros:
            fecha_fin_str = filtros['fecha_fin'].strftime('%Y-%m-%d')
            filtro_partes.append(f"fecha le '{fecha_fin_str}'")
        
        # Despacho
        if 'despacho' in filtros:
            filtro_partes.append(f"search.ismatch('{filtros['despacho']}', 'despacho')")
        
        # Tipo documento
        if 'tipo_documento' in filtros:
            filtro_partes.append(f"search.ismatch('{filtros['tipo_documento']}', 'tipo_documento')")
        
        # Departamento - usar campos poblados lugares_hechos y lugares_chunk
        if 'departamento' in filtros:
            filtro_partes.append(f"search.ismatch('{filtros['departamento']}', 'lugares_hechos,lugares_chunk')")
        
        # Municipio - usar campos poblados lugares_hechos y lugares_chunk
        if 'municipio' in filtros:
            filtro_partes.append(f"search.ismatch('{filtros['municipio']}', 'lugares_hechos,lugares_chunk')")
        
        # Combinar con AND
        return ' and '.join(filtro_partes) if filtro_partes else None
    
    def aplicar_filtros_busqueda_cruzada(self, filtros: Dict[str, Any]) -> Dict[str, str]:
        """Genera filtros para búsqueda cruzada entre índices Azure Search"""
        filtros_resultado = {}
        
        # Filtro para chunks (exhaustive-legal-chunks-v2)
        filtro_chunks = self.aplicar_filtros_azure_search(filtros)
        if filtro_chunks:
            filtros_resultado['chunks'] = filtro_chunks
        
        # Filtro para documentos completos (exhaustive-legal-index)
        # Puede tener campos diferentes, ajustamos según disponibilidad
        filtro_docs = self._adaptar_filtros_para_documentos_completos(filtros)
        if filtro_docs:
            filtros_resultado['documentos'] = filtro_docs
        
        return filtros_resultado
    
    def _adaptar_filtros_para_documentos_completos(self, filtros: Dict[str, Any]) -> str:
        """
        Adapta filtros para el índice de documentos completos (exhaustive-legal-index)
        
        Basado en inspección real del índice:
        - metadatos_nuc: campo para expediente/NUC  
        - metadatos_entidad_productora: entidad responsable
        - metadatos_fecha_creacion: fecha del documento
        - tipo_documento: tipo documental (puede estar vacío)
        - lugares_hechos, fechas_hechos: existen pero pueden estar vacíos
        """
        filtro_partes = []
        
        # NUCs -> metadatos_nuc (campo real confirmado)
        if 'nucs' in filtros and filtros['nucs']:
            nuc_filtros = [f"metadatos_nuc eq '{nuc}'" for nuc in filtros['nucs']]
            if len(nuc_filtros) == 1:
                filtro_partes.append(nuc_filtros[0])
            else:
                filtro_partes.append(f"({' or '.join(nuc_filtros)})")
        
        # Tipo documento - campo existe pero puede estar vacío
        if 'tipo_documento' in filtros:
            filtro_partes.append(f"search.ismatch('{filtros['tipo_documento']}', 'tipo_documento')")
        
        # Entidad/Organización -> metadatos_entidad_productora
        if 'organizacion' in filtros:
            filtro_partes.append(f"search.ismatch('{filtros['organizacion']}', 'metadatos_entidad_productora')")
        
        # Fecha -> metadatos_fecha_creacion
        if 'fecha_inicio' in filtros:
            filtro_partes.append(f"metadatos_fecha_creacion ge '{filtros['fecha_inicio']}'")
        if 'fecha_fin' in filtros:
            filtro_partes.append(f"metadatos_fecha_creacion le '{filtros['fecha_fin']}'")
        
        # Lugares y fechas de hechos (campos específicos que existen)
        if 'lugares_hechos' in filtros:
            # Usar search.ismatch para campos que pueden estar vacíos
            filtro_partes.append(f"search.ismatch('{filtros['lugares_hechos']}', 'lugares_hechos')")
        
        if 'fechas_hechos' in filtros:
            # Para fechas de hechos, puede ser búsqueda de texto o comparación
            filtro_partes.append(f"search.ismatch('{filtros['fechas_hechos']}', 'fechas_hechos')")
        
        # Búsqueda en análisis y contenido (campos principales poblados)
        if 'contenido_general' in filtros:
            filtro_partes.append(f"search.ismatch('{filtros['contenido_general']}', 'analisis,texto_extraido')")
        
        return ' and '.join(filtro_partes) if filtro_partes else ""
    
    def detectar_filtro_especifico_bd(self, consulta: str, filtros: Dict[str, Any]) -> bool:
        """Detecta si una consulta debe ir directo a BD por tipo de filtro"""
        consulta_lower = consulta.lower()
        
        # Casos que requieren BD directa por precisión de filtros
        casos_bd_directa = [
            # Filtro por tipo documento específico + consulta de víctimas
            ('tipo_documento' in filtros and 
             any(palabra in consulta_lower for palabra in ['víctima', 'victima', 'personas', 'afectado'])),
            
            # Filtro por NUC específico + conteos
            ('nucs' in filtros and len(filtros['nucs']) <= 3 and
             any(palabra in consulta_lower for palabra in ['cuántas', 'cuantas', 'cuántos', 'cuantos', 'total'])),
            
            # Filtro por despacho + estadísticas
            ('despacho' in filtros and
             any(palabra in consulta_lower for palabra in ['estadística', 'estadistica', 'resumen', 'conteo'])),
            
            # Filtros geográficos + consultas de víctimas (NUEVO)
            (('departamento' in filtros or 'municipio' in filtros) and
             any(palabra in consulta_lower for palabra in ['víctima', 'victima', 'lista', 'listado', 'personas', 'total'])),
            
            # Cualquier consulta directa de víctimas con filtros aplicados (NUEVO)
            (any(palabra in consulta_lower for palabra in ['lista total', 'listado', 'víctimas', 'victimas']) and
             any(filtros.values()))
        ]
        
        return any(casos_bd_directa)
    
    def generar_resumen_filtros(self, filtros: Dict[str, Any]) -> str:
        """Genera texto descriptivo de filtros aplicados"""
        if not filtros:
            return "Sin filtros aplicados"
        
        partes = []
        
        if 'nucs' in filtros:
            if len(filtros['nucs']) <= 3:
                partes.append(f"NUCs: {', '.join(filtros['nucs'])}")
            else:
                partes.append(f"NUCs: {len(filtros['nucs'])} seleccionados")
        
        if 'fecha_inicio' in filtros or 'fecha_fin' in filtros:
            inicio = filtros.get('fecha_inicio', 'Inicio')
            fin = filtros.get('fecha_fin', 'Presente')
            partes.append(f"Período: {inicio} - {fin}")
        
        if 'departamento' in filtros:
            partes.append(f"Departamento: {filtros['departamento']}")
        
        if 'municipio' in filtros:
            partes.append(f"Municipio: {filtros['municipio']}")
        
        if 'tipo_documento' in filtros:
            partes.append(f"Tipo: {filtros['tipo_documento']}")
        
        if 'despacho' in filtros:
            partes.append(f"Despacho: {filtros['despacho']}")
        
        return " | ".join(partes)

# Instancia global para uso en interfaz
filtro_universal = FiltroUniversal()
