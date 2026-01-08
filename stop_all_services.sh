#!/bin/bash
echo "🛑 Deteniendo todos los servicios..."
kill 2748620 2748621 2748622 2>/dev/null
echo "✅ Servicios detenidos"
rm -f stop_all_services.sh
