#!/bin/bash
echo "🚀 Iniciando servicios..."
docker-compose up -d
sleep 5
echo "✅ Servicios iniciados:"
echo "📊 PostgreSQL: localhost:5432"
echo "🖥️ PgAdmin: http://localhost:8080"
echo ""
echo "Credenciales PgAdmin:"
echo "  Email: admin@docs.local"
echo "  Password: admin_2025"
echo ""
echo "Credenciales PostgreSQL:"
echo "  Host: localhost:5432"
echo "  Database: documentos_juridicos"
echo "  User: docs_user"
echo "  Password: docs_password_2025"
