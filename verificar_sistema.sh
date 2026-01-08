#!/bin/bash
# Script de Verificación del Sistema RAG Jurídico
# Verifica el estado completo del sistema después de la restauración

echo "🔍 VERIFICACIÓN COMPLETA DEL SISTEMA RAG JURÍDICO"
echo "=================================================="

# Verificar estructura de archivos
echo "📁 Verificando estructura de archivos..."
expected_files=(
    "interfaz_principal.py"
    "src/core/sistema_rag_completo.py"
    "src/core/azure_search_vectorizado.py" 
    "src/core/consultor_base_datos.py"
    "clasificador_inteligente_llm.py"
    "config/.env"
    "api_requirements.txt"
    "docker-compose.yml"
    "test_busqueda_cruzada.py"
    "DOCUMENTACION_BACKUP_28AGO2025.md"
)

files_ok=0
files_missing=0

for file in "${expected_files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
        ((files_ok++))
    else
        echo "  ❌ $file - FALTANTE"
        ((files_missing++))
    fi
done

echo "📊 Archivos encontrados: $files_ok/$((files_ok + files_missing))"

# Verificar ambiente Python
echo ""
echo "🐍 Verificando ambiente Python..."
if [ -d "venv_docs" ]; then
    echo "  ✅ Ambiente virtual venv_docs encontrado"
    if [ -f "venv_docs/bin/activate" ]; then
        echo "  ✅ Activador encontrado"
        source venv_docs/bin/activate
        
        # Verificar paquetes críticos
        echo "  📦 Verificando paquetes críticos..."
        critical_packages=("streamlit" "openai" "azure-search-documents" "psycopg2" "python-dotenv")
        
        for package in "${critical_packages[@]}"; do
            if pip show "$package" > /dev/null 2>&1; then
                version=$(pip show "$package" | grep Version | cut -d: -f2 | tr -d ' ')
                echo "    ✅ $package ($version)"
            else
                echo "    ❌ $package - NO INSTALADO"
            fi
        done
    else
        echo "  ❌ Activador no encontrado"
    fi
else
    echo "  ❌ Ambiente virtual no encontrado"
fi

# Verificar configuración
echo ""
echo "⚙️  Verificando configuración..."
if [ -f "config/.env" ]; then
    echo "  ✅ Archivo .env encontrado"
    
    # Verificar variables críticas (sin mostrar valores)
    critical_vars=("AZURE_OPENAI_API_KEY" "AZURE_SEARCH_SERVICE_NAME" "AZURE_SEARCH_API_KEY" "DB_HOST" "DB_NAME")
    
    for var in "${critical_vars[@]}"; do
        if grep -q "^$var=" config/.env; then
            echo "    ✅ $var configurado"
        else
            echo "    ❌ $var - NO CONFIGURADO"
        fi
    done
else
    echo "  ❌ Archivo .env no encontrado"
fi

# Verificar conectividad de base de datos
echo ""
echo "🗄️  Verificando conectividad de base de datos..."
if command -v psql >/dev/null 2>&1; then
    echo "  ✅ Cliente psql disponible"
    
    # Intentar conexión (sin contraseña, esperará input del usuario si es necesario)
    if timeout 5 psql -h localhost -p 5432 -d documentos_juridicos_gpt4 -U docs_user -c "SELECT COUNT(*) FROM documentos;" 2>/dev/null; then
        echo "  ✅ Conexión a base de datos exitosa"
    else
        echo "  ⚠️  No se pudo verificar conexión automáticamente"
        echo "     Verificar manualmente con: psql -h localhost -p 5432 -d documentos_juridicos_gpt4 -U docs_user"
    fi
else
    echo "  ❌ Cliente psql no disponible"
fi

# Verificar puertos
echo ""
echo "🌐 Verificando puertos..."
if command -v netstat >/dev/null 2>&1; then
    if netstat -tuln | grep -q ":8508"; then
        echo "  ⚠️  Puerto 8508 ya está en uso - puede ser la aplicación ejecutándose"
    else
        echo "  ✅ Puerto 8508 disponible"
    fi
    
    if netstat -tuln | grep -q ":5432"; then
        echo "  ✅ Puerto 5432 (PostgreSQL) activo"
    else
        echo "  ❌ Puerto 5432 (PostgreSQL) no activo"
    fi
else
    echo "  ⚠️  netstat no disponible - verificación de puertos omitida"
fi

# Mostrar resumen
echo ""
echo "📋 RESUMEN DE VERIFICACIÓN:"
echo "=================================================="

if [ $files_missing -eq 0 ]; then
    echo "✅ Estructura de archivos: COMPLETA"
else
    echo "⚠️  Estructura de archivos: $files_missing archivos faltantes"
fi

echo ""
echo "🚀 PARA INICIAR EL SISTEMA:"
echo "1. source venv_docs/bin/activate"
echo "2. streamlit run interfaz_principal.py --server.port 8508 --server.address 0.0.0.0"
echo ""
echo "🌐 ACCESO A LA APLICACIÓN:"
echo "Local:  http://localhost:8508"
echo "Red:    http://10.1.180.13:8508"
echo ""

# Verificar si hay procesos corriendo
echo "🔄 PROCESOS ACTIVOS:"
if pgrep -f "streamlit" >/dev/null; then
    echo "  ✅ Streamlit ejecutándose (PID: $(pgrep -f "streamlit"))"
else
    echo "  ⏸️  Streamlit no está ejecutándose"
fi

if pgrep -f "postgres" >/dev/null; then
    echo "  ✅ PostgreSQL ejecutándose"
else
    echo "  ⚠️  PostgreSQL no detectado"
fi

echo ""
echo "✅ VERIFICACIÓN COMPLETADA"
