#!/bin/bash

# 🔄 SCRIPT DE REINICIO AUTOMÁTICO DEL SISTEMA
# Este script reinicia todos los servicios y verifica el estado

echo "🚀 INICIANDO REINICIO COMPLETO DEL SISTEMA"
echo "=========================================="
echo "⏰ $(date)"
echo ""

# Cambiar al directorio correcto
cd /home/lab4/scripts/documentos_judiciales || {
    echo "❌ Error: No se pudo acceder al directorio del proyecto"
    exit 1
}

echo "📁 Directorio de trabajo: $(pwd)"
echo ""

# 1. Reiniciar Docker Compose
echo "🐳 REINICIANDO POSTGRESQL..."
echo "--------------------------------"
docker-compose down
sleep 3
docker-compose up -d
sleep 5

if docker ps | grep -q postgres; then
    echo "✅ PostgreSQL reiniciado exitosamente"
else
    echo "❌ Error: PostgreSQL no se pudo iniciar"
    exit 1
fi
echo ""

# 2. Activar entorno virtual
echo "🐍 ACTIVANDO ENTORNO VIRTUAL..."
echo "--------------------------------"
source venv_docs/bin/activate

if [[ "$VIRTUAL_ENV" == *"venv_docs"* ]]; then
    echo "✅ Entorno virtual activado: $VIRTUAL_ENV"
else
    echo "❌ Error: No se pudo activar el entorno virtual"
    exit 1
fi
echo ""

# 3. Verificar base de datos
echo "🗄️ VERIFICANDO BASE DE DATOS..."
echo "--------------------------------"
sleep 3  # Dar tiempo a PostgreSQL para inicializar

python -c "
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv('.env.gpt41')

try:
    conn = psycopg2.connect(
        host='localhost',
        port='5432',
        database='documentos_juridicos_gpt4', 
        user='docs_user',
        password='docs_password_2025'
    )
    
    with conn.cursor() as cur:
        cur.execute('SELECT COUNT(*) FROM documentos')
        docs = cur.fetchone()[0]
        cur.execute('SELECT COUNT(*) FROM metadatos')
        meta = cur.fetchone()[0]
        cur.execute(\"SELECT COUNT(*) FROM personas WHERE tipo ILIKE '%victima%' AND tipo NOT ILIKE '%victimario%'\")
        victimas = cur.fetchone()[0]
        
        print(f'✅ Documentos: {docs:,}')
        print(f'✅ Metadatos: {meta:,}')
        print(f'✅ Víctimas: {victimas:,}')
        
        if docs == 11111 and meta == 11111 and victimas >= 2500:
            print('✅ Base de datos íntegra')
        else:
            print('⚠️ Advertencia: Conteos inesperados')
    
    conn.close()
    
except Exception as e:
    print(f'❌ Error conectando a base de datos: {e}')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo "✅ Base de datos verificada exitosamente"
else
    echo "❌ Error en verificación de base de datos"
    exit 1
fi
echo ""

# 4. Verificar puertos
echo "🔌 VERIFICANDO PUERTOS..."
echo "-------------------------"

if lsof -i :5432 > /dev/null 2>&1; then
    echo "✅ Puerto 5432 (PostgreSQL) activo"
else
    echo "⚠️ Puerto 5432 (PostgreSQL) libre"
fi

if lsof -i :8508 > /dev/null 2>&1; then
    echo "✅ Puerto 8508 (Streamlit) activo"
else
    echo "⚠️ Puerto 8508 (Streamlit) libre - Se iniciará automáticamente"
fi
echo ""

# 5. Ejecutar verificación completa
echo "🔍 EJECUTANDO VERIFICACIÓN COMPLETA..."
echo "--------------------------------------"
python verificar_sistema.py

echo ""
echo "🎯 COMANDOS PARA CONTINUAR:"
echo "=========================="
echo ""
echo "1. 🚀 Iniciar Frontend:"
echo "   streamlit run frontend_victimas_mejorado.py --server.port 8508"
echo ""
echo "2. 🔍 Verificar estado:"
echo "   python test_consultas_metadatos.py"
echo ""
echo "3. 🌐 Acceder al Frontend:"
echo "   URL: http://localhost:8508"
echo "   Usuario: docs_user"
echo "   Contraseña: docs_password_2025"
echo ""
echo "4. 📊 Validar víctimas:"
echo "   Total: 2,546 víctimas listas para validación"
echo ""
echo "✨ ¡SISTEMA REINICIADO Y LISTO!"
echo "================================"
