#!/bin/bash

echo "Instalando dependencias del sistema para el grabador de audio..."

# Instalar PortAudio development package
echo "Instalando PortAudio..."
sudo apt update
sudo apt install -y portaudio19-dev

# Activar entorno virtual e instalar dependencias Python
echo "Activando entorno virtual e instalando dependencias Python..."
source env/bin/activate
pip install --upgrade pip

# Instalar dependencias básicas
pip install sounddevice soundfile numpy

echo "Instalación completada!"
echo ""
echo "Para usar el grabador:"
echo "1. Ejecuta: source env/bin/activate"
echo "2. Ejecuta: python grabador_simple.py"
echo ""
echo "Para instalar Whisper (transcripción automática):"
echo "pip install openai-whisper"