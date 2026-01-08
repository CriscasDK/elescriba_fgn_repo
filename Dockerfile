# Imagen base de Python 3.11 slim para optimizar tamaño
FROM python:3.11-slim

# Configurar directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias para psycopg2 y otras librerías
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de dependencias
COPY requirements.txt .
COPY api_requirements.txt .

# Crear requirements consolidado para contenedor
RUN echo "# Dependencias principales para aplicación Dash" > requirements_docker.txt && \
    echo "dash==2.17.1" >> requirements_docker.txt && \
    echo "dash-bootstrap-components==1.5.0" >> requirements_docker.txt && \
    echo "plotly==5.17.0" >> requirements_docker.txt && \
    echo "pandas==2.1.4" >> requirements_docker.txt && \
    echo "" >> requirements_docker.txt && \
    echo "# Base de datos y RAG" >> requirements_docker.txt && \
    echo "psycopg2-binary==2.9.9" >> requirements_docker.txt && \
    echo "sqlalchemy==2.0.23" >> requirements_docker.txt && \
    echo "" >> requirements_docker.txt && \
    echo "# IA y procesamiento" >> requirements_docker.txt && \
    echo "openai==1.51.2" >> requirements_docker.txt && \
    echo "azure-search-documents==11.4.0" >> requirements_docker.txt && \
    echo "sentence-transformers==2.2.2" >> requirements_docker.txt && \
    echo "" >> requirements_docker.txt && \
    echo "# Utilidades" >> requirements_docker.txt && \
    echo "python-dotenv==1.0.0" >> requirements_docker.txt && \
    echo "requests==2.31.0" >> requirements_docker.txt && \
    echo "numpy==1.26.2" >> requirements_docker.txt && \
    echo "tqdm==4.66.1" >> requirements_docker.txt && \
    echo "colorama==0.4.6" >> requirements_docker.txt && \
    echo "" >> requirements_docker.txt && \
    echo "# Servidor web" >> requirements_docker.txt && \
    echo "gunicorn==21.2.0" >> requirements_docker.txt && \
    echo "waitress==2.1.2" >> requirements_docker.txt && \
    echo "" >> requirements_docker.txt && \
    echo "# Azure SDK" >> requirements_docker.txt && \
    echo "azure-identity==1.15.0" >> requirements_docker.txt && \
    echo "azure-keyvault-secrets==4.7.0" >> requirements_docker.txt

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements_docker.txt

# Copiar código fuente
COPY . .

# Crear usuario no-root para seguridad
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Exponer puerto 8050 para Dash
EXPOSE 8050

# Variables de entorno por defecto
ENV PYTHONPATH=/app
ENV DASH_HOST=0.0.0.0
ENV DASH_PORT=8050
ENV DASH_DEBUG=False

# Script de inicio con healthcheck
RUN echo '#!/bin/bash' > start.sh && \
    echo 'echo "🚀 Iniciando aplicación Dash..."' >> start.sh && \
    echo 'echo "📊 Puerto: $DASH_PORT"' >> start.sh && \
    echo 'echo "🔧 Debug: $DASH_DEBUG"' >> start.sh && \
    echo 'python app_dash.py' >> start.sh && \
    chmod +x start.sh

# Comando por defecto
CMD ["./start.sh"]

# Healthcheck para Container Apps
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8050/ || exit 1