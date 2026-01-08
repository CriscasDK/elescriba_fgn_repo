# Instrucciones de Buenas Prácticas de Programación y Desarrollo

## 🎯 **Filosofía de Desarrollo**

Enfoque en **código limpio, mantenible y reutilizable** con documentación completa y arquitectura modular.

---

## 📁 **1. MODULARIZACIÓN Y ARQUITECTURA**

### **Principios de Modularización:**
- **Un módulo = Una responsabilidad específica**
- **Interfaces claras entre módulos**
- **Separación de lógica de negocio y presentación**
- **Reutilización máxima de componentes**

### **Estructura de Módulos Recomendada:**
```
proyecto/
├── src/
│   ├── core/           # Lógica de negocio central
│   ├── modules/        # Módulos especializados
│   ├── utils/          # Utilidades reutilizables
│   ├── interfaces/     # Interfaces y contratos
│   └── config/         # Configuraciones
├── tests/              # Pruebas unitarias
├── docs/               # Documentación
└── scripts/            # Scripts de automatización
```

### **Patrón de Módulos:**
```python
# Cada módulo debe tener:
"""
Título del Módulo
=================

Descripción clara de la funcionalidad.

Ejemplos de uso:
    from modulo import Clase
    instancia = Clase()
    resultado = instancia.metodo()

Autor: [Nombre]
Fecha: [YYYY-MM-DD]
"""

class ModuloEspecializado:
    """Clase con responsabilidad única y bien definida"""
    
    def __init__(self, config: Dict):
        """Constructor con parámetros tipados"""
        pass
    
    def metodo_publico(self) -> ResultType:
        """Método público con documentación clara"""
        return self._metodo_privado()
    
    def _metodo_privado(self) -> ResultType:
        """Método privado para lógica interna"""
        pass
```

---

## 📝 **2. DOCUMENTACIÓN COMPLETA**

### **Niveles de Documentación:**

#### **A. Documentación de Código:**
```python
def funcion_ejemplo(parametro: str, config: Dict[str, Any]) -> Tuple[str, List]:
    """
    Descripción clara de qué hace la función.
    
    Args:
        parametro: Descripción del parámetro
        config: Diccionario de configuración con claves X, Y, Z
    
    Returns:
        Tupla con (resultado_string, lista_elementos)
    
    Raises:
        ValueError: Cuando parametro está vacío
        ConnectionError: Cuando falla la conexión
    
    Example:
        >>> resultado, lista = funcion_ejemplo("test", {"key": "value"})
        >>> print(resultado)
        "procesado: test"
    """
```

#### **B. Documentación de Módulos:**
- **README.md** por módulo explicando propósito y uso
- **API_REFERENCE.md** con métodos públicos
- **CHANGELOG.md** con historial de cambios

#### **C. Documentación de Arquitectura:**
- **ARQUITECTURA.md** con diagramas del sistema
- **FLUJOS_DATOS.md** explicando procesamiento
- **INTEGRACIONES.md** documentando APIs externas

### **Plantilla de README para Módulos:**
```markdown
# Nombre del Módulo

## Propósito
[Una línea explicando para qué sirve]

## Instalación
```bash
pip install -r requirements.txt
```

## Uso Básico
```python
from modulo import ClasePrincipal
# Ejemplo de uso
```

## API Principal
- `metodo1()`: Descripción
- `metodo2()`: Descripción

## Dependencias
- Library1: Para funcionalidad X
- Library2: Para funcionalidad Y
```

---

## 💾 **3. ESTRATEGIA DE RESPALDOS**

### **A. Respaldos de Código:**
```bash
#!/bin/bash
# backup_code.sh - Script de respaldo diario

DATE=$(date +%Y%m%d_%H%M%S)
PROJECT_NAME="documentos_judiciales"
BACKUP_DIR="/backups/code"

# Crear respaldo con git
git bundle create "$BACKUP_DIR/${PROJECT_NAME}_${DATE}.bundle" --all

# Respaldo de archivos de configuración
tar -czf "$BACKUP_DIR/${PROJECT_NAME}_config_${DATE}.tar.gz" \
    .env .env.* *.yml *.yaml *.json requirements.txt

# Rotar respaldos (mantener últimos 30 días)
find $BACKUP_DIR -name "${PROJECT_NAME}_*" -mtime +30 -delete

echo "Respaldo completado: $DATE"
```

### **B. Respaldos de Base de Datos:**
```bash
#!/bin/bash
# backup_db.sh - Respaldo automático de BD

DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="documentos_juridicos_gpt4"
DB_USER="docs_user"
BACKUP_DIR="/backups/database"

# Respaldo completo con estructura y datos
pg_dump -h localhost -p 5432 -U $DB_USER -W $DB_NAME \
    --verbose --clean --no-owner --no-privileges \
    --file="$BACKUP_DIR/backup_${DB_NAME}_${DATE}.sql"

# Comprimir respaldo
gzip "$BACKUP_DIR/backup_${DB_NAME}_${DATE}.sql"

# Rotar respaldos (mantener últimos 7 días completos)
find $BACKUP_DIR -name "backup_${DB_NAME}_*" -mtime +7 -delete

echo "Respaldo BD completado: $DATE"
```

