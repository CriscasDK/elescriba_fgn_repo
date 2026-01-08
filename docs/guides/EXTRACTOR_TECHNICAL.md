# 🔧 Documentación Técnica - ExtractorMetadatosOptimizado

## 📋 Guía de Implementación para Desarrolladores

### Instalación y Configuración

#### 1. Dependencias
```bash
pip install psycopg2-binary python-dotenv
```

#### 2. Variables de Entorno
```bash
# Archivo .env o config/.env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=documentos_juridicos_gpt4
POSTGRES_USER=docs_user
POSTGRES_PASSWORD=docs_password_2025
```

#### 3. Importación
```python
from extractor_metadatos_optimizado import ExtractorMetadatosOptimizado, MetadatosOptimizados
```

---

## 🏗️ API Reference

### Clase ExtractorMetadatosOptimizado

#### Constructor
```python
def __init__(self):
    """
    Inicializa el extractor con conexión a BD y cache vacío
    
    Atributos:
        db_conn: Conexión a PostgreSQL
        _cache_metadatos: Dict para cache de resultados
        _estadisticas: Dict con métricas de rendimiento
    """
```

#### Métodos Principales

##### extraer_metadatos()
```python
def extraer_metadatos(
    self, 
    identificador: str, 
    tipo_busqueda: str = 'archivo'
) -> Optional[MetadatosOptimizados]:
    """
    Extrae metadatos optimizados para un documento
    
    Args:
        identificador: Nombre del archivo o NUC a buscar
        tipo_busqueda: 'archivo' o 'nuc'
    
    Returns:
        MetadatosOptimizados: Objeto con 26 campos poblados
        None: Si no se encuentra el documento
    
    Raises:
        Exception: Error de conexión o consulta SQL
    """
```

##### extraer_para_rag()
```python
def extraer_para_rag(self, identificador: str) -> Dict[str, Any]:
    """
    Extrae metadatos en formato compatible con RAG
    
    Args:
        identificador: Nombre del archivo a buscar
    
    Returns:
        Dict con campos esenciales para RAG:
        - nuc, cuaderno, despacho, serie, detalle
        - codigo, folios, fechas
        - metadatos_enriquecidos: True
    """
```

##### obtener_estadisticas()
```python
def obtener_estadisticas(self) -> Dict[str, Any]:
    """
    Obtiene métricas de rendimiento del extractor
    
    Returns:
        Dict con:
        - consultas_bd: Número de consultas a BD
        - consultas_cache: Número de hits de cache
        - total_extracciones: Total de extracciones realizadas
        - promedio_campos_poblados: Promedio de campos con datos
        - cache_hit_rate: Porcentaje de hits de cache
    """
```

##### cerrar_conexion()
```python
def cerrar_conexion(self):
    """
    Cierra la conexión a PostgreSQL
    Recomendado llamar al final del uso
    """
```

---

## 📊 Estructura de Datos

### MetadatosOptimizados

```python
@dataclass
class MetadatosOptimizados:
    # Identificación (8 campos)
    id: Optional[int] = None                    # PK tabla metadatos
    documento_id: Optional[int] = None          # FK tabla documentos
    nuc: Optional[str] = None                   # Número Único de Caso
    cuaderno: Optional[str] = None              # Ej: "Cuaderno 1"
    codigo: Optional[str] = None                # Ej: "20150"
    despacho: Optional[str] = None              # Ej: "59"
    detalle: Optional[str] = None               # Descripción del documento
    serie: Optional[str] = None                 # Ej: "052"
    
    # Estructura (3 campos)
    folio_inicial: Optional[int] = None         # Folio de inicio
    folio_final: Optional[int] = None           # Folio final
    paginas_total: Optional[int] = None         # Total de páginas
    
    # Archivo (3 campos)
    archivo: Optional[str] = None               # Nombre del archivo PDF
    ruta_documento: Optional[str] = None        # Ruta en filesystem
    hash_sha256: Optional[str] = None           # Hash del archivo
    
    # Técnico (1 campo)
    tamano_mb: Optional[float] = None           # Tamaño en MB
    
    # Fechas (4 campos)
    fecha_procesado: Optional[str] = None       # Fecha de procesamiento
    created_at: Optional[str] = None            # Fecha de creación en BD
    metadatos_timestamp: Optional[str] = None   # Timestamp de metadatos
    fecha_creacion: Optional[str] = None        # Fecha original (condicional)
    
    # Procesamiento (6 campos)
    estado_procesamiento: Optional[str] = None     # Estado actual
    version_sistema: Optional[str] = None          # Versión del sistema
    usuario_procesamiento: Optional[str] = None    # Usuario que procesó
    equipo_procesamiento: Optional[str] = None     # Equipo de procesamiento
    es_procesamiento_batch: Optional[bool] = None  # Si fue batch
    costo_procesamiento: Optional[float] = None    # Costo en USD
    
    # Autenticación (1 campo)
    authentication_info: Optional[Dict] = None  # Info de autenticación JSON
```

