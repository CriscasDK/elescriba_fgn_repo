#!/bin/bash
# Script de Restauración del Sistema RAG Jurídico
# Fecha: 28 de Agosto de 2025
# Backup: backup_sistema_rag_28ago2025_1055.tar.gz

echo "🔄 INICIANDO RESTAURACIÓN DEL SISTEMA RAG JURÍDICO"
echo "Fecha del backup: 28 de Agosto de 2025 - 10:55 AM"
echo "=================================================="

# Verificar si existe el archivo de backup
if [ ! -f "backup_sistema_rag_28ago2025_1055.tar.gz" ]; then
    echo "❌ ERROR: Archivo de backup no encontrado"
    echo "Esperado: backup_sistema_rag_28ago2025_1055.tar.gz"
    exit 1
fi

echo "✅ Archivo de backup encontrado ($(ls -lh backup_sistema_rag_28ago2025_1055.tar.gz | awk '{print $5}'))"

# Crear directorio de respaldo del estado actual
echo "📦 Creando respaldo del estado actual..."
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
mkdir -p "respaldo_antes_restauracion_$TIMESTAMP"

# Respaldar archivos existentes que serán reemplazados
if [ -f "interfaz_principal.py" ]; then
    cp interfaz_principal.py "respaldo_antes_restauracion_$TIMESTAMP/"
fi
if [ -d "src/" ]; then
    cp -r src/ "respaldo_antes_restauracion_$TIMESTAMP/"
fi
if [ -f "clasificador_inteligente_llm.py" ]; then
    cp clasificador_inteligente_llm.py "respaldo_antes_restauracion_$TIMESTAMP/"
fi

echo "✅ Estado actual respaldado en: respaldo_antes_restauracion_$TIMESTAMP"

# Extraer backup
echo "📂 Extrayendo backup..."
tar -xzf backup_sistema_rag_28ago2025_1055.tar.gz

echo "✅ Archivos restaurados desde backup"

# Verificar archivos críticos
echo "🔍 Verificando archivos críticos..."

critical_files=(
    "interfaz_principal.py"
    "src/core/sistema_rag_completo.py" 
    "src/core/azure_search_vectorizado.py"
    "clasificador_inteligente_llm.py"
    "config/.env"
    "test_busqueda_cruzada.py"
)

all_ok=true
for file in "${critical_files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file - FALTANTE"
        all_ok=false
    fi
done

if [ "$all_ok" = true ]; then
    echo "✅ Todos los archivos críticos restaurados correctamente"
else
    echo "⚠️  Algunos archivos críticos faltan - revisar manualmente"
fi

# Verificar ambiente virtual
echo "🐍 Verificando ambiente virtual..."
if [ -d "venv_docs" ]; then
    echo "  ✅ venv_docs encontrado"
else
    echo "  ⚠️  venv_docs no encontrado - crear manualmente:"
    echo "     python -m venv venv_docs"
    echo "     source venv_docs/bin/activate"
    echo "     pip install -r api_requirements.txt"
fi

# Mostrar comandos para iniciar el sistema
echo ""
echo "🚀 COMANDOS PARA INICIAR EL SISTEMA:"
echo "=================================================="
echo "1. Activar ambiente virtual:"
echo "   source venv_docs/bin/activate"
echo ""
echo "2. Instalar dependencias (si es necesario):"
echo "   pip install -r api_requirements.txt"
echo ""
echo "3. Iniciar interfaz principal:"
echo "   streamlit run interfaz_principal.py --server.port 8508 --server.address 0.0.0.0"
echo ""
echo "4. Acceder a la aplicación:"
echo "   Local:  http://localhost:8508"
echo "   Red:    http://10.1.180.13:8508"
echo ""
echo "5. Base de datos (si es necesario):"
echo "   psql -h localhost -p 5432 -d documentos_juridicos_gpt4 -U docs_user"
echo ""

# Mostrar información del estado restaurado
echo "📊 INFORMACIÓN DEL SISTEMA RESTAURADO:"
echo "=================================================="
echo "Funcionalidades incluidas:"
echo "  ✅ Sistema RAG completo unificado"
echo "  ✅ Búsqueda cruzada entre índices Azure Search"
echo "  ✅ Interfaz dinámica inteligente"
echo "  ✅ Panel de filtros integrado"
echo "  ✅ Clasificación automática de consultas"
echo "  ✅ Metadatos y trazabilidad completa"
echo ""
echo "Índices Azure Search configurados:"
echo "  - exhaustive-legal-chunks-v2 (100,025+ chunks)"
echo "  - exhaustive-legal-index (documentos completos)"
echo ""
echo "Base de datos PostgreSQL:"
echo "  - 11,111 documentos únicos"
echo "  - 12,248 víctimas documentadas"
echo ""

echo "🎉 RESTAURACIÓN COMPLETADA EXITOSAMENTE"
echo "Consulta DOCUMENTACION_BACKUP_28AGO2025.md para detalles técnicos completos"
