#!/bin/bash
# Script para verificar estado completo del sistema
# Uso: ./estado_sistema.sh

echo "🔍 ESTADO DEL SISTEMA - $(date)"
echo "=================================="

echo "📊 SERVICIOS ACTIVOS:"
echo "- API RAG (8005):" 
curl -s http://localhost:8005 > /dev/null && echo "  ✅ Funcionando" || echo "  ❌ No responde"

echo "- Streamlit 2030:" 
curl -s http://localhost:2030 > /dev/null && echo "  ✅ Funcionando" || echo "  ❌ No responde"

echo "- Streamlit 2031:" 
curl -s http://localhost:2031 > /dev/null && echo "  ✅ Funcionando" || echo "  ❌ No responde"

echo "- PostgreSQL:" 
pg_isready -h localhost -p 5432 > /dev/null && echo "  ✅ Funcionando" || echo "  ❌ No responde"

echo ""
echo "📁 ARCHIVOS MODIFICADOS HOY:"
find . -name "*.py" -newermt "$(date +%Y-%m-%d) 00:00" -exec ls -la {} \; 2>/dev/null | head -10

echo ""
echo "🐳 CONTENEDORES DOCKER:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "  ⚠️ Docker no disponible"

echo ""
echo "💾 ESPACIO EN DISCO:"
df -h . | tail -1

echo ""
echo "📝 ÚLTIMA ACTIVIDAD:"
echo "  - Modificado recientemente: $(find . -name "*.py" -newermt "1 hour ago" | wc -l) archivos Python"
echo "  - Logs recientes: $(find . -name "*.log" -newermt "1 hour ago" | wc -l) archivos"
