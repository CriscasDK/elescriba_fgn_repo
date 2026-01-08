#!/bin/bash
# Script de inicio del sistema RAG - Versión sanitizada
# Fecha: Julio 28, 2025
# Ubicación: /scripts/ (raíz del proyecto)

echo "🚀 Iniciando Sistema RAG Documentos Jurídicos v2.0"
echo "=================================================="

# Verificar estructura sanitizada
if [ ! -d "src/core" ]; then
    echo "❌ ERROR: Estructura sanitizada no encontrada"
    echo "   Ejecute primero la sanitización del proyecto"
    exit 1
fi

# Verificar Python virtual environment
if [ ! -d "venv_docs" ]; then
    echo "📦 Creando entorno virtual Python..."
    python3 -m venv venv_docs
fi

# Activar entorno virtual
echo "🔧 Activando entorno virtual..."
source venv_docs/bin/activate

# Instalar dependencias desde config/
echo "📥 Instalando dependencias..."
pip install -r config/requirements.txt

# Verificar configuración
if [ ! -f "config/.env" ]; then
    echo "⚠️  Archivo .env no encontrado en config/"
    echo "   Copiando template..."
    cp config/.env.template config/.env
    echo "   ✏️  EDITE config/.env con sus credenciales antes de continuar"
fi

# Verificar conexión a base de datos
echo "🔍 Verificando conexión a base de datos..."
python3 -c "
import sys
sys.path.append('src')
from core.sistema_rag_completo import SistemaRAGCompleto
try:
    sistema = SistemaRAGCompleto()
    print('✅ Conexión a BD exitosa')
except Exception as e:
    print(f'❌ Error conexión BD: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ No se pudo conectar a la base de datos"
    echo "   Verifique que PostgreSQL esté ejecutándose"
    exit 1
fi

echo ""
echo "✅ Sistema inicializado correctamente"
echo ""
echo "🎯 Opciones disponibles:"
echo "   1. API REST:     cd src/api && python api_rag.py"
echo "   2. Dashboard:    cd src/api && streamlit run streamlit_app.py"
echo "   3. Verificación: cd src/maintenance && python verificacion_final.py"
echo ""
echo "🔧 Sistema ubicado en estructura sanitizada:"
echo "   - Core:         src/core/"
echo "   - API:          src/api/"
echo "   - Análisis:     src/analysis/"
echo "   - Mantenimiento: src/maintenance/"
echo "   - SQL:          sql/validated/"
echo "   - Config:       config/"
echo ""
echo "📚 Documentación en: docs/"
echo "🗄️  Archivos históricos en: archive/"
