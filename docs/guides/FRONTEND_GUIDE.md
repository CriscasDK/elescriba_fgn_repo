# 🚀 Frontend RAG - Guía de Inicio Rápido

## 🎯 **Frontend Streamlit Desplegado**

### 📍 **URLs de Acceso:**
- **Frontend RAG:** http://localhost:8501
- **pgAdmin:** http://localhost:8080
- **PostgreSQL:** localhost:5432

## 💻 **Interfaz de Usuario**

### 🏠 **Página Principal (3 Tabs):**

#### 1. 💬 **Chat RAG** - Interfaz Principal
- **Chat inteligente** tipo ChatGPT
- **Consultas de ejemplo** con botones rápidos
- **Historial de conversación** con métricas
- **Feedback inmediato** (👍👎) para mejora continua

#### 2. 📊 **Dashboard** - Métricas Ejecutivas
- **Métricas principales:** Documentos, personas, organizaciones
- **Gráficos interactivos:** Performance por método
- **Estadísticas en tiempo real:** Consultas del día

#### 3. 🔍 **Análisis** - Herramientas Avanzadas
- **Análisis de entidades:** Top personas/organizaciones
- **Análisis geográfico:** Distribución por departamentos
- **Análisis temporal:** Evolución de eventos
- **Redes de relaciones:** Conexiones entre entidades

## 🎮 **Guía de Uso**

### 🚀 **Inicio Rápido (5 minutos):**

1. **Abrir Frontend:** http://localhost:8501
2. **Probar consultas de ejemplo:**
   - Clic en "📊 Estadísticas Generales"
   - Clic en "👥 Personas Más Mencionadas"
   - Clic en "🏛️ Análisis de Organizaciones"

### 💬 **Usar el Chat RAG:**

#### **Consultas Frecuentes (Base de Datos - Rápidas):**
```
¿Cuántos documentos hay procesados?
¿Cuáles son las estadísticas principales?
Dame el top 10 de personas más mencionadas
¿Cuántas víctimas hay por departamento?
Muéstrame el dashboard principal
```

#### **Consultas RAG (LLM - Complejas):**
```
¿Cómo impactó la violencia a las víctimas?
¿Qué relación hay entre FARC y las víctimas?
Explica el papel de las fuerzas armadas
¿Por qué Antioquia aparece tanto en los documentos?
Analiza las consecuencias del conflicto
```

#### **Consultas Híbridas (Adaptativas):**
```
¿Qué organizaciones están más involucradas?
¿Cuáles son los principales actores del conflicto?
¿Qué lugares son más relevantes en el caso?
```

## 🎯 **Ejemplos de Interacción**

### ⚡ **Consulta Rápida (80ms):**
```
👤 Usuario: "¿Cuántas víctimas hay?"
🤖 Sistema: "He encontrado 1,247 víctimas identificadas en el sistema..."
⏱️ Tiempo: 87ms | 🎯 Confianza: 95% | 🔧 Método: vista_materializada
```

### 🧠 **Consulta Compleja (3s):**
```
👤 Usuario: "¿Cómo afectó la violencia a las comunidades rurales?"
🤖 Sistema: "Basándome en el análisis de 234 documentos, la violencia impactó..."
⏱️ Tiempo: 3,247ms | 🎯 Confianza: 78% | 🔧 Método: llm_generacion
```

## 📊 **Panel de Control**

### 🔧 **Sidebar (Información del Sistema):**
- **Estado actual:** Documentos, personas, organizaciones
- **Performance:** Tiempo promedio de respuesta
- **Consultas del día:** Contador en tiempo real
- **Configuración:** Base de datos, modelo IA
- **Documentación:** Enlaces a guías técnicas

### 📈 **Métricas en Tiempo Real:**
- **Documentos procesados:** 11,111+
- **Personas identificadas:** 68,039+
- **Organizaciones clasificadas:** 65,608+
- **Tiempo promedio:** < 100ms para BD, ~3s para RAG

## 🎨 **Características de la UI**

### ✨ **Diseño Visual:**
- **Tema moderno:** Gradiente azul con glass morphism
- **Responsive:** Se adapta a diferentes pantallas
- **Iconos intuitivos:** Cada sección tiene iconos claros
- **Colores semánticos:** Verde para éxito, azul para info

