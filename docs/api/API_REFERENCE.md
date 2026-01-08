# 🚀 API Reference - Sistema de Documentos Jurídicos

## 📋 Índice

1. [Introducción](#introducción)
2. [Autenticación](#autenticación)
3. [Endpoints Principales](#endpoints-principales)
4. [Modelos de Datos](#modelos-de-datos)
5. [Códigos de Respuesta](#códigos-de-respuesta)
6. [Ejemplos de Uso](#ejemplos-de-uso)
7. [SDK y Librerías](#sdk-y-librerías)

## 🌟 Introducción

La API REST del Sistema de Documentos Jurídicos proporciona acceso programático a la base de datos de documentos jurídicos, permitiendo consultas especializadas, búsquedas avanzadas y análisis de entidades.

### Base URL
```
https://api.documentos-juridicos.fiscalia.gov.co/v1
```

### Características
- ✅ **RESTful**: Sigue principios REST estándar
- ✅ **JSON**: Todas las respuestas en formato JSON
- ✅ **Paginación**: Soporte para grandes conjuntos de datos
- ✅ **Filtrado**: Múltiples opciones de filtrado y búsqueda
- ✅ **Versioning**: Versionado de API para compatibilidad
- ✅ **Rate Limiting**: Límites de velocidad para protección
- ✅ **CORS**: Soporte para aplicaciones web cross-origin

## 🔐 Autenticación

### API Key Authentication

```http
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json
```

### Ejemplo con curl
```bash
curl -H "Authorization: Bearer sk-proj-abc123..." \
     -H "Content-Type: application/json" \
     https://api.documentos-juridicos.fiscalia.gov.co/v1/documentos
```

### Obtener API Key
```python
import requests

response = requests.post(
    'https://api.documentos-juridicos.fiscalia.gov.co/auth/token',
    json={
        'username': 'your_username',
        'password': 'your_password'
    }
)

token = response.json()['access_token']
```

## 🎯 Endpoints Principales

### 📄 Documentos

#### Listar Documentos
```http
GET /v1/documentos
```

**Parámetros de Query:**
- `page` (int): Número de página (default: 1)
- `limit` (int): Elementos por página (default: 50, max: 500)
- `nuc` (string): Filtrar por NUC específico
- `despacho` (string): Filtrar por despacho
- `fecha_desde` (string): Fecha desde (ISO 8601)
- `fecha_hasta` (string): Fecha hasta (ISO 8601)
- `buscar` (string): Búsqueda en texto completo

**Ejemplo:**
```bash
curl -H "Authorization: Bearer $API_KEY" \
     "https://api.documentos-juridicos.fiscalia.gov.co/v1/documentos?limit=100&despacho=URI&buscar=víctima"
```

**Respuesta:**
```json
{
    "data": [
        {
            "id": 12345,
            "archivo": "documento_ejemplo.pdf",
            "nuc": "2015005204",
            "despacho": "URI",
            "cuaderno": "C1",
            "fecha_procesado": "2024-08-20T10:30:00Z",
            "extracto": "Fragmento del texto del documento...",
            "metadatos": {
                "paginas": 15,
                "tamano_mb": 2.4,
                "serie": "Investigaciones",
                "subserie": "Testimonios"
            }
        }
    ],
    "pagination": {
        "page": 1,
        "limit": 100,
        "total": 11111,
        "pages": 112
    },
    "meta": {
        "tiempo_respuesta_ms": 145,
        "filtros_aplicados": ["despacho", "buscar"]
    }
}
```

#### Obtener Documento Específico
```http
GET /v1/documentos/{id}
```

**Respuesta:**
```json
{
    "id": 12345,
    "archivo": "documento_ejemplo.pdf",
    "texto_completo": "Texto completo del documento...",
    "analisis": "Análisis automático del documento...",
    "nuc": "2015005204",
    "despacho": "URI",
    "cuaderno": "C1",
    "fecha_procesado": "2024-08-20T10:30:00Z",
    "metadatos": {
        "paginas": 15,
        "tamano_mb": 2.4,
        "serie": "Investigaciones",
        "subserie": "Testimonios",
        "authentication_info": {
            "firma_digital": true,
            "certificado_valido": true
        }
    },
    "entidades": {
        "personas": 12,
        "organizaciones": 3,
        "lugares": 8
    }
}
```

#### Buscar en Documentos
```http
POST /v1/documentos/buscar
```

**Body:**
```json
{
    "query": "víctimas desaparición forzada",
    "filtros": {
        "nuc": ["2015005204", "2016003401"],
        "despacho": ["URI", "CTI"],
        "fecha_desde": "2015-01-01",
        "fecha_hasta": "2024-12-31"
    },
    "opciones": {
        "busqueda_fuzzy": true,
        "incluir_sinonimos": true,
        "resaltar_resultados": true
    },
    "paginacion": {
        "page": 1,
        "limit": 50
    }
}
```

### 👥 Personas

#### Listar Personas
```http
GET /v1/personas
```

**Parámetros:**
- `tipo` (string): victima, responsable, testigo, defensa
- `nombre` (string): Búsqueda por nombre
- `documento_id` (int): Filtrar por documento específico

**Ejemplo:**
```bash
curl -H "Authorization: Bearer $API_KEY" \
     "https://api.documentos-juridicos.fiscalia.gov.co/v1/personas?tipo=victima&limit=100"
```

**Respuesta:**
```json
{
    "data": [
        {
            "id": 5678,
            "nombre": "María González López",
            "tipo": "victima",
            "documento_id": 12345,
            "observaciones": "Víctima de desaparición forzada",
            "fecha_registro": "2024-08-20T10:30:00Z",
            "metadatos": {
                "categoria_automatica": "civil",
                "confianza_clasificacion": 0.95,
                "menciones_documento": 8
            }
        }
    ],
    "pagination": {
        "page": 1,
        "limit": 100,
        "total": 2561,
        "pages": 26
    }
}
```

#### Buscar Personas con IA
```http
POST /v1/personas/buscar-inteligente
```

**Body:**
```json
{
    "query": "María González",
    "opciones": {
        "busqueda_fuzzy": true,
        "similitud_minima": 0.7,
        "incluir_variaciones": true,
        "expandir_nombres": true
    }
}
```

**Respuesta:**
```json
{
    "resultados": [
        {
            "persona": {
                "id": 5678,
                "nombre": "María González López",
                "tipo": "victima"
            },
            "similitud": 0.95,
            "variaciones_encontradas": [
                "Maria González",
                "M. González López",
                "María G. López"
            ],
            "documentos_relacionados": 3
        }
    ],
    "metadatos_busqueda": {
        "algoritmo": "fuzzy_matching_plus_nlp",
        "tiempo_procesamiento_ms": 234,
        "resultados_totales": 15
    }
}
```

### 🏢 Organizaciones

#### Listar Organizaciones
```http
GET /v1/organizaciones
```

#### Análisis de Organizaciones
```http
GET /v1/organizaciones/analisis
```

**Respuesta:**
```json
{
    "estadisticas": {
        "total_organizaciones": 156,
        "tipos": {
            "militar": 45,
            "policial": 23,
            "paramilitar": 78,
            "judicial": 10
        }
    },
    "organizaciones_frecuentes": [
        {
            "nombre": "Ejército Nacional",
            "menciones": 234,
            "documentos": 89,
            "clasificacion": "militar"
        }
    ],
    "redes_organizacionales": {
        "nodos": 156,
        "conexiones": 289,
        "clusters_principales": 12
    }
}
```

### 📊 Consultas Especializadas

#### Consultas Predefinidas
```http
GET /v1/consultas/{tipo}
```

**Tipos disponibles:**
- `victimas-por-despacho`
- `responsables-clasificados`
- `crimenes-lesa-humanidad`
- `desapariciones-forzadas`
- `ejecutores-materiales`
- `comandantes-responsables`

**Ejemplo:**
```bash
curl -H "Authorization: Bearer $API_KEY" \
     "https://api.documentos-juridicos.fiscalia.gov.co/v1/consultas/victimas-por-despacho"
```

#### Consulta Personalizada
```http
POST /v1/consultas/personalizada
```

**Body:**
```json
{
    "sql": "SELECT d.nuc, COUNT(p.id) as total_victimas FROM documentos d JOIN personas p ON d.id = p.documento_id WHERE p.tipo ILIKE '%victim%' GROUP BY d.nuc ORDER BY total_victimas DESC LIMIT 10",
    "parametros": {},
    "validar": true
}
```

### 📈 Estadísticas y Métricas

#### Estadísticas Generales
```http
GET /v1/estadisticas
```

**Respuesta:**
```json
{
    "documentos": {
        "total": 11111,
        "procesados_hoy": 45,
        "tamano_total_gb": 156.7
    },
    "personas": {
        "total": 2561,
        "victimas": 1876,
        "responsables": 456,
        "testigos": 229
    },
    "consultas": {
        "total_hoy": 1245,
        "tiempo_promedio_ms": 145,
        "consultas_por_hora": 52
    },
    "cobertura": {
        "nucs_unicos": 45,
        "despachos": 12,
        "anos_cubiertos": "2015-2024"
    }
}
```

#### Métricas de Performance
```http
GET /v1/metricas/performance
```

#### Análisis de Tendencias
```http
GET /v1/estadisticas/tendencias
```

**Parámetros:**
- `periodo` (string): dia, semana, mes, ano
- `metrica` (string): consultas, documentos, personas

## 📝 Modelos de Datos

### Documento
```typescript
interface Documento {
    id: number;
    archivo: string;
    texto_extraido?: string;
    analisis?: string;
    nuc: string;
    despacho: string;
    cuaderno: string;
    fecha_procesado: string; // ISO 8601
    metadatos: {
        paginas?: number;
        tamano_mb?: number;
        serie?: string;
        subserie?: string;
        authentication_info?: object;
    };
}
```

### Persona
```typescript
interface Persona {
    id: number;
    documento_id: number;
    nombre: string;
    tipo: 'victima' | 'responsable' | 'testigo' | 'defensa' | 'otro';
    observaciones?: string;
    fecha_registro: string; // ISO 8601
    metadatos?: {
        categoria_automatica?: string;
        confianza_clasificacion?: number;
    };
}
```

### Organización
```typescript
interface Organizacion {
    id: number;
    documento_id: number;
    nombre: string;
    tipo: 'militar' | 'policial' | 'paramilitar' | 'judicial' | 'civil' | 'otro';
    observaciones?: string;
    fecha_registro: string;
}
```

### Respuesta Estándar
```typescript
interface RespuestaAPI<T> {
    data: T | T[];
    pagination?: {
        page: number;
        limit: number;
        total: number;
        pages: number;
    };
    meta?: {
        tiempo_respuesta_ms: number;
        version_api: string;
        filtros_aplicados?: string[];
    };
    error?: {
        codigo: string;
        mensaje: string;
        detalles?: object;
    };
}
```

## 🚦 Códigos de Respuesta

### Éxito (2xx)
- `200 OK`: Solicitud exitosa
- `201 Created`: Recurso creado exitosamente
- `202 Accepted`: Solicitud aceptada para procesamiento
- `204 No Content`: Solicitud exitosa sin contenido

### Error del Cliente (4xx)
- `400 Bad Request`: Solicitud malformada
- `401 Unauthorized`: Token de autenticación requerido
- `403 Forbidden`: Permisos insuficientes
- `404 Not Found`: Recurso no encontrado
- `409 Conflict`: Conflicto con el estado actual
- `422 Unprocessable Entity`: Entidad no procesable
- `429 Too Many Requests`: Límite de velocidad excedido

### Error del Servidor (5xx)
- `500 Internal Server Error`: Error interno del servidor
- `502 Bad Gateway`: Error de gateway
- `503 Service Unavailable`: Servicio no disponible
- `504 Gateway Timeout`: Timeout de gateway

### Formato de Errores
```json
{
    "error": {
        "codigo": "VALIDATION_ERROR",
        "mensaje": "Los parámetros proporcionados no son válidos",
        "detalles": {
            "campo": "fecha_desde",
            "problema": "Formato de fecha inválido",
            "formato_esperado": "YYYY-MM-DD"
        }
    },
    "timestamp": "2024-08-20T10:30:00Z",
    "path": "/v1/documentos",
    "request_id": "req_abc123def456"
}
```

## 💡 Ejemplos de Uso

### Python SDK

```python
# Instalación
pip install documentos-juridicos-sdk

# Uso básico
from documentos_juridicos import DocumentosClient

client = DocumentosClient(api_key="sk-proj-abc123...")

# Buscar víctimas
victimas = client.personas.buscar(
    tipo="victima",
    buscar="María González",
    limit=50
)

for victima in victimas:
    print(f"Víctima: {victima.nombre}")
    documentos = client.documentos.por_persona(victima.id)
    print(f"  Documentos relacionados: {len(documentos)}")

# Consulta especializada
estadisticas = client.consultas.victimas_por_despacho()
for despacho, total in estadisticas.items():
    print(f"{despacho}: {total} víctimas")

# Búsqueda avanzada con IA
resultados = client.busqueda.inteligente(
    query="desaparición forzada comandantes militares",
    opciones={
        "incluir_sinonimos": True,
        "busqueda_fuzzy": True,
        "filtrar_relevancia": 0.8
    }
)
```

### JavaScript/Node.js

```javascript
// Instalación
npm install documentos-juridicos-js

// Uso básico
const { DocumentosClient } = require('documentos-juridicos-js');

const client = new DocumentosClient({
    apiKey: 'sk-proj-abc123...',
    baseURL: 'https://api.documentos-juridicos.fiscalia.gov.co/v1'
});

// Buscar documentos
async function buscarDocumentos() {
    try {
        const documentos = await client.documentos.listar({
            limit: 100,
            despacho: 'URI',
            buscar: 'víctima'
        });
        
        console.log(`Encontrados: ${documentos.pagination.total} documentos`);
        
        for (const doc of documentos.data) {
            console.log(`NUC: ${doc.nuc} - ${doc.archivo}`);
        }
    } catch (error) {
        console.error('Error:', error.message);
    }
}

// Consulta con streaming para grandes resultados
async function consultaConStreaming() {
    const stream = client.documentos.stream({
        nuc: '2015005204',
        incluir_texto: true
    });
    
    stream.on('data', (documento) => {
        console.log(`Procesando: ${documento.archivo}`);
    });
    
    stream.on('end', () => {
        console.log('Streaming completado');
    });
}
```

### cURL Ejemplos Avanzados

```bash
#!/bin/bash

API_KEY="sk-proj-abc123..."
BASE_URL="https://api.documentos-juridicos.fiscalia.gov.co/v1"

# Función para headers comunes
headers() {
    echo "-H 'Authorization: Bearer $API_KEY' -H 'Content-Type: application/json'"
}

# Buscar víctimas con filtros complejos
curl $(headers) -X POST "$BASE_URL/personas/buscar-inteligente" -d '{
    "query": "María González López",
    "filtros": {
        "tipo": ["victima"],
        "documento_fechas": {
            "desde": "2015-01-01",
            "hasta": "2024-12-31"
        }
    },
    "opciones": {
        "busqueda_fuzzy": true,
        "similitud_minima": 0.7,
        "incluir_contexto": true
    }
}'

# Exportar resultados en CSV
curl $(headers) -X GET "$BASE_URL/consultas/victimas-por-despacho?formato=csv" \
    -o "victimas_por_despacho.csv"

# Consulta con agregación compleja
curl $(headers) -X POST "$BASE_URL/consultas/personalizada" -d '{
    "descripcion": "Víctimas por año y tipo de delito",
    "agregacion": {
        "grupo_por": ["EXTRACT(YEAR FROM d.fecha_procesado)", "m.serie"],
        "metricas": ["COUNT(DISTINCT p.id) as total_victimas"],
        "filtros": {
            "personas.tipo": "victima",
            "metadatos.serie": ["Investigaciones", "Testimonios"]
        },
        "orden": ["-total_victimas"]
    }
}'
```

### Integraciones Comunes

#### Jupyter Notebook
```python
import pandas as pd
from documentos_juridicos import DocumentosClient
import matplotlib.pyplot as plt

# Configurar cliente
client = DocumentosClient(api_key="tu_api_key")

# Obtener estadísticas para visualización
stats = client.estadisticas.por_despacho()
df = pd.DataFrame(stats)

# Crear visualización
plt.figure(figsize=(12, 6))
plt.bar(df['despacho'], df['total_victimas'])
plt.title('Víctimas por Despacho')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
```

#### Power BI / Tableau
```python
# Conector para Power BI
import requests
import json

class DocumentosConnector:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.documentos-juridicos.fiscalia.gov.co/v1"
    
    def get_victimas_dataset(self):
        """Dataset optimizado para Power BI"""
        response = requests.get(
            f"{self.base_url}/consultas/victimas-powerbi",
            headers={'Authorization': f'Bearer {self.api_key}'}
        )
        return response.json()
    
    def get_documentos_timeline(self):
        """Timeline de documentos para visualización temporal"""
        response = requests.get(
            f"{self.base_url}/estadisticas/timeline",
            headers={'Authorization': f'Bearer {self.api_key}'}
        )
        return response.json()
```

## 🔧 Rate Limiting

### Límites por Defecto
- **Consultas por minuto**: 1000
- **Consultas por hora**: 50000
- **Consultas por día**: 1000000

### Headers de Rate Limiting
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1629446400
X-RateLimit-Window: 60
```

### Manejo de Rate Limiting
```python
import time
from documentos_juridicos import DocumentosClient, RateLimitError

client = DocumentosClient(api_key="tu_api_key")

def consulta_con_retry(consulta_func, max_intentos=3):
    for intento in range(max_intentos):
        try:
            return consulta_func()
        except RateLimitError as e:
            if intento < max_intentos - 1:
                tiempo_espera = e.retry_after
                print(f"Rate limit alcanzado. Esperando {tiempo_espera} segundos...")
                time.sleep(tiempo_espera)
            else:
                raise
```

## 🔗 Webhooks

### Configurar Webhooks
```http
POST /v1/webhooks
```

**Body:**
```json
{
    "url": "https://tu-aplicacion.com/webhook/documentos",
    "eventos": [
        "documento.procesado",
        "persona.creada",
        "consulta.completada"
    ],
    "filtros": {
        "despacho": ["URI", "CTI"]
    },
    "configuracion": {
        "retry_max": 3,
        "timeout_segundos": 30
    }
}
```

### Eventos Disponibles
- `documento.procesado`: Nuevo documento procesado
- `documento.actualizado`: Documento existente actualizado
- `persona.creada`: Nueva persona identificada
- `persona.actualizada`: Información de persona actualizada
- `organizacion.creada`: Nueva organización identificada
- `consulta.completada`: Consulta especializada completada
- `error.critico`: Error crítico en el sistema

### Formato de Webhook
```json
{
    "evento": "documento.procesado",
    "timestamp": "2024-08-20T10:30:00Z",
    "datos": {
        "documento_id": 12345,
        "archivo": "nuevo_documento.pdf",
        "nuc": "2024001234",
        "personas_identificadas": 5,
        "organizaciones_identificadas": 2
    },
    "webhook_id": "wh_abc123",
    "intento": 1
}
```

---

**Versión API**: v1.2.0  
**Última actualización**: 20 de Agosto, 2025  
**Soporte**: api-support@fiscalia.gov.co
