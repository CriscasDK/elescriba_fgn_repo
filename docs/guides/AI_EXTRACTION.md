# 🤖 EXTRACCIÓN MASIVA DE RELACIONES CON IA

**Sistema:** ESCRIBA - Fiscalía General de la Nación
**Fecha:** 31 de Octubre, 2025
**Propósito:** Extracción automática de relaciones semánticas usando Azure OpenAI GPT-4

---

## 📊 **RESUMEN DEL PROYECTO**

### **Estadísticas:**
- **Documentos totales con análisis:** 11,111
- **Ya procesados:** 0
- **Pendientes de procesar:** 11,111

### **Estimaciones:**
- **Tokens estimados:** ~19.6 millones
- **Costo estimado:** ~**$589 USD**
- **Tiempo estimado:** ~**9-10 horas**
- **Velocidad:** ~3-4 segundos por documento

---

## 🚀 **INICIO RÁPIDO**

### **Paso 1: Iniciar el Proceso**

```bash
cd /home/lab4/scripts/documentos_judiciales

# Opción A: Modo interactivo (confirma antes de iniciar)
./scripts/start_ai_extraction.sh

# Opción B: Modo directo (para scripts)
source venv_docs/bin/activate
nohup python scripts/extract_relations_with_ai_batch.py > logs/extraction.log 2>&1 &
```

### **Paso 2: Monitorear el Progreso**

```bash
# Ver monitor en tiempo real (actualizar cada 10 segundos)
watch -n 10 ./scripts/monitor_ai_extraction.sh

# O ejecutar una sola vez
./scripts/monitor_ai_extraction.sh

# Ver logs en tiempo real
tail -f logs/ai_extraction_*.log
```

### **Paso 3: Detener si es Necesario**

```bash
# Ver PID del proceso
cat logs/ai_extraction.pid

# Detener proceso
kill $(cat logs/ai_extraction.pid)

# El checkpoint se guarda automáticamente
# Puedes resumir más tarde con el mismo comando de inicio
```

---

## 🔧 **CARACTERÍSTICAS DEL SISTEMA**

### **1. Checkpoint Automático**
- Se guarda cada 100 documentos
- Si el proceso se interrumpe, puedes resumir desde donde quedó
- Archivo: `logs/extraction_checkpoint.json`

### **2. Rate Limiting**
- 0.5 segundos entre llamadas API
- Evita throttling de Azure OpenAI
- Configurable con `--rate-limit`

### **3. Reintentos Automáticos**
- 3 intentos por documento
- Backoff exponencial (5s, 10s, 20s)
- Manejo de errores de red y API

### **4. Logging Detallado**
- Logs en `logs/ai_extraction_TIMESTAMP.log`
- Nivel INFO con timestamps
- Errores capturados con stack traces

### **5. Estimación de Progreso**
- ETA (tiempo estimado restante)
- Progreso en porcentaje
- Velocidad actual (docs/seg)
- Costo acumulado en USD

---

## 📋 **FORMATO DE SALIDA**

Las relaciones se guardan en la tabla `relaciones_extraidas` con:

```sql
CREATE TABLE relaciones_extraidas (
    id SERIAL PRIMARY KEY,
    entidad_origen VARCHAR(500),      -- "Omar de Jesús Correa Isaza"
    entidad_destino VARCHAR(500),     -- "María Ligia Isaza"
    tipo_relacion VARCHAR(200),       -- "hijo"
    documento_id INTEGER,             -- Documento de origen
    contexto TEXT,                    -- Frase que soporta la relación
    confianza FLOAT,                  -- 0.5 - 1.0
    metodo_extraccion VARCHAR(100),   -- "gpt4_from_analisis"
    created_at TIMESTAMP
);
```

---

## 🧪 **VERIFICACIÓN DE CALIDAD**

### **Después de procesar N documentos, verificar:**

```bash
# 1. Ver estadísticas generales
source venv_docs/bin/activate
python -c "
from core.consultas import get_db_connection
conn = get_db_connection()
cur = conn.cursor()

cur.execute('''
    SELECT
        COUNT(DISTINCT documento_id) as docs,
        COUNT(*) as relaciones,
        COUNT(DISTINCT tipo_relacion) as tipos,
        AVG(confianza)::numeric(3,2) as confianza_promedio
    FROM relaciones_extraidas
    WHERE metodo_extraccion = 'gpt4_from_analisis'
''')

docs, rels, tipos, conf = cur.fetchone()
print(f'Documentos procesados: {docs:,}')
print(f'Relaciones extraídas: {rels:,}')
print(f'Tipos distintos: {tipos}')
print(f'Confianza promedio: {conf}')

cur.close()
conn.close()
"

# 2. Ver top relaciones
python -c "
from core.consultas import get_db_connection
conn = get_db_connection()
cur = conn.cursor()

cur.execute('''
    SELECT tipo_relacion, COUNT(*) as total
    FROM relaciones_extraidas
    WHERE metodo_extraccion = 'gpt4_from_analisis'
    GROUP BY tipo_relacion
    ORDER BY total DESC
    LIMIT 15
''')

print('\\nTOP TIPOS DE RELACIONES:')
print('='*50)
for tipo, total in cur.fetchall():
    print(f'{tipo:30} {total:>8,}')

cur.close()
conn.close()
"

# 3. Comparar con método anterior (regex)
python scripts/extract_relations_with_ai.py --compare
```