---

## 🔍 Ejemplos de Uso

### Uso Básico
```python
# Crear instancia
extractor = ExtractorMetadatosOptimizado()

# Extraer metadatos
archivo = "2015005204_24D_0017C1.pdf"
metadatos = extractor.extraer_metadatos(archivo)

if metadatos:
    print(f"NUC: {metadatos.nuc}")
    print(f"Cuaderno: {metadatos.cuaderno}")
    print(f"Fecha creación: {metadatos.fecha_creacion}")
else:
    print("Documento no encontrado")

# Cerrar conexión
extractor.cerrar_conexion()
```

### Uso con Context Manager
```python
class ExtractorContextManager:
    def __init__(self):
        self.extractor = None
    
    def __enter__(self):
        self.extractor = ExtractorMetadatosOptimizado()
        return self.extractor
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.extractor:
            self.extractor.cerrar_conexion()

# Uso recomendado
with ExtractorContextManager() as extractor:
    metadatos = extractor.extraer_metadatos("archivo.pdf")
    # Conexión se cierra automáticamente
```

### Búsqueda por NUC
```python
extractor = ExtractorMetadatosOptimizado()

# Buscar por NUC (usa LIKE con %)
nuc_parcial = "11001606606420030010017"
metadatos = extractor.extraer_metadatos(nuc_parcial, tipo_busqueda='nuc')

if metadatos:
    print(f"Archivo encontrado: {metadatos.archivo}")
```

### Integración con RAG
```python
def enriquecer_resultados_rag(documentos_encontrados):
    """Enriquece resultados de RAG con metadatos"""
    extractor = ExtractorMetadatosOptimizado()
    
    for documento in documentos_encontrados:
        metadatos_rag = extractor.extraer_para_rag(documento['nombre_archivo'])
        documento.update(metadatos_rag)
    
    extractor.cerrar_conexion()
    return documentos_encontrados
```

---

## ⚡ Optimizaciones de Rendimiento

### Sistema de Cache
```python
# El cache se maneja automáticamente
cache_key = f"optimizado_{tipo_busqueda}_{identificador}"

# Para limpiar cache manualmente (si necesario)
extractor._cache_metadatos.clear()
```

### Conexiones de BD
```python
# Reutilizar conexión para múltiples consultas
extractor = ExtractorMetadatosOptimizado()

for archivo in lista_archivos:
    metadatos = extractor.extraer_metadatos(archivo)
    # Procesar metadatos...

# Cerrar al final
extractor.cerrar_conexion()
```

### Consultas Batch (Recomendación)
```python
def procesar_lote_documentos(archivos):
    """Procesa múltiples documentos eficientemente"""
    extractor = ExtractorMetadatosOptimizado()
    resultados = []
    
    for archivo in archivos:
        try:
            metadatos = extractor.extraer_metadatos(archivo)
            if metadatos:
                resultados.append({
                    'archivo': archivo,
                    'metadatos': metadatos,
                    'exito': True
                })
            else:
                resultados.append({
                    'archivo': archivo,
                    'error': 'No encontrado',
                    'exito': False
                })
        except Exception as e:
            resultados.append({
                'archivo': archivo,
                'error': str(e),
                'exito': False
            })
    
    # Estadísticas finales
    stats = extractor.obtener_estadisticas()
    extractor.cerrar_conexion()
    
    return resultados, stats
```

---

## 🐛 Manejo de Errores

### Errores Comunes
```python
try:
    metadatos = extractor.extraer_metadatos("archivo.pdf")
except psycopg2.OperationalError as e:
    # Error de conexión a BD
    print(f"Error de conexión: {e}")
except psycopg2.ProgrammingError as e:
    # Error en consulta SQL
    print(f"Error SQL: {e}")
except Exception as e:
    # Otros errores
    print(f"Error inesperado: {e}")
```

### Validación de Datos
```python
def validar_metadatos(metadatos: MetadatosOptimizados) -> bool:
    """Valida que los metadatos básicos estén presentes"""
    if not metadatos:
        return False
    
    # Campos obligatorios
    campos_obligatorios = ['id', 'documento_id', 'nuc', 'archivo']
    
    for campo in campos_obligatorios:
        if not getattr(metadatos, campo):
            return False
    
    return True
```

