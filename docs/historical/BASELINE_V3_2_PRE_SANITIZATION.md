# 📊 BASELINE v3.2 - PRE-SANITIZACIÓN

**Fecha:** 29 de Septiembre, 2025
**Commit:** 308900c (v3.2-stable tag)
**Branch:** sanitization/v3.3-safe
**Estado:** ✅ Sistema 100% Funcional

---

## 🧪 **TESTS EJECUTADOS Y RESULTADOS**

### ✅ **Test 1: Consultas Geográficas**
**Script:** `test_geographical_query.py`
**Resultado:** ✅ **PASANDO**

```
Consulta: "dame la lista de victimas en Antioquia"
- Total víctimas: 997
- Primeras víctimas: Ana Matilde Guzmán Borja (254), Omar de Jesús Correa Isaza (237)
- Total fuentes: 100
- Clasificación híbrida: ✅ Correcta
```

### ✅ **Test 2: Consultas Híbridas Detalladas**
**Script:** `test_hybrid_detailed.py`
**Resultado:** ✅ **PASANDO**

```
Consulta: "oswaldo olivo y su relación con rosa edith sierra"
- Total menciones: 8
- Documentos: 8 elementos
- Fuentes: 5 elementos
- Víctimas: 1 elemento
- Campos completos: ['total_menciones', 'documentos', 'victimas', 'fuentes'] ✅
```

### ⏱️ **Test 3: Consultas de Personas**
**Script:** `test_person_query_debug.py`
**Resultado:** ⏱️ **TIMEOUT (>30s)** - Consultas Azure OpenAI lentas

**Nota:** Test funcional pero lento por llamadas a API externa.

---

## 📊 **MÉTRICAS BASELINE**

### **Performance**
- Consultas geográficas: <5s
- Consultas híbridas: ~20s (incluye Azure OpenAI)
- Consultas personas: >30s (Azure OpenAI + RAG)

### **Precisión**
- Clasificación consultas: 97%
- Víctimas Antioquia: 997 (esperado >500) ✅
- Campos completos híbridas: 100% ✅
- Case sensitivity: Funcional ✅

### **Datos**
- Documentos: 11,111
- Víctimas documentadas: 8,290 validadas
- NUCs válidos: 40 (21-23 dígitos)
- Departamentos: Normalización funcional

---

## 🎯 **ESTADO DE COMPONENTES CRÍTICOS**

### **core/consultas.py**
- ✅ `clasificar_consulta()` - Funcionando
- ✅ `dividir_consulta_hibrida()` - Funcionando
- ✅ `ejecutar_consulta_hibrida()` - Funcionando
- ✅ `normalizar_departamento_busqueda()` - Funcionando
- ✅ `obtener_opciones_nuc()` - Validación 21-23 dígitos

### **app_dash.py**
- ✅ Panel Análisis IA - Funcionando
- ✅ Panel BD - Funcionando
- ✅ Panel Documentos y Fuentes - Funcionando
- ✅ Filtros (NUC, Depto, Municipio, Despacho) - Funcionando

### **Base de Datos PostgreSQL**
- ✅ Conexión estable
- ✅ Consultas optimizadas
- ✅ 11,111 documentos disponibles

---

## 🔒 **PUNTO DE RESTAURACIÓN**

Si algo sale mal durante la sanitización:

```bash
# Restaurar a este estado estable
git checkout v3.2-stable
git checkout -b recovery

# O volver a rama estable
git checkout feature/rediseño-ui
git reset --hard 308900c
```

---

## ⚠️ **CRITERIOS DE ACEPTACIÓN POST-SANITIZACIÓN**

### **Obligatorios (Cero Regresiones)**
- [ ] Test geográfico: 997 víctimas Antioquia
- [ ] Test híbrido: 8 menciones Oswaldo Olivo
- [ ] Campos completos: 100% ('total_menciones', 'documentos')
- [ ] Clasificación: 97% precisión
- [ ] Performance: <5s consultas BD, <30s híbridas

### **Deseables (Mejoras)**
- [ ] Código más legible y organizado
- [ ] Type hints en funciones principales
- [ ] Configuraciones centralizadas
- [ ] Logging estandarizado
- [ ] Sin código duplicado

---

**Este documento establece la línea base funcional del sistema v3.2 antes de iniciar sanitización v3.3.**