### **C. Respaldos de Configuración del Sistema:**
```bash
#!/bin/bash
# backup_system.sh - Respaldo de configuraciones

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/system"

# Crear directorio de respaldo
mkdir -p "$BACKUP_DIR/$DATE"

# Respaldar configuraciones importantes
cp -r ~/.ssh "$BACKUP_DIR/$DATE/"
cp ~/.bashrc ~/.profile "$BACKUP_DIR/$DATE/"
cp /etc/nginx/sites-available/* "$BACKUP_DIR/$DATE/" 2>/dev/null || true
cp /etc/systemd/system/*.service "$BACKUP_DIR/$DATE/" 2>/dev/null || true

# Comprimir todo
tar -czf "$BACKUP_DIR/system_config_${DATE}.tar.gz" -C "$BACKUP_DIR" "$DATE"
rm -rf "$BACKUP_DIR/$DATE"

echo "Respaldo sistema completado: $DATE"
```

---

## 🔧 **4. GESTIÓN DE CONFIGURACIÓN**

### **A. Variables de Entorno:**
```python
# config/environment.py
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class EnvironmentConfig:
    """Configuración centralizada del entorno"""
    
    # Base de datos
    DB_HOST: str = os.getenv('DB_HOST', 'localhost')
    DB_PORT: int = int(os.getenv('DB_PORT', '5432'))
    DB_NAME: str = os.getenv('DB_NAME', 'documentos_juridicos_gpt4')
    DB_USER: str = os.getenv('DB_USER', 'docs_user')
    DB_PASSWORD: str = os.getenv('DB_PASSWORD', '')
    
    # APIs externas
    AZURE_OPENAI_ENDPOINT: str = os.getenv('AZURE_OPENAI_ENDPOINT', '')
    AZURE_OPENAI_KEY: str = os.getenv('AZURE_OPENAI_KEY', '')
    AZURE_SEARCH_ENDPOINT: str = os.getenv('AZURE_SEARCH_ENDPOINT', '')
    
    # Aplicación
    DEBUG: bool = os.getenv('DEBUG', 'False').lower() == 'true'
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    
    def validate(self) -> bool:
        """Valida que las configuraciones requeridas estén presentes"""
        required = [self.DB_PASSWORD, self.AZURE_OPENAI_KEY]
        return all(required)

# Uso:
config = EnvironmentConfig()
if not config.validate():
    raise ValueError("Configuración incompleta")
```

### **B. Configuración por Archivos:**
```yaml
# config/app.yml
development:
  database:
    pool_size: 5
    timeout: 30
  
  logging:
    level: DEBUG
    format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  
  features:
    enable_debug_panel: true
    enable_profiling: true

production:
  database:
    pool_size: 20
    timeout: 60
  
  logging:
    level: INFO
    format: "%(asctime)s - %(levelname)s - %(message)s"
  
  features:
    enable_debug_panel: false
    enable_profiling: false
```

---

## 🧪 **5. TESTING Y CALIDAD**

### **A. Estructura de Pruebas:**
```python
# tests/test_modulo.py
import pytest
from unittest.mock import Mock, patch
from src.modules.modulo import ClaseAProbar

class TestClaseAProbar:
    """Pruebas para ClaseAProbar"""
    
    def setup_method(self):
        """Configuración antes de cada prueba"""
        self.config = {"test": True}
        self.instancia = ClaseAProbar(self.config)
    
    def test_metodo_basico_caso_exitoso(self):
        """Prueba caso exitoso del método básico"""
        # Arrange
        entrada = "datos_prueba"
        esperado = "resultado_esperado"
        
        # Act
        resultado = self.instancia.metodo_basico(entrada)
        
        # Assert
        assert resultado == esperado
    
    def test_metodo_basico_caso_error(self):
        """Prueba caso de error del método básico"""
        with pytest.raises(ValueError, match="Mensaje específico"):
            self.instancia.metodo_basico("")
    
    @patch('src.modules.modulo.external_api')
    def test_metodo_con_dependencia_externa(self, mock_api):
        """Prueba método que depende de API externa"""
        # Arrange
        mock_api.return_value = {"status": "success"}
        
        # Act
        resultado = self.instancia.metodo_con_api()
        
        # Assert
        assert resultado["status"] == "success"
        mock_api.assert_called_once()
```

### **B. Script de Calidad:**
```bash
#!/bin/bash
# quality_check.sh - Verificaciones de calidad

echo "🔍 Ejecutando verificaciones de calidad..."

# Linting con flake8
echo "📝 Verificando estilo de código..."
flake8 src/ tests/ --max-line-length=100 --ignore=E203,W503

# Type checking con mypy
echo "🏷️  Verificando tipos..."
mypy src/ --ignore-missing-imports

# Pruebas unitarias
echo "🧪 Ejecutando pruebas..."
pytest tests/ -v --cov=src --cov-report=html

# Verificar cobertura mínima
coverage report --fail-under=80

echo "✅ Verificaciones completadas"
```

