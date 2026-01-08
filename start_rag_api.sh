#!/bin/bash

# Script para lanzar la API RAG
# Uso: ./start_rag_api.sh

echo "🚀 Iniciando API RAG - Documentos Judiciales..."

# Activar ambiente virtual
source venv_docs/bin/activate

# Verificar que las variables de entorno estén configuradas
if [ ! -f .env ]; then
    echo "❌ Error: No se encontró archivo .env"
    echo "Por favor, crea el archivo .env con las configuraciones necesarias"
    exit 1
fi

echo "✅ Ambiente virtual activado"
echo "✅ Variables de entorno cargadas"

# Lanzar API con uvicorn
echo "🌐 Iniciando API en http://localhost:8000"
echo "📚 Documentación disponible en http://localhost:8000/docs"
echo ""
echo "Para detener la API, presiona Ctrl+C"
echo ""

uvicorn src.api.rag_api:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --log-level info
