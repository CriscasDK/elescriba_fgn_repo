"""
Constantes del sistema - Sistema Híbrido v3.3

Este archivo centraliza todas las constantes hardcodeadas del sistema
para facilitar el mantenimiento y evitar duplicación.

Fecha: 29 de Septiembre, 2025
Versión: v3.3-sanitization
"""

# ============================================================================
# ENTIDADES GEOGRÁFICAS Y CONCEPTUALES
# ============================================================================

ENTIDADES_NO_PERSONAS = [
    # Departamentos de Colombia
    'antioquia', 'bogotá', 'valle del cauca', 'cundinamarca', 'atlántico',
    'santander', 'bolívar', 'nariño', 'tolima', 'huila', 'caldas', 'cauca',
    'córdoba', 'sucre', 'magdalena', 'cesar', 'arauca', 'amazonas', 'chocó',
    'guaviare', 'guainía', 'vichada', 'vaupés', 'putumayo', 'caquetá',
    'casanare', 'meta', 'norte de santander', 'boyacá', 'risaralda', 'quindío',
    'san andrés', 'providencia', 'santa catalina',

    # Ciudades principales
    'medellín', 'cali', 'barranquilla', 'cartagena', 'bucaramanga',
    'pereira', 'manizales', 'armenia', 'ibagué', 'pasto', 'popayán',
    'valledupar', 'montería', 'villavicencio', 'neiva', 'cúcuta',

    # Conceptos y entidades institucionales
    'fiscalía', 'fiscalia', 'despacho', 'juzgado', 'tribunal',
    'corte', 'colombia', 'nación', 'estado', 'gobierno',
    'ejército', 'ejercito', 'policía', 'policia', 'fuerza pública',

    # Organizaciones (no personas)
    'farc', 'eln', 'auc', 'bacrim', 'ong',

    # Otros términos comunes que no son personas
    'víctima', 'victima', 'víctimas', 'victimas',
    'responsable', 'responsables', 'caso', 'casos',
    'documento', 'documentos', 'expediente', 'expedientes'
]

# ============================================================================
# PALABRAS CLAVE PARA ANÁLISIS CUALITATIVO (RAG)
# ============================================================================

PALABRAS_ANALISIS = [
    # Análisis y patrones
    'patrón', 'patrones', 'análisis', 'analisis', 'observ', 'observar',
    'context', 'contexto', 'relación', 'relacion', 'comparar', 'evaluar',

    # Interpretación y síntesis
    'interpretar', 'interpretación', 'sintesis', 'síntesis',
    'conclusiones', 'hallazgos', 'tendencias',

    # Análisis temporal y evolutivo
    'evolución', 'evolucion', 'cambios', 'tendencia',
    'progresión', 'progresion', 'desarrollo',

    # Análisis cualitativo
    'características', 'caracteristicas', 'similitudes', 'diferencias',
    'común', 'comun', 'frecuente', 'recurrente',

    # Verbos de análisis
    'describe', 'describir', 'explica', 'explicar',
    'identifica', 'identificar', 'determina', 'determinar'
]

# ============================================================================
# VALIDACIÓN DE DATOS
# ============================================================================

# Longitudes válidas para NUC (Número Único de Caso)
LONGITUD_NUC_MIN = 21
LONGITUD_NUC_MAX = 23

# Campos obligatorios en resultados de consultas híbridas BD
CAMPOS_REQUERIDOS_BD_HIBRIDA = [
    'total_menciones',
    'documentos',
    'victimas',
    'fuentes'
]

# ============================================================================
# LÍMITES DE CONSULTAS
# ============================================================================

# Límites por defecto para paginación
LIMITE_VICTIMAS_DEFECTO = 100
LIMITE_FUENTES_DEFECTO = 100
LIMITE_DOCUMENTOS_DEFECTO = 100

# Límites máximos para prevenir sobrecarga
LIMITE_VICTIMAS_MAXIMO = 1000
LIMITE_FUENTES_MAXIMO = 500
LIMITE_DOCUMENTOS_MAXIMO = 500

# ============================================================================
# CONFIGURACIÓN DE NORMALIZACIÓN
# ============================================================================

# Mapeo de variaciones geográficas a formas canónicas
NORMALIZACION_DEPARTAMENTOS = {
    'antioquía': 'antioquia',
    'bogota': 'bogotá',
    'bogotá d.c.': 'bogotá',
    'distrito capital': 'bogotá',
    'valle': 'valle del cauca',
    'n. de santander': 'norte de santander',
    'norte santander': 'norte de santander',
    'san andres': 'san andrés',
    # Agregar más variaciones según sea necesario
}

# ============================================================================
# MENSAJES Y TEXTOS DEL SISTEMA
# ============================================================================

MENSAJE_SIN_RESULTADOS = "No se encontraron resultados para la consulta especificada."
MENSAJE_ERROR_CONEXION_BD = "Error de conexión a la base de datos. Por favor, intente nuevamente."
MENSAJE_ERROR_AZURE_API = "Error al conectar con Azure OpenAI. Verifique la configuración."

# ============================================================================
# CONFIGURACIÓN DE PERFORMANCE
# ============================================================================

# Timeouts en segundos
TIMEOUT_CONSULTA_BD = 30
TIMEOUT_CONSULTA_RAG = 60
TIMEOUT_CONSULTA_HIBRIDA = 90

# Tamaños de página para scroll
TAMANO_PAGINA_SCROLL = 1000