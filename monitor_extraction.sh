#!/bin/bash
# Monitor LLM extraction progress

cd /home/lab4/scripts/documentos_judiciales
source venv_docs/bin/activate

while true; do
    clear
    echo "=========================================="
    echo "MONITOREO DE EXTRACCIÓN LLM"
    echo "=========================================="
    echo ""

    python -c "
from core.consultas import get_db_connection
conn = get_db_connection()
cur = conn.cursor()

# Total relaciones extraídas
cur.execute(\"SELECT COUNT(*) FROM relaciones_extraidas WHERE metodo_extraccion = 'azure_gpt41_extraction'\")
total_rel = cur.fetchone()[0]

# Documentos totales a procesar
cur.execute('SELECT COUNT(*) FROM documentos WHERE analisis IS NOT NULL AND LENGTH(analisis) > 100')
total_docs = cur.fetchone()[0]

# Estimación de documentos procesados (asumiendo 3.48 relaciones por doc como en el test)
docs_procesados = int(total_rel / 3.48) if total_rel > 0 else 0

# Progreso
progreso = (docs_procesados / total_docs * 100) if total_docs > 0 else 0

print(f'📊 Total documentos a procesar:  {total_docs:,}')
print(f'✅ Documentos procesados (est):   {docs_procesados:,} ({progreso:.1f}%)')
print(f'🔗 Relaciones extraídas:          {total_rel:,}')
print(f'📈 Promedio relaciones/doc:       {total_rel/docs_procesados:.2f}' if docs_procesados > 0 else '📈 Promedio relaciones/doc:       N/A')

# Últimas 5 relaciones
print()
print('📝 Últimas 5 relaciones extraídas:')
print('='*70)
cur.execute(\"\"\"
    SELECT entidad_origen, tipo_relacion, entidad_destino, created_at
    FROM relaciones_extraidas
    WHERE metodo_extraccion = 'azure_gpt41_extraction'
    ORDER BY created_at DESC
    LIMIT 5
\"\"\")

for origen, tipo, destino, created_at in cur.fetchall():
    origen_short = (origen[:25] + '...') if len(origen) > 28 else origen
    destino_short = (destino[:25] + '...') if len(destino) > 28 else destino
    print(f'  {origen_short:28} --[{tipo:15}]--> {destino_short}')

cur.close()
conn.close()
"

    echo ""
    echo "=========================================="
    echo "Actualizando en 30 segundos... (Ctrl+C para salir)"
    echo "=========================================="
    sleep 30
done
