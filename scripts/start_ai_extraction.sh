#!/bin/bash
# Script para iniciar extracción de relaciones con IA en background

cd "$(dirname "$0")/.."

echo "=========================================="
echo "🚀 INICIANDO EXTRACCIÓN IA EN BACKGROUND"
echo "=========================================="
echo ""

# Activar entorno virtual
source venv_docs/bin/activate

# Verificar que tenemos API key
if [ -z "$AZURE_OPENAI_API_KEY" ]; then
    echo "❌ ERROR: AZURE_OPENAI_API_KEY no configurada"
    echo "   Cargando desde .env..."
    export $(cat .env | grep AZURE_OPENAI | xargs)
fi

# Crear directorio de logs si no existe
mkdir -p logs

# Timestamp para identificar esta ejecución
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="logs/ai_extraction_${TIMESTAMP}.log"
PID_FILE="logs/ai_extraction.pid"

echo "📝 Log file: $LOG_FILE"
echo "🆔 PID file: $PID_FILE"
echo ""

# Confirmar con el usuario
echo "⚠️  ADVERTENCIA:"
echo "   - Esto procesará ~11,111 documentos"
echo "   - Costo estimado: ~$589 USD"
echo "   - Tiempo estimado: ~9-10 horas"
echo ""
read -p "¿Continuar? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Cancelado por usuario"
    exit 1
fi

echo ""
echo "🚀 Iniciando procesamiento..."

# Ejecutar en background con nohup
nohup python scripts/extract_relations_with_ai_batch.py \
    --batch-size 100 \
    --rate-limit 0.5 \
    > "$LOG_FILE" 2>&1 &

# Guardar PID
echo $! > "$PID_FILE"

echo "✅ Proceso iniciado con PID: $(cat $PID_FILE)"
echo ""
echo "📊 Para monitorear el progreso:"
echo "   ./scripts/monitor_ai_extraction.sh"
echo ""
echo "🛑 Para detener el proceso:"
echo "   kill $(cat $PID_FILE)"
echo ""
echo "📄 Ver logs en tiempo real:"
echo "   tail -f $LOG_FILE"
echo ""
