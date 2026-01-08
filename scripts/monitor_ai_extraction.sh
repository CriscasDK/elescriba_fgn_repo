#!/bin/bash
# Script para monitorear el progreso de la extracción IA

cd "$(dirname "$0")/.."

PID_FILE="logs/ai_extraction.pid"
CHECKPOINT_FILE="logs/extraction_checkpoint.json"

clear

echo "=========================================="
echo "📊 MONITOR DE EXTRACCIÓN IA"
echo "=========================================="
echo ""

# Verificar si está corriendo
if [ ! -f "$PID_FILE" ]; then
    echo "❌ No hay proceso activo (no se encontró $PID_FILE)"
    exit 1
fi

PID=$(cat "$PID_FILE")

if ! ps -p $PID > /dev/null 2>&1; then
    echo "⚠️  El proceso PID $PID no está corriendo"
    echo "   (Puede haber terminado o fallado)"
    rm -f "$PID_FILE"
    exit 1
fi

echo "✅ Proceso activo: PID $PID"
echo ""

# Leer checkpoint si existe
if [ -f "$CHECKPOINT_FILE" ]; then
    echo "📌 CHECKPOINT ACTUAL:"
    python3 -c "
import json
import sys
try:
    with open('$CHECKPOINT_FILE', 'r') as f:
        data = json.load(f)
    print(f\"   Último documento procesado: {data.get('last_document_id', 'N/A')}\" )
    print(f\"   Timestamp: {data.get('timestamp', 'N/A')}\")
    stats = data.get('stats', {})
    if stats:
        print(f\"   Documentos procesados: {stats.get('documentos_procesados', 0):,}\")
        print(f\"   Relaciones extraídas: {stats.get('relaciones_extraidas', 0):,}\")
        print(f\"   Llamadas API: {stats.get('llamadas_api', 0):,}\")
        print(f\"   Tokens usados: {stats.get('tokens_usados', 0):,}\")
        cost = stats.get('tokens_usados', 0) * 0.03 / 1000
        print(f\"   Costo acumulado: \${cost:.2f} USD\")
except Exception as e:
    print(f\"   Error leyendo checkpoint: {e}\")
"
    echo ""
fi

# Estadísticas de BD en tiempo real
echo "📊 ESTADÍSTICAS EN BASE DE DATOS:"
source venv_docs/bin/activate
python3 -c "
import sys
sys.path.insert(0, '.')
from core.consultas import get_db_connection

conn = get_db_connection()
cur = conn.cursor()

# Total procesados con IA
cur.execute('''
    SELECT COUNT(DISTINCT documento_id)
    FROM relaciones_extraidas
    WHERE metodo_extraccion = \"gpt4_from_analisis\"
''')
procesados = cur.fetchone()[0]

# Total relaciones insertadas
cur.execute('''
    SELECT COUNT(*)
    FROM relaciones_extraidas
    WHERE metodo_extraccion = \"gpt4_from_analisis\"
''')
relaciones = cur.fetchone()[0]

# Total pendientes
cur.execute('''
    SELECT COUNT(*)
    FROM documentos
    WHERE analisis IS NOT NULL AND LENGTH(analisis) > 100
''')
total = cur.fetchone()[0]

pendientes = total - procesados
progreso = (procesados / total * 100) if total > 0 else 0

print(f'   Total documentos: {total:,}')
print(f'   Procesados: {procesados:,}')
print(f'   Pendientes: {pendientes:,}')
print(f'   Progreso: {progreso:.1f}%')
print(f'   Relaciones totales: {relaciones:,}')

cur.close()
conn.close()
"

echo ""
echo "📄 ÚLTIMAS LÍNEAS DEL LOG:"
echo "----------------------------------------"
tail -20 logs/ai_extraction_*.log | tail -10
echo "----------------------------------------"

echo ""
echo "💡 COMANDOS ÚTILES:"
echo "   Ver log completo:     tail -f logs/ai_extraction_*.log"
echo "   Detener proceso:      kill $PID"
echo "   Ver este monitor:     watch -n 10 ./scripts/monitor_ai_extraction.sh"
echo ""
