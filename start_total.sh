#!/bin/bash

set -euo pipefail

# ==============================================
# Script de arranque completo (backend + frontend)
# ==============================================

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BASE_DIR"

BACKEND_PORT=${BACKEND_PORT:-8010}
FRONTEND_PORT=${FRONTEND_PORT:-8050}

BACKEND_LOG="logs/rag_api.log"
FRONTEND_LOG="logs/app_dash.log"

echo -e "${BLUE}🚀 Inicializando stack completo (backend + frontend)${NC}"

require_file() {
    local file="$1"
    local message="$2"
    [[ -f "$file" ]] || { echo -e "${RED}❌ $message${NC}"; exit 1; }
}

check_port() {
    local port="$1"
    if lsof -Pi :"$port" -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${RED}❌ Puerto $port en uso. Libéralo antes de continuar.${NC}"
        exit 1
    else
        echo -e "${GREEN}✅ Puerto $port disponible${NC}"
    fi
}

ensure_virtualenv() {
    if [[ -z "${VIRTUAL_ENV:-}" ]]; then
        local venv_path="$BASE_DIR/venv_docs/bin/activate"
        [[ -f "$venv_path" ]] || { echo -e "${RED}❌ No se encontró el ambiente virtual venv_docs${NC}"; exit 1; }
        echo -e "${BLUE}🔧 Activando ambiente virtual (venv_docs)${NC}"
        # shellcheck disable=SC1090
        source "$venv_path"
    else
        echo -e "${GREEN}✅ Ambiente virtual activo (${VIRTUAL_ENV})${NC}"
    fi
}

load_env() {
    local env_file=".env"
    if [[ -f ".env.gpt41" ]]; then
        env_file=".env.gpt41"
    fi

    if [[ -f "$env_file" ]]; then
        echo -e "${BLUE}📦 Cargando variables desde $env_file${NC}"
        # shellcheck disable=SC1090
        set -a
        source "$env_file"
        set +a
    else
        echo -e "${YELLOW}⚠️  No se encontró archivo .env; continuando con variables actuales${NC}"
    fi
}

start_backend() {
    echo -e "${BLUE}🌐 Iniciando backend FastAPI (puerto $BACKEND_PORT)${NC}"
    nohup uvicorn src.api.rag_api:app --host 0.0.0.0 --port "$BACKEND_PORT" \
        > "$BACKEND_LOG" 2>&1 &
    BACKEND_PID=$!
    sleep 2
    if ! ps -p "$BACKEND_PID" >/dev/null 2>&1; then
        echo -e "${RED}❌ Backend no pudo iniciarse. Revisa $BACKEND_LOG${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Backend listo (PID $BACKEND_PID)${NC}"
}

start_frontend() {
    echo -e "${BLUE}🖥️  Iniciando frontend Dash (puerto $FRONTEND_PORT)${NC}"
    nohup python -c "from app_dash import app; app.run(host='0.0.0.0', port=$FRONTEND_PORT, debug=False)" \
        > "$FRONTEND_LOG" 2>&1 &
    FRONTEND_PID=$!
    sleep 2
    if ! ps -p "$FRONTEND_PID" >/dev/null 2>&1; then
        echo -e "${RED}❌ Frontend no pudo iniciarse. Revisa $FRONTEND_LOG${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Frontend listo (PID $FRONTEND_PID)${NC}"
}

create_stop_script() {
    cat > stop_total.sh <<EOF
#!/bin/bash
echo "🛑 Deteniendo servicios backend/frontend..."
kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
echo "✅ Servicios detenidos"
EOF
    chmod +x stop_total.sh
    echo -e "${BLUE}📝 Usa ./stop_total.sh para detener los servicios${NC}"
}

require_file "app_dash.py" "Ejecuta el script desde la raíz del proyecto (app_dash.py no encontrado)."
require_file "src/api/rag_api.py" "No se encontró src/api/rag_api.py"

mkdir -p logs

ensure_virtualenv
load_env

check_port "$BACKEND_PORT"
check_port "$FRONTEND_PORT"

start_backend
start_frontend

create_stop_script

echo ""
echo -e "${GREEN}🎉 Sistema arriba y corriendo${NC}"
echo -e "${BLUE}📍 Backend:  http://localhost:$BACKEND_PORT${NC}"
echo -e "${BLUE}🖥️  Frontend: http://localhost:$FRONTEND_PORT${NC}"
echo -e "${BLUE}📚 Docs API: http://localhost:$BACKEND_PORT/docs${NC}"
echo ""
echo -e "${BLUE}🔍 Logs:${NC}"
echo "   tail -f $BACKEND_LOG"
echo "   tail -f $FRONTEND_LOG"
echo ""