### 🔄 **Interactividad:**
- **Botones de ejemplo:** Consultas predefinidas
- **Feedback inmediato:** Botones 👍👎 para cada respuesta
- **Historial persistente:** Se mantiene durante la sesión
- **Cache inteligente:** Respuestas instantáneas para consultas repetidas

### 📱 **Usabilidad:**
- **Placeholders informativos:** Ejemplos en campos de entrada
- **Mensajes de estado:** Spinners y confirmaciones
- **Errores amigables:** Mensajes claros en caso de problemas
- **Shortcuts:** Botones rápidos para acciones comunes

## 🔧 **Configuración y Personalización**

### ⚙️ **Variables de Entorno:**
```bash
# Frontend se conecta automáticamente a:
POSTGRES_HOST=localhost
POSTGRES_DB=documentos_juridicos_gpt4
POSTGRES_USER=docs_user
POSTGRES_PASSWORD=docs_password_2024

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=tu_endpoint
AZURE_OPENAI_API_KEY=tu_api_key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini
```

### 🎨 **Personalización Visual:**
El frontend usa CSS personalizado que puedes modificar en `streamlit_app.py`:
- **Colores:** Cambiar el gradiente de fondo
- **Tipografía:** Ajustar fuentes y tamaños
- **Layout:** Modificar distribución de columnas
- **Componentes:** Agregar nuevos elementos visuales

## 🚀 **Despliegue en Producción**

### 🐳 **Con Docker Compose:**
```bash
# Construir y levantar todo el stack
docker compose up -d

# Acceder a:
# Frontend: http://localhost:8501
# pgAdmin: http://localhost:8080
# PostgreSQL: localhost:5432
```

### 📋 **Verificación Post-Despliegue:**
1. ✅ Frontend carga correctamente
2. ✅ Se conecta a la base de datos
3. ✅ Azure OpenAI responde
4. ✅ Chat funciona con ejemplos
5. ✅ Dashboard muestra métricas
6. ✅ Análisis carga sin errores

## 🔍 **Troubleshooting Frontend**

### ❌ **Problemas Comunes:**

#### **Frontend no carga:**
```bash
# Verificar si Streamlit está ejecutándose
curl http://localhost:8501
# Si falla, verificar logs:
docker logs docs_frontend
```

#### **No se conecta a BD:**
```bash
# Verificar conectividad
docker exec -it docs_frontend python -c "
import psycopg2
conn = psycopg2.connect(host='postgres', database='documentos_juridicos_gpt4', user='docs_user', password='docs_password_2024')
print('✅ Conexión exitosa')
"
```

#### **Azure OpenAI falla:**
```bash
# Verificar variables de entorno
docker exec -it docs_frontend env | grep AZURE
```

### 🔧 **Logs y Debugging:**
```bash
# Logs del frontend
docker logs -f docs_frontend

# Logs de Streamlit
docker exec -it docs_frontend streamlit --help

# Restart del frontend
docker restart docs_frontend
```

## 📈 **Próximas Mejoras**

### 🎯 **Funcionalidades Planeadas:**
- [ ] **Autenticación:** Sistema de login/usuarios
- [ ] **Exportación:** PDF/Excel de resultados
- [ ] **Notificaciones:** Alertas en tiempo real
- [ ] **Mapas interactivos:** Visualización geográfica
- [ ] **Análisis de sentimientos:** Emociones en documentos
- [ ] **API REST:** Endpoints para integración externa

### 🔧 **Optimizaciones Técnicas:**
- [ ] **Cache avanzado:** Redis para respuestas compartidas
- [ ] **Websockets:** Updates en tiempo real
- [ ] **Compresión:** Optimización de assets
- [ ] **CDN:** Distribución de contenido estático
- [ ] **A/B Testing:** Diferentes interfaces
- [ ] **Analytics:** Tracking de uso detallado

---

## 🎉 **¡Frontend RAG Operativo!**

**🌐 Acceso inmediato:** http://localhost:8501  
**📊 Métricas en vivo:** Dashboard integrado  
**💬 Chat inteligente:** RAG + Base de datos híbrido  
**🔧 100% funcional:** Listo para producción  

---

**📅 Creado:** Julio 25, 2025  
**🚀 Estado:** Producción  
**👨‍💻 Stack:** Streamlit + PostgreSQL + Azure OpenAI
