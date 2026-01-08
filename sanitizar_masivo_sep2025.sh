#!/bin/bash
# 🧹 SCRIPT DE SANITIZACIÓN MASIVA - SEPTIEMBRE 2025
# Limpia el proyecto de documentos judiciales eliminando archivos redundantes

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧹 INICIANDO SANITIZACIÓN MASIVA DEL PROYECTO${NC}"
echo -e "${YELLOW}Fecha: $(date)${NC}"
echo ""

# Función para mostrar progreso
show_progress() {
    echo -e "${GREEN}✅ $1${NC}"
}

show_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

show_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Verificar que estamos en el directorio correcto
if [[ ! -f "interfaz_principal.py" ]]; then
    show_error "Error: No se encuentra interfaz_principal.py. Ejecuta desde la raíz del proyecto."
    exit 1
fi

# Crear backup de seguridad antes de la limpieza
BACKUP_DIR="backup_pre_sanitizacion_$(date +%Y%m%d_%H%M%S)"
show_warning "Creando backup de seguridad en $BACKUP_DIR..."
mkdir -p "$BACKUP_DIR"

# Backup de archivos críticos
cp interfaz_principal.py "$BACKUP_DIR/"
cp -r src/ "$BACKUP_DIR/" 2>/dev/null || true
cp -r config/ "$BACKUP_DIR/" 2>/dev/null || true
cp requirements.txt "$BACKUP_DIR/" 2>/dev/null || true
cp .env "$BACKUP_DIR/" 2>/dev/null || true

show_progress "Backup de seguridad creado"

echo ""
echo -e "${BLUE}🗂️  FASE 1: ELIMINAR ARCHIVOS REDUNDANTES${NC}"

# 1. Eliminar backups antiguos
show_warning "Eliminando backups redundantes..."
rm -f backup_*.tar.gz 2>/dev/null || true
rm -rf backup_*/ 2>/dev/null || true
show_progress "Backups eliminados"

# 2. Eliminar tests obsoletos y debug
show_warning "Eliminando tests y scripts de debug..."
rm -f test_*.py 2>/dev/null || true
rm -f debug_*.py 2>/dev/null || true
rm -f verificar_*.py 2>/dev/null || true
rm -f analizar_*.py 2>/dev/null || true
show_progress "Scripts de test/debug eliminados"

# 3. Eliminar documentación redundante
show_warning "Eliminando documentación redundante..."
rm -f ESTADO_*.md 2>/dev/null || true
rm -f RESUMEN_*.md 2>/dev/null || true
rm -f ACTUALIZACION_*.md 2>/dev/null || true
rm -f HITO_*.md 2>/dev/null || true
rm -f PROCESO_*.md 2>/dev/null || true
rm -f REGISTRO_*.md 2>/dev/null || true
rm -f REPORTE_*.md 2>/dev/null || true
rm -f UNIFICACION_*.md 2>/dev/null || true
rm -f FILTROS_*.md 2>/dev/null || true
show_progress "Documentación redundante eliminada"

# 4. Limpiar cache y temporales
show_warning "Eliminando archivos temporales..."
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "*.log" -delete 2>/dev/null || true
rm -rf logs/ 2>/dev/null || true
rm -rf cache/ 2>/dev/null || true
show_progress "Archivos temporales eliminados"

echo ""
echo -e "${BLUE}🔗 FASE 2: CONSOLIDAR ARCHIVOS DUPLICADOS${NC}"

# 5. Eliminar interfaces redundantes
show_warning "Eliminando interfaces redundantes..."
rm -f interfaz_fiscales.py 2>/dev/null || true
rm -f interfaz_rag_vectorizada.py 2>/dev/null || true
rm -f interfaz_simple_api.py 2>/dev/null || true
rm -f mejoras_interfaz_rag.py 2>/dev/null || true
show_progress "Interfaces redundantes eliminadas"

