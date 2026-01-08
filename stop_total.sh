#!/bin/bash
echo "🛑 Deteniendo servicios backend/frontend..."
kill 3876259 3876291 2>/dev/null || true
echo "✅ Servicios detenidos"