---

## 📊 Monitoreo y Métricas

### Logging Personalizado
```python
import logging

# Configurar logging específico
logger = logging.getLogger('extractor_metadatos')
handler = logging.FileHandler('extractor.log')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
```

### Métricas de Rendimiento
```python
def obtener_metricas_detalladas(extractor):
    """Obtiene métricas detalladas del extractor"""
    stats = extractor.obtener_estadisticas()
    
    return {
        'eficiencia_cache': stats['cache_hit_rate'] * 100,
        'consultas_totales': stats['consultas_bd'] + stats['consultas_cache'],
        'promedio_campos': stats['promedio_campos_poblados'],
        'rendimiento': 'Excelente' if stats['cache_hit_rate'] > 0.7 else 'Bueno' if stats['cache_hit_rate'] > 0.5 else 'Mejorable'
    }
```

---

## 🧪 Testing

### Test Unitario Básico
```python
import unittest

class TestExtractorOptimizado(unittest.TestCase):
    
    def setUp(self):
        self.extractor = ExtractorMetadatosOptimizado()
    
    def tearDown(self):
        self.extractor.cerrar_conexion()
    
    def test_extraccion_archivo_existente(self):
        """Prueba extracción de archivo conocido"""
        metadatos = self.extractor.extraer_metadatos("2015005204_24D_0017C1.pdf")
        
        self.assertIsNotNone(metadatos)
        self.assertIsNotNone(metadatos.nuc)
        self.assertEqual(metadatos.nuc, "11001606606420030010017")
    
    def test_extraccion_archivo_inexistente(self):
        """Prueba con archivo que no existe"""
        metadatos = self.extractor.extraer_metadatos("archivo_inexistente.pdf")
        
        self.assertIsNone(metadatos)
    
    def test_formato_rag(self):
        """Prueba formato para RAG"""
        metadatos_rag = self.extractor.extraer_para_rag("2015005204_24D_0017C1.pdf")
        
        self.assertIn('nuc', metadatos_rag)
        self.assertIn('metadatos_enriquecidos', metadatos_rag)
        self.assertTrue(metadatos_rag['metadatos_enriquecidos'])

if __name__ == '__main__':
    unittest.main()
```

### Test de Rendimiento
```python
import time
from typing import List

def test_rendimiento_lote(archivos: List[str]) -> Dict:
    """Prueba rendimiento con lote de archivos"""
    extractor = ExtractorMetadatosOptimizado()
    
    inicio = time.time()
    resultados_exitosos = 0
    
    for archivo in archivos:
        metadatos = extractor.extraer_metadatos(archivo)
        if metadatos:
            resultados_exitosos += 1
    
    fin = time.time()
    stats = extractor.obtener_estadisticas()
    extractor.cerrar_conexion()
    
    return {
        'tiempo_total': fin - inicio,
        'archivos_procesados': len(archivos),
        'exitosos': resultados_exitosos,
        'tiempo_promedio': (fin - inicio) / len(archivos),
        'cache_hit_rate': stats['cache_hit_rate']
    }
```

---

## 🔧 Migración desde Sistema Anterior

### Mapeo de Campos
```python
# Equivalencias entre versiones
MAPEO_CAMPOS = {
    # Anterior -> Optimizado
    'detalle_documento': 'detalle',
    'nuc_completo': 'nuc',
    'total_paginas': 'paginas_total',
    'tamaño_archivo': 'tamano_mb',
    # Campos eliminados (siempre None)
    'soporte': None,
    'idioma': None,
    'descriptores': None,
    # ... otros campos eliminados
}
```

### Script de Migración
```python
def migrar_desde_extractor_anterior(archivo):
    """Migra llamadas del extractor anterior al optimizado"""
    
    # Anterior (ExtractorUnificado)
    # metadatos_antiguos = extractor_antiguo.extraer_metadatos_completos(archivo)
    
    # Nuevo (ExtractorOptimizado)
    extractor_nuevo = ExtractorMetadatosOptimizado()
    metadatos_nuevos = extractor_nuevo.extraer_metadatos(archivo)
    
    # Convertir a formato anterior si necesario
    if metadatos_nuevos:
        return {
            'nuc': metadatos_nuevos.nuc,
            'detalle_documento': metadatos_nuevos.detalle,  # Mapeo
            'total_paginas': metadatos_nuevos.paginas_total,  # Mapeo
            # ... otros campos según necesidad
        }
    
    return None
```

---

*Documentación Técnica - ExtractorMetadatosOptimizado v2.0*  
*Generada el 19 de Agosto, 2025*