# 6. Consolidar requirements
show_warning "Consolidando requirements..."
rm -f requirements_*.txt 2>/dev/null || true
rm -f api_requirements.txt 2>/dev/null || true
rm -f requirements_api.txt 2>/dev/null || true
rm -f requirements_chatbot.txt 2>/dev/null || true
rm -f requirements-frontend.txt 2>/dev/null || true
show_progress "Requirements consolidados"

# 7. Eliminar scripts obsoletos
show_warning "Eliminando scripts obsoletos..."
rm -f clasificador_*.py 2>/dev/null || true
rm -f consultor_*.py 2>/dev/null || true
rm -f comparacion_*.py 2>/dev/null || true
rm -f vectorizacion_*.py 2>/dev/null || true
rm -f monitor_*.py 2>/dev/null || true
rm -f procesar_*.py 2>/dev/null || true
show_progress "Scripts obsoletos eliminados"

# 8. Limpiar archivos SQL redundantes
show_warning "Eliminando archivos SQL redundantes..."
rm -f fix_*.sql 2>/dev/null || true
rm -f consulta_*.sql 2>/dev/null || true
rm -f consultas_*.sql 2>/dev/null || true
rm -f verificacion_*.sql 2>/dev/null || true
rm -f migracion_*.sql 2>/dev/null || true
show_progress "Archivos SQL redundantes eliminados"

echo ""
echo -e "${BLUE}🗂️  FASE 3: LIMPIAR CARPETAS INNECESARIAS${NC}"

# 9. Eliminar carpetas innecesarias
show_warning "Eliminando carpetas innecesarias..."
rm -rf archive/ 2>/dev/null || true
rm -rf json_files/ 2>/dev/null || true
rm -rf poblar_tablas/ 2>/dev/null || true
rm -rf templates/ 2>/dev/null || true
rm -rf scripts/ 2>/dev/null || true
rm -rf backups/ 2>/dev/null || true
show_progress "Carpetas innecesarias eliminadas"

# 10. Limpiar archivos sueltos
show_warning "Eliminando archivos sueltos..."
rm -f *.ipynb 2>/dev/null || true
rm -f tatus 2>/dev/null || true
rm -f "_password_*" 2>/dev/null || true
rm -f "documentos_con_datos," 2>/dev/null || true
rm -f *.sh 2>/dev/null || true
show_progress "Archivos sueltos eliminados"

echo ""
echo -e "${BLUE}📊 ESTADÍSTICAS FINALES${NC}"

# Mostrar estadísticas post-limpieza
ARCHIVOS_PYTHON=$(find . -name "*.py" 2>/dev/null | wc -l)
ARCHIVOS_MD=$(find . -name "*.md" 2>/dev/null | wc -l)
TAMANO_FINAL=$(du -sh . 2>/dev/null | cut -f1)

echo -e "${GREEN}✅ LIMPIEZA COMPLETADA${NC}"
echo ""
echo -e "${BLUE}📈 Estadísticas finales:${NC}"
echo -e "  📄 Archivos Python: $ARCHIVOS_PYTHON"
echo -e "  📚 Archivos MD: $ARCHIVOS_MD"
echo -e "  💾 Tamaño total: $TAMANO_FINAL"
echo ""
echo -e "${YELLOW}🔄 Archivos esenciales mantenidos:${NC}"
echo -e "  ✅ interfaz_principal.py"
echo -e "  ✅ src/core/ (módulos fundamentales)"
echo -e "  ✅ config/ (configuración)"
echo -e "  ✅ venv/ (ambiente virtual)"
echo -e "  ✅ requirements.txt"
echo ""
echo -e "${GREEN}🎯 Proyecto sanitizado exitosamente!${NC}"
echo -e "${BLUE}📁 Backup disponible en: $BACKUP_DIR${NC}"
echo ""
echo -e "${YELLOW}⚠️  PRÓXIMOS PASOS:${NC}"
echo -e "  1. Verificar que la aplicación funciona: streamlit run interfaz_principal.py"
echo -e "  2. Si hay problemas, restaurar desde: $BACKUP_DIR"
echo -e "  3. Eliminar backup cuando confirmes que todo funciona"
echo ""