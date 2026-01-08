#!/bin/bash

# Script de inicio para la API RAG
echo "🚀 Iniciando API RAG - Sistema de Documentos Jurídicos"
echo "=============================================="

# Verificar virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Activando virtual environment..."
    source venv_docs/bin/activate
fi

# Instalar dependencias si es necesario
echo "📦 Verificando dependencias de la API..."
pip install -r requirements_api.txt

# Verificar archivo .env
if [[ ! -f ".env.gpt41" ]]; then
    echo "❌ Error: Archivo .env.gpt41 no encontrado"
    echo "   Asegúrate de tener configuradas las variables de entorno"
    exit 1
fi

# Iniciar la API
echo "🌟 Iniciando servidor API en puerto 8000..."
echo "📍 URL: http://localhost:8000"
echo "📚 Documentación: http://localhost:8000/api/docs"
echo "🔍 Redoc: http://localhost:8000/api/redoc"
echo ""
echo "Presiona Ctrl+C para detener el servidor"
echo "=============================================="

python api_rag.py
