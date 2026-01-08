#!/usr/bin/env python3
"""
Enriquecedor de Metadatos en Tiempo Real
Sistema para complementar resultados de Azure Search con datos de PostgreSQL
Fecha: Agosto 19, 2025
Estado: DESARROLLO - Enriquecimiento Inteligente
"""

import psycopg2
import psycopg2.extras
import re
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MetadatosEnriquecidos:
    """Estructura para metadatos enriquecidos"""
    nuc: str
    nuc_completo: str
    cuaderno: str
    despacho: str
    entidad_productora: str
    serie: str
    subserie: str
    detalle: str
    folio_inicial: Optional[int]
    folio_final: Optional[int]
    fecha_creacion: Optional[str]
    observaciones: Optional[str]
    # Campos adicionales para entidades
    personas_relacionadas: List[str]
    lugares_relacionados: List[str]
    fechas_relevantes: List[str]
    organizaciones_relacionadas: List[str]

class EnriquecedorMetadatos:
    """Clase para enriquecer resultados de Azure Search con datos de PostgreSQL"""
    
    def __init__(self):
        self.db_conn = None
        self._inicializar_conexion()
        self._cache_metadatos = {}  # Cache para evitar consultas repetidas
    
    def _inicializar_conexion(self):
        """Inicializar conexión a PostgreSQL"""
        try:
            self.db_conn = psycopg2.connect(
                host='localhost',
                port='5432',
                user='docs_user',
                password='docs_password_2025',
                database='documentos_juridicos_gpt4'
            )
            logger.info("✅ Conexión a PostgreSQL establecida")
        except Exception as e:
            logger.error(f"❌ Error conectando a PostgreSQL: {e}")
            self.db_conn = None
    
    def extraer_nuc_base_de_archivo(self, nombre_archivo: str) -> Optional[str]:
        """Extraer NUC base del nombre de archivo"""
        # Patrones para diferentes formatos de archivo
        patrones = [
            r'^(\d+)',  # Números al inicio
            r'doc_(\d+)',  # doc_números
            r'RAD_(\d+)',  # RAD_números
        ]
        
        for patron in patrones:
            match = re.search(patron, nombre_archivo)
            if match:
                return match.group(1)
        
        return None
    
    def buscar_metadatos_por_archivo(self, nombre_archivo: str) -> Optional[MetadatosEnriquecidos]:
        """Buscar metadatos por nombre de archivo exacto"""
        if not self.db_conn:
            return None
        
        # Buscar en cache primero
        if nombre_archivo in self._cache_metadatos:
            return self._cache_metadatos[nombre_archivo]
        
        try:
            cursor = self.db_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # Limpiar nombre de archivo (quitar .json si existe)
            archivo_limpio = nombre_archivo.replace('.json', '').replace('_batch_resultado', '')
            
            # Buscar por nombre de archivo (múltiples variantes)
            consulta = """
                SELECT m.*, d.archivo as archivo_documento
                FROM metadatos m
                LEFT JOIN documentos d ON m.documento_id = d.id
                WHERE m.archivo ILIKE %s 
                   OR m.archivo ILIKE %s
                   OR d.archivo ILIKE %s
                LIMIT 1;
            """
            
            patrones = [
                f"%{archivo_limpio}%",
                f"%{nombre_archivo}%",
                f"%{archivo_limpio.split('_')[0]}%"  # Solo la parte del NUC
            ]
            
            cursor.execute(consulta, patrones)
            resultado = cursor.fetchone()
            
            if resultado:
                metadatos = self._crear_metadatos_enriquecidos(resultado)
                self._cache_metadatos[nombre_archivo] = metadatos
                return metadatos
            
        except Exception as e:
            logger.error(f"❌ Error buscando metadatos para {nombre_archivo}: {e}")
        
        return None
    
    def buscar_metadatos_por_nuc_base(self, nuc_base: str) -> Optional[MetadatosEnriquecidos]:
        """Buscar metadatos por NUC base (primera parte del NUC)"""
        if not self.db_conn or not nuc_base:
            return None
        
        try:
            cursor = self.db_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # Buscar por NUC que contenga la base
            consulta = """
                SELECT m.*, d.archivo as archivo_documento
                FROM metadatos m
                LEFT JOIN documentos d ON m.documento_id = d.id
                WHERE m.nuc LIKE %s
                LIMIT 1;
            """
            
            cursor.execute(consulta, (f"%{nuc_base}%",))
            resultado = cursor.fetchone()
            
            if resultado:
                return self._crear_metadatos_enriquecidos(resultado)
            
        except Exception as e:
            logger.error(f"❌ Error buscando metadatos por NUC {nuc_base}: {e}")
        
        return None
    
    def _crear_metadatos_enriquecidos_completos(self, datos_bd):
        """
        Crea un diccionario completo con TODOS los metadatos disponibles (52 campos)
        Trabaja directamente con los datos de BD sin limitaciones de dataclass
        """
        metadatos_completos = {
            # Campos básicos de identificación
            'id': datos_bd.get('id'),
            'documento_id': datos_bd.get('documento_id'),
            'nuc': datos_bd.get('nuc', '') or 'No disponible',
            'nuc_completo': datos_bd.get('nuc', '') or 'No disponible',
            'cuaderno': datos_bd.get('cuaderno', '') or 'No especificado',
            'codigo': datos_bd.get('codigo'),
            'despacho': datos_bd.get('despacho', '') or 'No especificado',
            'detalle_documento': datos_bd.get('detalle', '') or 'Sin detalle',
            
            # Campos de entidad y organización
            'entidad_productora': datos_bd.get('entidad_productora', '') or 'No especificada',
            'serie': datos_bd.get('serie', '') or 'No especificada',
            'subserie': datos_bd.get('subserie', '') or 'No especificada',
            'seccion': datos_bd.get('seccion'),
            'tipo_documental': datos_bd.get('tipo_documental'),
            
            # Folios y paginación
            'folio_inicial': datos_bd.get('folio_inicial'),
            'folio_final': datos_bd.get('folio_final'),
            'numero_folios': datos_bd.get('numero_folios'),
            'total_paginas': datos_bd.get('total_paginas'),
            
            # Fechas y temporales
            'fecha_creacion': str(datos_bd.get('fecha_creacion', '')) if datos_bd.get('fecha_creacion') else None,
            'fecha_creacion_documento': str(datos_bd.get('fecha_creacion', '')) if datos_bd.get('fecha_creacion') else None,
            'fecha_modificacion': datos_bd.get('fecha_modificacion'),
            'fecha_ultimo_acceso': datos_bd.get('fecha_ultimo_acceso'),
            'fecha_procesamiento': datos_bd.get('fecha_procesamiento'),
            'fecha_indexacion': datos_bd.get('fecha_indexacion'),
            
            # Información de autenticación y seguridad
            'hash_sha256': datos_bd.get('hash_sha256'),
            'firma_digital': datos_bd.get('firma_digital'),
            'authentication_info': datos_bd.get('authentication_info'),
            'checksum_validado': datos_bd.get('checksum_validado'),
            
            # Características técnicas del documento
            'soporte': datos_bd.get('soporte'),
            'idioma': datos_bd.get('idioma'),
            'tamaño_archivo': datos_bd.get('tamaño_archivo'),
            'formato_archivo': datos_bd.get('formato_archivo'),
            'calidad_digitalizacion': datos_bd.get('calidad_digitalizacion'),
            
            # Descriptores y clasificación
            'descriptores': datos_bd.get('descriptores'),
            'palabras_clave': datos_bd.get('palabras_clave'),
            'materias': datos_bd.get('materias'),
            'topicos_juridicos': datos_bd.get('topicos_juridicos'),
            'clasificacion_documental': datos_bd.get('clasificacion_documental'),
            
            # Observaciones y notas
            'observaciones': datos_bd.get('observaciones', ''),
            'notas_adicionales': datos_bd.get('notas_adicionales'),
            'comentarios_procesamiento': datos_bd.get('comentarios_procesamiento'),
            
            # Información de procesamiento y sistema
            'version_sistema': datos_bd.get('version_sistema'),
            'usuario_procesamiento': datos_bd.get('usuario_procesamiento'),
            'estado_procesamiento': datos_bd.get('estado_procesamiento'),
            'errores_procesamiento': datos_bd.get('errores_procesamiento'),
            'metadatos_extraidos': datos_bd.get('metadatos_extraidos'),
            
            # Ubicación y almacenamiento
            'ubicacion_fisica': datos_bd.get('ubicacion_fisica'),
            'ruta_archivo_original': datos_bd.get('ruta_archivo_original'),
            'servidor_almacenamiento': datos_bd.get('servidor_almacenamiento'),
            
            # Control de calidad y validación
            'validacion_completada': datos_bd.get('validacion_completada'),
            'errores_validacion': datos_bd.get('errores_validacion'),
            'calidad_contenido': datos_bd.get('calidad_contenido'),
            
            # Metadatos de enriquecimiento
            'metadatos_enriquecidos': True,
            'timestamp_enriquecimiento': datetime.now().isoformat(),
            'campos_totales_disponibles': 52,
            'fuente_enriquecimiento': 'PostgreSQL-completo'
        }
        
        # Filtrar valores None para no sobrecargar el resultado
        return {k: v for k, v in metadatos_completos.items() if v is not None}

    def buscar_metadatos_raw_por_archivo(self, nombre_archivo: str) -> Optional[Dict]:
        """Buscar metadatos por nombre de archivo exacto - devuelve datos raw de BD"""
        if not self.db_conn:
            return None
        
        try:
            cursor = self.db_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # Limpiar nombre de archivo (quitar .json si existe)
            archivo_limpio = nombre_archivo.replace('.json', '').replace('_batch_resultado', '')
            
            # Buscar por nombre de archivo (múltiples variantes)
            consulta = """
                SELECT m.*, d.archivo as archivo_documento
                FROM metadatos m
                LEFT JOIN documentos d ON m.documento_id = d.id
                WHERE m.archivo ILIKE %s 
                   OR m.archivo ILIKE %s
                   OR d.archivo ILIKE %s
                LIMIT 1;
            """
            
            patrones = [
                f"%{archivo_limpio}%",
                f"%{nombre_archivo}%",
                f"%{archivo_limpio.split('_')[0]}%"  # Solo la parte del NUC
            ]
            
            cursor.execute(consulta, patrones)
            resultado = cursor.fetchone()
            
            if resultado:
                return dict(resultado)  # Convertir a diccionario regular
            
        except Exception as e:
            logger.error(f"❌ Error buscando metadatos por archivo {nombre_archivo}: {e}")
        
        return None

    def buscar_metadatos_raw_por_nuc_base(self, nuc_base: str) -> Optional[Dict]:
        """Buscar metadatos por NUC base - devuelve datos raw de BD"""
        if not self.db_conn or not nuc_base:
            return None
        
        try:
            cursor = self.db_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # Buscar por NUC que empiece con el nuc_base
            consulta = """
                SELECT * FROM metadatos 
                WHERE nuc LIKE %s
                LIMIT 1;
            """
            
            cursor.execute(consulta, (f"{nuc_base}%",))
            resultado = cursor.fetchone()
            
            if resultado:
                return dict(resultado)  # Convertir a diccionario regular
                
        except Exception as e:
            logger.error(f"❌ Error buscando metadatos por NUC {nuc_base}: {e}")
        
        return None

    def _crear_metadatos_enriquecidos(self, datos_bd):
        """Crear objeto MetadatosEnriquecidos desde datos de BD"""
        return MetadatosEnriquecidos(
            nuc=datos_bd.get('nuc', '') or 'No disponible',
            nuc_completo=datos_bd.get('nuc', '') or 'No disponible',
            cuaderno=datos_bd.get('cuaderno', '') or 'No especificado',
            despacho=datos_bd.get('despacho', '') or 'No especificado',
            entidad_productora=datos_bd.get('entidad_productora', '') or 'No especificada',
            serie=datos_bd.get('serie', '') or 'No especificada',
            subserie=datos_bd.get('subserie', '') or 'No especificada',
            detalle=datos_bd.get('detalle', '') or 'Sin detalle',
            folio_inicial=datos_bd.get('folio_inicial'),
            folio_final=datos_bd.get('folio_final'),
            fecha_creacion=str(datos_bd.get('fecha_creacion', '')) if datos_bd.get('fecha_creacion') else None,
            observaciones=datos_bd.get('observaciones', ''),
            # TODO: Implementar búsqueda de entidades relacionadas
            personas_relacionadas=[],
            lugares_relacionados=[],
            fechas_relevantes=[],
            organizaciones_relacionadas=[]
        )
    
    def enriquecer_resultado_azure_search(self, resultado_azure: Dict) -> Dict:
        """Enriquecer un resultado individual de Azure Search"""
        try:
            # Obtener información básica del resultado
            documento = resultado_azure.get('documento', '')
            chunk_id = resultado_azure.get('chunk_id', '')
            
            logger.info(f"🔍 Enriqueciendo: {documento}")
            
            # Estrategia 1: Buscar por nombre de archivo exacto
            metadatos = self.buscar_metadatos_raw_por_archivo(documento)
            
            # Estrategia 2: Si no encuentra, buscar por NUC base
            if not metadatos:
                nuc_base = self.extraer_nuc_base_de_archivo(documento)
                if nuc_base:
                    metadatos = self.buscar_metadatos_raw_por_nuc_base(nuc_base)
            
            # Enriquecer el resultado
            if metadatos:
                resultado_enriquecido = resultado_azure.copy()
                resultado_enriquecido.update(self._crear_metadatos_enriquecidos_completos(metadatos))
                
                nuc_encontrado = metadatos.get('nuc', 'No disponible')
                logger.info(f"✅ Enriquecido con NUC: {nuc_encontrado}")
                return resultado_enriquecido
            else:
                # Si no se encuentran metadatos, al menos intentar extraer NUC base
                nuc_base = self.extraer_nuc_base_de_archivo(documento)
                resultado_azure['nuc'] = nuc_base or 'Sin NUC identificado'
                resultado_azure['metadatos_enriquecidos'] = False
                logger.warning(f"⚠️ No se encontraron metadatos para: {documento}")
                
        except Exception as e:
            logger.error(f"❌ Error enriqueciendo resultado: {e}")
            resultado_azure['nuc'] = 'Error en enriquecimiento'
            resultado_azure['metadatos_enriquecidos'] = False
        
        return resultado_azure
    
    def enriquecer_lista_resultados(self, resultados_azure: List[Dict]) -> List[Dict]:
        """Enriquecer una lista completa de resultados de Azure Search"""
        logger.info(f"🚀 Iniciando enriquecimiento de {len(resultados_azure)} resultados")
        
        resultados_enriquecidos = []
        contadores = {'enriquecidos': 0, 'fallidos': 0}
        
        for resultado in resultados_azure:
            resultado_enriquecido = self.enriquecer_resultado_azure_search(resultado)
            resultados_enriquecidos.append(resultado_enriquecido)
            
            if resultado_enriquecido.get('metadatos_enriquecidos', False):
                contadores['enriquecidos'] += 1
            else:
                contadores['fallidos'] += 1
        
        logger.info(f"📊 Enriquecimiento completado: {contadores['enriquecidos']} exitosos, {contadores['fallidos']} fallidos")
        return resultados_enriquecidos
    
    def obtener_estadisticas_enriquecimiento(self) -> Dict:
        """Obtener estadísticas del proceso de enriquecimiento"""
        return {
            'cache_size': len(self._cache_metadatos),
            'conexion_bd': self.db_conn is not None,
            'timestamp': datetime.now().isoformat()
        }
    
    def limpiar_cache(self):
        """Limpiar cache de metadatos"""
        self._cache_metadatos.clear()
        logger.info("🧹 Cache de metadatos limpiado")

