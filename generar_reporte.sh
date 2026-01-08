#!/bin/bash

# Script para generar reporte de víctimas sin problemas de terminal
echo "🚀 Ejecutando reporte de víctimas..."

cd /home/lab4/scripts/documentos_judiciales

# Activar entorno virtual y ejecutar script
source venv_docs/bin/activate
python reporte_victimas_simple.py

echo "✅ Reporte generado. Revisa los archivos .txt en el directorio actual."
ls -la reporte_victimas_*.txt
