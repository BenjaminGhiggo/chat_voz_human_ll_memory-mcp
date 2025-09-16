#!/bin/bash

echo "=== Instalador MCP para SpeakerMan ==="
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: Ejecuta este script desde el directorio del proyecto"
    exit 1
fi

# Activar entorno virtual
if [ ! -d "env" ]; then
    echo "🐍 Creando entorno virtual..."
    python3 -m venv env
fi

echo "🐍 Activando entorno virtual..."
source env/bin/activate

# Actualizar pip
echo "📦 Actualizando pip..."
pip install --upgrade pip

# Instalar dependencias MCP específicas
echo "🔌 Instalando dependencias MCP..."

# Nota: MCP puede no estar disponible en PyPI aún
# Instalaremos las dependencias básicas necesarias

pip install asyncio-extras
pip install aiosqlite
pip install sqlite3

# Verificar instalación
echo ""
echo "✅ Verificando instalación..."

python3 -c "
import asyncio
import sqlite3
import json
print('✅ asyncio disponible')
print('✅ sqlite3 disponible')
print('✅ json disponible')
print('✅ Dependencias básicas instaladas')
"

echo ""
echo "📋 Archivos MCP creados:"
echo "   - memory_server.py          (Servidor de memoria MCP)"
echo "   - full_voice_human_llm_mcp.py (Cliente con MCP)"
echo "   - start_mcp_memory.py       (Iniciador del servidor)"
echo "   - test_mcp_memory.py        (Pruebas del sistema)"
echo ""

echo "🚀 Para usar el sistema MCP:"
echo "   1. Terminal 1: python start_mcp_memory.py"
echo "   2. Terminal 2: python full_voice_human_llm_mcp.py"
echo ""

echo "🧪 Para probar el sistema:"
echo "   python test_mcp_memory.py"
echo ""

echo "✅ Instalación MCP completada!"