# Instancia global del enriquecedor
enriquecedor_global = None

def get_enriquecedor() -> EnriquecedorMetadatos:
    """Obtener instancia global del enriquecedor (patrón singleton)"""
    global enriquecedor_global
    if enriquecedor_global is None:
        enriquecedor_global = EnriquecedorMetadatos()
    return enriquecedor_global

# Función de conveniencia para enriquecer resultados
def enriquecer_resultados_rag(resultados: List[Dict]) -> List[Dict]:
    """Función de conveniencia para enriquecer resultados RAG"""
    enriquecedor = get_enriquecedor()
    return enriquecedor.enriquecer_lista_resultados(resultados)

if __name__ == "__main__":
    # Test del enriquecedor
    print("🧪 PROBANDO ENRIQUECEDOR DE METADATOS")
    print("="*60)
    
    enriquecedor = EnriquecedorMetadatos()
    
    # Simular resultado de Azure Search
    resultado_test = {
        'chunk_id': 'doc_2015005204_24G_6175C5_batch_resultado_20250619_091941_chunk_8',
        'documento': '2015005204_24G_6175C5_batch_resultado_20250619_091941.json',
        'pagina': 1,
        'parrafo': 9,
        'score_relevancia': 0.85,
        'legal_significance': 0.52,
        'texto_chunk_preview': 'El documento refleja un seguimiento detallado...'
    }
    
    print("📄 Resultado original:")
    print(json.dumps(resultado_test, indent=2, ensure_ascii=False))
    
    print(f"\n🔍 Enriqueciendo...")
    resultado_enriquecido = enriquecedor.enriquecer_resultado_azure_search(resultado_test)
    
    print(f"\n✅ Resultado enriquecido:")
    print(json.dumps(resultado_enriquecido, indent=2, ensure_ascii=False, default=str))
