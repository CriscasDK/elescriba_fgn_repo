#!/bin/bash

# ========================================
# FIX AGE "OUT OF SHARED MEMORY" ERROR
# ========================================
#
# Problema: AGE falla con "out of shared memory"
# Solución: Aumentar max_locks_per_transaction de 64 a 256
#
# Fecha: 03 Octubre 2025
# ========================================

echo "🔧 Iniciando fix de AGE memory error..."
echo ""

# Verificar que se ejecuta como root o con sudo
if [ "$EUID" -ne 0 ]; then
    echo "❌ Error: Este script necesita ejecutarse con sudo"
    echo "   Uso: sudo bash $0"
    exit 1
fi

echo "✅ Ejecutando como superusuario"
echo ""

# Paso 1: Verificar valor actual
echo "📊 Paso 1/4: Verificando valor actual de max_locks_per_transaction..."
CURRENT_VALUE=$(su - postgres -c "psql -t -c 'SHOW max_locks_per_transaction;'" | tr -d ' ')
echo "   Valor actual: $CURRENT_VALUE"
echo ""

# Paso 2: Aplicar cambio
echo "🔧 Paso 2/4: Aumentando max_locks_per_transaction a 256..."
su - postgres -c "psql -c \"ALTER SYSTEM SET max_locks_per_transaction = 256;\""

if [ $? -eq 0 ]; then
    echo "   ✅ Cambio aplicado correctamente"
else
    echo "   ❌ Error al aplicar cambio"
    exit 1
fi
echo ""

# Paso 3: Recargar configuración
echo "🔄 Paso 3/4: Recargando configuración de PostgreSQL..."
echo "   Opciones:"
echo "   A) Reload (sin interrupción, pero algunos parámetros requieren restart)"
echo "   B) Restart (interrumpe conexiones activas, pero garantiza aplicación)"
echo ""
read -p "   Selecciona opción [A/B] (default: B): " OPTION
OPTION=${OPTION:-B}

if [ "$OPTION" = "A" ] || [ "$OPTION" = "a" ]; then
    echo "   Ejecutando reload..."
    su - postgres -c "psql -c 'SELECT pg_reload_conf();'"
    echo "   ⚠️ Nota: max_locks_per_transaction requiere RESTART para aplicarse"
    echo "   Si los grafos siguen fallando, ejecuta: sudo systemctl restart postgresql"
else
    echo "   Ejecutando restart..."
    systemctl restart postgresql

    if [ $? -eq 0 ]; then
        echo "   ✅ PostgreSQL reiniciado correctamente"
    else
        echo "   ❌ Error al reiniciar PostgreSQL"
        exit 1
    fi
fi
echo ""

# Paso 4: Verificar nuevo valor
echo "✅ Paso 4/4: Verificando nuevo valor..."
sleep 2  # Esperar a que PostgreSQL esté listo
NEW_VALUE=$(su - postgres -c "psql -t -c 'SHOW max_locks_per_transaction;'" | tr -d ' ')
echo "   Valor nuevo: $NEW_VALUE"
echo ""

# Resumen
echo "=========================================="
echo "📋 RESUMEN"
echo "=========================================="
echo "Valor anterior: $CURRENT_VALUE"
echo "Valor nuevo:    $NEW_VALUE"
echo ""

if [ "$NEW_VALUE" = "256" ]; then
    echo "✅ FIX APLICADO EXITOSAMENTE"
    echo ""
    echo "🎯 PRÓXIMOS PASOS:"
    echo "1. Verificar que Dash app está corriendo:"
    echo "   ps aux | grep 'python.*app_dash'"
    echo ""
    echo "2. Si no está corriendo, iniciar:"
    echo "   cd /home/lab4/scripts/documentos_judiciales"
    echo "   python app_dash.py &"
    echo ""
    echo "3. Abrir en navegador:"
    echo "   http://0.0.0.0:8050/"
    echo ""
    echo "4. Probar:"
    echo "   - Hacer consulta: 'quien es Oswaldo Olivo?'"
    echo "   - Click en botón 🌐"
    echo "   - Verificar que aparece grafo 3D"
    echo ""
    echo "5. Revisar logs para confirmar sin errores:"
    echo "   tail -f /home/lab4/scripts/documentos_judiciales/dash_app_all.log"
    echo ""
else
    echo "⚠️ WARNING: El valor no cambió a 256"
    echo "   Puede que necesites reiniciar PostgreSQL manualmente:"
    echo "   sudo systemctl restart postgresql"
    echo ""
    echo "   Luego verificar de nuevo:"
    echo "   sudo -u postgres psql -c 'SHOW max_locks_per_transaction;'"
fi

echo "=========================================="
echo ""
echo "📚 Documentación relacionada:"
echo "- ESTADO_ACTUAL_GRAFOS.md (resumen ejecutivo)"
echo "- TROUBLESHOOTING_GRAFOS.md (guía de troubleshooting)"
echo "- SESION_GRAFOS_INLINE_03OCT2025.md (documentación técnica completa)"
echo ""

exit 0
