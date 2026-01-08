# 📊 Estado del Módulo de Grafos - Sistema Documentos Judiciales

**Fecha**: 2025-09-30
**Versión**: 0.1.0 (Prototipo en desarrollo)
**Responsable**: Sistema Modular

---

## ✅ Completado

### 1. Estructura Modular Creada
```
core/graph/
├── __init__.py              ✅ Módulo inicializado
├── config.py                ✅ Configuración centralizada
├── parser.py                ✅ Parser de entidades (en refinamiento)
├── age_connector.py         ⏳ Pendiente
├── graph_builder.py         ⏳ Pendiente
└── graph_queries.py         ⏳ Pendiente

scripts/graph_setup/
├── 01_install_age.sh        ⏳ Pendiente
├── 02_test_age.py           ⏳ Pendiente
├── 03_parse_sample.py       ✅ Creado y funcional
├── 04_populate_prototype.py ⏳ Pendiente
└── 05_populate_full.py      ⏳ Pendiente

tests/graph/
├── test_parser.py           ⏳ Pendiente
├── test_age_connection.py   ⏳ Pendiente
└── test_graph_queries.py    ⏳ Pendiente
```

### 2. Parser de Entidades (core/graph/parser.py)

**Estado**: ✅ Funcional parcialmente

**Capacidades actuales**:
- ✅ Extrae organizaciones del campo `analisis` de JSONs
- ✅ Genera relaciones de co-ocurrencia
- ⚠️ Extracción de personas: requiere refinamiento
- ⏳ Extracción de lugares: en desarrollo
- ⏳ Clasificaciones (víctima/responsable): en desarrollo

**Test actual**:
```bash
# JSON: 201500520432J_6466_C2_batch_resultado_20250619_130047.json
Personas: 0 (requiere ajuste de regex)
Organizaciones: 4 (✅ funcional)
  - ADRES
  - MINSALUD
  - Salud Total S.A.
  - Fuerzas ilegales
Relaciones: 6 (✅ co-ocurrencias generadas)
```

### 3. Configuración (core/graph/config.py)

**Estado**: ✅ Completo

Parámetros configurables:
- Conexión a PostgreSQL/AGE
- Nombre del grafo: `documentos_juridicos_graph`
- Batch sizes para parsing y construcción
- Paths de archivos JSON
- Límites para prototipado

---

## ⏳ En Desarrollo

### Parser de Entidades - Refinamiento Necesario

**Problema identificado**:
- Regex para personas no captura el formato exacto del campo `analisis`
- El análisis usa estructura: `#### **A. PERSONAS**` con subsección `- **Lista general de personas mencionadas:**`

**Solución en implementación**:
```python
# Ajustar regex para capturar:
# - **Nombre Completo**: Descripción del rol
```

**Próximos pasos**:
1. Refinar regex de personas
2. Implementar extracción de lugares
3. Capturar clasificaciones (víctima/responsable/etc.)
4. Validar con 100+ documentos diversos

---

## 🎯 Próximos Pasos

### Fase 1: Completar Parser (1-2 días)
- [ ] Refinar extracción de personas
- [ ] Implementar extracción de lugares
- [ ] Capturar clasificaciones completas
- [ ] Test con 100 documentos variados
- [ ] Documentar patrones encontrados

### Fase 2: Apache AGE Setup (1 día)
- [ ] Script instalación AGE (`01_install_age.sh`)
- [ ] Test conexión AGE (`02_test_age.py`)
- [ ] Crear grafo base en PostgreSQL
- [ ] Implementar `age_connector.py`

### Fase 3: Construcción del Grafo (2-3 días)
- [ ] Implementar `graph_builder.py`
- [ ] Poblado de nodos (personas, organizaciones, documentos)
- [ ] Poblado de edges (relaciones)
- [ ] Prototipo con 10K documentos
- [ ] Medición de performance

