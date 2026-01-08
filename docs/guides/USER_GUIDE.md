# 📖 GUÍA DE USUARIO - SISTEMA UNIFICADO

## 🚀 **ACCESO RÁPIDO**

**URL:** http://localhost:8507  
**Estado:** ✅ OPERATIVO  

---

## 💬 **CÓMO USAR EL SISTEMA**

### **1. Simplemente Escribe Tu Consulta**
No necesitas saber si es una consulta de base de datos o RAG. El sistema decide automáticamente.

### **2. Ejemplos de Consultas**

#### **📊 Consultas de Datos (Sistema elegirá BD)**
```
¿Cuántas víctimas hay en total?
Dame el listado de víctimas
Buscar María García López
Mostrar responsables identificados
```

#### **🤖 Consultas de Análisis (Sistema elegirá RAG)**
```
¿Qué significa genocidio de la Unión Patriótica?
Analizar las estructuras criminales identificadas
Explicar las cadenas de mando
¿Por qué ocurrieron las masacres en el 2000?
```

#### **🔄 Consultas Completas (Sistema elegirá Híbrido)**
```
Víctimas de masacres con contexto legal
Documentos sobre ejecuciones extrajudiciales y su análisis
Casos de desplazamiento forzado con estadísticas
```

### **3. Información del Sistema**
- El sistema te mostrará qué tipo de consulta detectó
- Verás el nivel de confianza de la decisión
- Se explicará por qué eligió ese método

---

## 🎯 **QUÉ VER EN LA INTERFAZ**

### **Panel de Chat**
- Historial de conversación
- Respuestas contextuales completas

### **Información del Clasificador**
```
🤖 Clasificador IA: rag_complejo (Confianza: 0.95) - Análisis conceptual obvio
```

### **Panel de Fuentes**
- **📊 Base de Datos:** Datos estructurados
- **🤖 Análisis IA:** Documentos analizados
- **Scores de relevancia:** Qué tan relevante es cada fuente

---

## ⚡ **VENTAJAS**

✅ **Una sola interfaz** para todo  
✅ **Decisión automática** inteligente  
✅ **Respuestas completas** con contexto  
✅ **Transparencia** en el proceso  
✅ **Fuentes verificables** para cada respuesta  

---

## 🛠️ **SI ALGO NO FUNCIONA**

1. **Verifica la URL:** http://localhost:8507
2. **Si no responde:** El clasificador usará reglas de respaldo
3. **Si falla BD:** Automáticamente intenta RAG
4. **Si falla RAG:** Automáticamente intenta BD

El sistema tiene múltiples niveles de respaldo para asegurar que siempre obtengas una respuesta.

---

*¡Disfruta del sistema unificado!* 🎉