---

## ⚠️ **CONSIDERACIONES IMPORTANTES**

### **Costos:**
- Azure OpenAI GPT-4: ~$0.03 por 1K tokens
- Estimado total: **~$589 USD**
- Se factura según uso real (puede ser menos)

### **Tiempo:**
- Estimado: ~9-10 horas corriendo 24/7
- Depende de:
  - Velocidad de respuesta de Azure
  - Rate limiting configurado
  - Errores/reintentos

### **Recursos:**
- CPU: Bajo (solo llamadas API)
- RAM: ~500MB
- Disco: ~100MB para logs
- Red: Constante (llamadas API)

### **Recomendaciones:**
- ✅ Ejecutar en servidor/VM dedicado
- ✅ Verificar espacio en disco para logs
- ✅ Configurar alertas de costo en Azure
- ✅ Hacer backup de BD antes de iniciar
- ✅ Revisar primeras 100 relaciones para QA

---

## 🔍 **CALIDAD DE RELACIONES (IA vs Regex)**

### **Mejoras esperadas con IA:**

**ANTES (Regex):**
```
Omar de Jesús Correa Isaza --[victima_de]--> Fiscalía General  ❌
Omar de Jesús Correa Isaza --[victima_de]--> Procuraduría     ❌
Omar de Jesús Correa Isaza --[victima_de]--> ASFADDES         ❌
```
*(Falsos positivos: "víctima investigada por" ≠ "víctima de")*

**AHORA (IA):**
```
Omar de Jesús Correa Isaza --[hijo]--> María Ligia Isaza            ✅
Omar de Jesús Correa Isaza --[miembro_de]--> Partido Comunista     ✅
Omar de Jesús Correa Isaza --[esposo]--> Cruz Amparo Zapata        ✅
Omar de Jesús Correa Isaza --[victima_de]--> Desaparición forzada  ✅
```
*(Relaciones contextuales precisas)*

### **Ventajas del método IA:**
1. ✅ Distingue "investigado por" vs "víctima de"
2. ✅ Entiende contexto colombiano (agentes del Estado como victimarios)
3. ✅ Score de confianza por relación
4. ✅ Explica cada relación (campo `contexto`)
5. ✅ Reduce falsos positivos dramáticamente

---

## 📞 **SOPORTE Y TROUBLESHOOTING**

### **Problema: Proceso se detuvo**
```bash
# 1. Verificar si está corriendo
ps aux | grep extract_relations_with_ai_batch

# 2. Ver último error en logs
tail -50 logs/ai_extraction_*.log | grep ERROR

# 3. Verificar checkpoint
cat logs/extraction_checkpoint.json | python -m json.tool

# 4. Resumir desde checkpoint
./scripts/start_ai_extraction.sh
# (Automáticamente continúa desde donde quedó)
```

### **Problema: Muchos errores de API**
```bash
# Verificar conectividad
curl -s https://api.openai.com/v1/models > /dev/null && echo "OK" || echo "ERROR"

# Verificar API key
echo $AZURE_OPENAI_API_KEY | head -c 10
```

### **Problema: Costo muy alto**
```bash
# Ver costo acumulado en checkpoint
cat logs/extraction_checkpoint.json | grep tokens_usados

# Detener proceso
kill $(cat logs/ai_extraction.pid)

# Analizar primeras N relaciones antes de continuar
```

---

## 📈 **PRÓXIMOS PASOS DESPUÉS DE COMPLETAR**

1. **Verificar calidad:**
   - Revisar muestra de 100 relaciones aleatorias
   - Comparar con relaciones conocidas (casos famosos)
   - Calcular precisión y recall

2. **Visualizar en grafos mejorados:**
   - Regenerar grafos 3D con nuevas relaciones
   - Comparar densidad de red antes/después
   - Identificar nuevas conexiones descubiertas

3. **Analítica avanzada:**
   - Top personas con más conexiones
   - Organizaciones más mencionadas
   - Patrones de relaciones victima-victimario
   - Red de organizaciones criminales

4. **Exportar resultados:**
   - CSV para análisis en Excel/Python
   - GraphML para Gephi/Cytoscape
   - JSON para visualizaciones web

---

## 📝 **REGISTRO DE EJECUCIÓN**

### **Ejecución 1: [FECHA]**
- Inicio: __________
- Fin: __________
- Documentos procesados: __________
- Relaciones extraídas: __________
- Costo real: $__________
- Observaciones: __________

---

## 🏛️ **FIRMA**

**Fiscalía General de la Nación - Colombia**
**Sistema ESCRIBA - Extracción IA de Relaciones Semánticas**

**Elaborado:** 31 de Octubre, 2025
**Responsable:** Equipo de Análisis de Datos
**Estado:** ✅ Listo para producción

---

**🚀 ¡Listo para iniciar! Ejecuta `./scripts/start_ai_extraction.sh`**