### Fase 4: Consultas Especializadas (2 días)
- [ ] Implementar `graph_queries.py`
- [ ] Consultas Cypher para:
  - Shortest path
  - Degree centrality
  - Pattern matching
- [ ] Benchmarks de performance

### Fase 5: Integración (2 días)
- [ ] Extender router LLM
- [ ] Integrar en `interfaz_principal.py`
- [ ] Tests end-to-end
- [ ] Documentación de uso

---

## 📋 Decisiones Técnicas Tomadas

### Motor de Grafos: Apache AGE
**Razón**:
- ✅ Extiende PostgreSQL actual (sin infraestructura adicional)
- ✅ Usa Cypher (lenguaje más simple que Gremlin)
- ✅ Consistencia transaccional con SQL existente
- ⚠️ Limitación: Algoritmos avanzados requieren implementación

**Alternativa evaluada**: Neo4j Community
- Más potente pero requiere servidor separado
- Reservado si AGE no cumple en prototipo

### Estrategia de Poblado
**Fuente**: Campo `analisis` de 11,111 (futuro 244K) JSONs
- Ya contiene extracción NER hecha por GPT-4
- Misma fuente que pobló PostgreSQL (consistencia)
- Evita re-procesamiento de PDFs

### Arquitectura Híbrida Final
```
Usuario → Router LLM → [SQL | RAG | GRAFO | Híbrido]
                         ↓     ↓      ↓        ↓
                    PostgreSQL Azure  AGE   Combinado
```

---

## 🔧 Comandos de Desarrollo

### Probar Parser
```bash
cd /home/lab4/scripts/documentos_judiciales
python3 scripts/graph_setup/03_parse_sample.py --docs 10
```

### Ver Resultados
```bash
cat tests/graph/parser_sample_results.json | jq '.stats'
```

### Estructura de Datos Extraídos
```json
{
  "documento_id": "nombre_archivo.pdf",
  "personas": [
    {
      "nombre": "Juan Pérez",
      "clasificacion": "victima",
      "documento_id": "doc123",
      "contexto": "Afiliado consultado"
    }
  ],
  "organizaciones": [
    {
      "nombre": "ADRES",
      "tipo": "fuerza_legitima",
      "documento_id": "doc123"
    }
  ],
  "lugares": [...],
  "relaciones": [
    {
      "origen": "Juan Pérez",
      "destino": "ADRES",
      "tipo": "co_ocurrencia_persona_org",
      "documento_id": "doc123",
      "fuerza": 1.0
    }
  ]
}
```

---

## 📊 Estimaciones

### Tamaño del Grafo (244K documentos)
```
Nodos estimados: 800K - 1.3M
  - Personas: 500K - 1M
  - Organizaciones: 50K
  - Lugares: 20K
  - Documentos: 244K

Edges estimados: 7M - 13M
  - Co-ocurrencias: 5M - 10M
  - Vínculos directos: 2M - 3M

Tamaño en disco: ~10-15 GB (con índices)
Tiempo de poblado: 6-8 horas (estimado)
```

### Performance Esperada (con Apache AGE)
```
- Shortest path (2-3 saltos): < 500ms ✅
- Pattern matching: < 1s ✅
- Degree centrality: < 2s ✅
- Deep traversals (5+ saltos): 2-5s ⚠️
- PageRank: Requiere implementación custom ⚠️
```

---

## 🚀 Objetivo Final

**Sistema unificado con 4 modos de consulta**:

1. **SQL**: Consultas estructuradas (filtros, conteos, agregaciones)
2. **RAG**: Análisis semántico con GPT-4 (contexto, narrativa)
3. **GRAFO**: Relaciones y análisis de redes (caminos, centralidad)
4. **HÍBRIDO**: Combinación inteligente de los 3 anteriores

**Router LLM** decide automáticamente según la pregunta del usuario.

---

**Próxima sesión**: Continuar con refinamiento del parser y setup de Apache AGE
