#!/bin/bash

# Script unificado para lanzar todos los servicios del sistema
# Autor: Rodrigo Bazurto - 21 Agosto 2025

echo "🚀 Iniciando Sistema Completo de Documentos Judiciales..."
echo "======================================================"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para verificar si un puerto está libre
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${RED}❌ Puerto $port está ocupado${NC}"
        return 1
    else
        echo -e "${GREEN}✅ Puerto $port está libre${NC}"
        return 0
    fi
}

# Función para esperar que un servicio esté listo
wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=1
    
    echo -e "${YELLOW}⏳ Esperando que $name esté listo...${NC}"
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $name está listo${NC}"
            return 0
        fi
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo -e "${RED}❌ Timeout esperando $name${NC}"
    return 1
}

# Verificar directorio
if [ ! -f "interfaz_principal.py" ]; then
    echo -e "${RED}❌ Error: Ejecutar desde el directorio raíz del proyecto${NC}"
    exit 1
fi

# Verificar ambiente virtual
if [ ! -d "venv_docs" ]; then
    echo -e "${RED}❌ Error: No se encontró ambiente virtual venv_docs${NC}"
    exit 1
fi

# Activar ambiente virtual
echo -e "${BLUE}🔧 Activando ambiente virtual...${NC}"
source venv_docs/bin/activate

# Verificar archivo .env
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ Error: No se encontró archivo .env${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Ambiente virtual activado${NC}"

# Verificar puertos
echo -e "${BLUE}🔍 Verificando puertos disponibles...${NC}"
check_port 8001 || { echo "Usar: kill \$(lsof -t -i:8001)"; exit 1; }
check_port 8502 || { echo "Usar: kill \$(lsof -t -i:8502)"; exit 1; }
check_port 8503 || { echo "Usar: kill \$(lsof -t -i:8503)"; exit 1; }

# Crear directorio de logs si no existe
mkdir -p logs

echo ""
echo -e "${BLUE}🚀 Iniciando servicios...${NC}"
echo ""

# 1. Lanzar API RAG (Puerto 8001)
echo -e "${YELLOW}1️⃣ Iniciando API RAG (Puerto 8001)...${NC}"
nohup uvicorn src.api.rag_api:app --host 0.0.0.0 --port 8001 > logs/rag_api.log 2>&1 &
RAG_API_PID=$!
echo "   PID: $RAG_API_PID"

# 2. Lanzar Interfaz Principal - Víctimas (Puerto 8502)
echo -e "${YELLOW}2️⃣ Iniciando Interfaz Principal - Víctimas (Puerto 8502)...${NC}"
nohup streamlit run interfaz_principal.py --server.port 8502 --server.address 0.0.0.0 > logs/interfaz_principal.log 2>&1 &
INTERFAZ_PID=$!
echo "   PID: $INTERFAZ_PID"

# 3. Lanzar Interfaz de Pruebas RAG (Puerto 8503)
echo -e "${YELLOW}3️⃣ Iniciando Interfaz de Pruebas RAG (Puerto 8503)...${NC}"
nohup streamlit run src/api/streamlit_app.py --server.port 8503 --server.address 0.0.0.0 > logs/streamlit_rag.log 2>&1 &
RAG_STREAMLIT_PID=$!
echo "   PID: $RAG_STREAMLIT_PID"

echo ""
echo -e "${BLUE}⏳ Esperando que los servicios estén listos...${NC}"
sleep 5

# Verificar servicios
echo ""
echo -e "${BLUE}🔍 Verificando servicios...${NC}"

wait_for_service "http://localhost:8001/health" "API RAG"
wait_for_service "http://localhost:8502" "Interfaz Principal"
wait_for_service "http://localhost:8503" "Interfaz RAG"

echo ""
echo -e "${GREEN}🎉 ¡Todos los servicios están funcionando!${NC}"
echo "======================================================"
echo ""
echo -e "${BLUE}📋 URLs de Acceso:${NC}"
echo "   🏛️  Interfaz Principal (Víctimas): http://localhost:8502"
echo "   🧪 Interfaz de Pruebas RAG:        http://localhost:8503"
echo "   🚀 API REST:                       http://localhost:8001"
echo "   📖 Documentación API:              http://localhost:8001/docs"
echo ""
echo -e "${BLUE}📊 PIDs de Procesos:${NC}"
echo "   API RAG:           $RAG_API_PID"
echo "   Interfaz Principal: $INTERFAZ_PID"
echo "   Interfaz RAG:      $RAG_STREAMLIT_PID"
echo ""
echo -e "${BLUE}📝 Logs:${NC}"
echo "   API RAG:           tail -f logs/rag_api.log"
echo "   Interfaz Principal: tail -f logs/interfaz_principal.log"
echo "   Interfaz RAG:      tail -f logs/streamlit_rag.log"
echo ""
echo -e "${YELLOW}🛑 Para detener todos los servicios:${NC}"
echo "   kill $RAG_API_PID $INTERFAZ_PID $RAG_STREAMLIT_PID"
echo "   O usar: ./stop_all_services.sh"
echo ""

# Crear script de parada
cat > stop_all_services.sh << EOF
#!/bin/bash
echo "🛑 Deteniendo todos los servicios..."
kill $RAG_API_PID $INTERFAZ_PID $RAG_STREAMLIT_PID 2>/dev/null
echo "✅ Servicios detenidos"
rm -f stop_all_services.sh
EOF

chmod +x stop_all_services.sh

echo -e "${GREEN}✨ Sistema listo para usar. ¡Happy coding!${NC}"
echo ""

# Probar API con consulta de ejemplo
echo -e "${BLUE}🧪 Probando API con consulta de ejemplo...${NC}"
sleep 3

curl -s -X POST "http://localhost:8001/rag/consulta" \
     -H "Content-Type: application/json" \
     -d '{
       "pregunta": "¿Cuántas víctimas de la Unión Patriótica están documentadas?",
       "usuario_id": "sistema_startup"
     }' | jq -r '.texto' 2>/dev/null | head -2 || echo "API disponible (instalar jq para ver respuesta)"

echo ""
echo -e "${GREEN}🚀 Sistema completamente operativo${NC}"