---

## 📦 **6. GESTIÓN DE DEPENDENCIAS**

### **A. Requirements Organizados:**
```txt
# requirements.txt - Dependencias base
streamlit>=1.28.0
pandas>=1.5.0
psycopg2-binary>=2.9.0
python-dotenv>=1.0.0

# requirements-dev.txt - Dependencias de desarrollo
pytest>=7.0.0
flake8>=5.0.0
mypy>=1.0.0
coverage>=6.0.0
black>=22.0.0

# requirements-prod.txt - Dependencias de producción
gunicorn>=20.0.0
nginx-python>=1.0.0
```

### **B. Gestión de Versiones:**
```python
# version.py
__version__ = "1.2.3"
__author__ = "Equipo Desarrollo"
__license__ = "MIT"

# Registro de cambios en cada versión
CHANGELOG = {
    "1.2.3": [
        "Corregido error en filtros de víctimas",
        "Optimizada consulta de menciones",
        "Agregado manejo de asyncio robusto"
    ],
    "1.2.2": [
        "Implementado gestor de filtros universal",
        "Mejorada modularización del código"
    ]
}
```

---

## 🚀 **7. AUTOMATIZACIÓN Y DEPLOYMENT**

### **A. Script de Deployment:**
```bash
#!/bin/bash
# deploy.sh - Script de despliegue automatizado

set -e  # Salir en caso de error

echo "🚀 Iniciando despliegue..."

# Verificar rama
BRANCH=$(git branch --show-current)
if [ "$BRANCH" != "main" ]; then
    echo "❌ Error: Solo se puede desplegar desde rama 'main'"
    exit 1
fi

# Ejecutar pruebas
echo "🧪 Ejecutando pruebas..."
./quality_check.sh

# Crear respaldo
echo "💾 Creando respaldo..."
./backup_code.sh
./backup_db.sh

# Actualizar dependencias
echo "📦 Actualizando dependencias..."
pip install -r requirements.txt

# Aplicar migraciones de BD
echo "🗄️ Aplicando migraciones..."
python scripts/migrate_db.py

# Reiniciar servicios
echo "🔄 Reiniciando servicios..."
sudo systemctl restart streamlit-app
sudo systemctl restart nginx

echo "✅ Despliegue completado exitosamente"
```

### **B. Monitoreo y Logs:**
```python
# utils/logging_config.py
import logging
import os
from datetime import datetime

def setup_logging(name: str, level: str = "INFO"):
    """Configurar logging estandarizado"""
    
    # Crear directorio de logs
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # Configurar formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Handler para archivo
    file_handler = logging.FileHandler(
        f"{log_dir}/{name}_{datetime.now().strftime('%Y%m%d')}.log"
    )
    file_handler.setFormatter(formatter)
    
    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Configurar logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger
```

---

## 📋 **8. CHECKLIST DE BUENAS PRÁCTICAS**

### **Antes de cada commit:**
- [ ] Código documentado con docstrings
- [ ] Pruebas unitarias escritas y pasando
- [ ] Sin errores de linting (flake8, mypy)
- [ ] Configuraciones en variables de entorno
- [ ] Logs informativos agregados
- [ ] Manejo de errores implementado

### **Antes de cada release:**
- [ ] Respaldo completo creado
- [ ] Documentación actualizada
- [ ] Versión incrementada
- [ ] Changelog actualizado
- [ ] Pruebas de integración ejecutadas
- [ ] Configuración de producción validada

### **Mantenimiento regular:**
- [ ] Respaldos automáticos funcionando
- [ ] Logs monitoreados y rotados
- [ ] Dependencias actualizadas
- [ ] Métricas de performance revisadas
- [ ] Documentación sincronizada con código

---

## 🎯 **RESUMEN DE INSTRUCCIONES PARA IA**

**Cuando trabajes en este proyecto, siempre:**

1. **Modulariza**: Crea funciones/clases con responsabilidad única
2. **Documenta**: Agrega docstrings y comentarios explicativos
3. **Tipifica**: Usa type hints en funciones y métodos
4. **Prueba**: Incluye ejemplos de uso y casos de prueba
5. **Configura**: Usa variables de entorno para configuraciones
6. **Registra**: Agrega logs informativos para debugging
7. **Respald**: Sugiere crear respaldos antes de cambios grandes
8. **Estructura**: Mantén organización clara de archivos y carpetas

**Patrones a seguir:**
- **DRY (Don't Repeat Yourself)**: Reutiliza código
- **SOLID**: Principios de diseño orientado a objetos
- **Clean Code**: Código legible y mantenible
- **Test-Driven**: Considera pruebas desde el diseño

¡Estas instrucciones aseguran un desarrollo robusto y mantenible!