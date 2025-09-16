# 🗣️ SpeakerMan - Manual de Usuario

## 📋 Descripción

SpeakerMan es un sistema completo de chat por voz que utiliza inteligencia artificial para mantener conversaciones naturales. Combina reconocimiento de voz (Whisper), procesamiento de lenguaje natural (Gemini) y síntesis de voz (gTTS) para crear una experiencia de conversación fluida.

## ✨ Características Principales

- 🎙️ **Grabación de voz** con micrófono
- 🤖 **Transcripción automática** con Whisper AI
- 💬 **Chat inteligente** con Gemini AI
- 🔊 **Respuestas por voz** con velocidad ajustable (1.25x)
- 🧠 **Memoria conversacional** (últimos 10 intercambios)
- 📁 **Organización automática** de archivos
- 🧹 **Limpieza de formato** Markdown en audio

## 📦 Instalación

### 1. Requisitos del Sistema

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y portaudio19-dev ffmpeg mpg123

# Verificar Python 3.8+
python3 --version
```

### 2. Configuración del Proyecto

```bash
# Clonar o descargar el proyecto
cd speakerman

# Crear entorno virtual
python3 -m venv env

# Activar entorno virtual
source env/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Configuración de API

Crear archivo `.env` en la raíz del proyecto:

```bash
API_KEY_GEMINI=tu_api_key_de_gemini_aqui
```

**Obtener API Key de Gemini:**
1. Ir a [Google AI Studio](https://aistudio.google.com/)
2. Crear cuenta y generar API key
3. Copiar la clave al archivo `.env`

## 🚀 Scripts Disponibles

### ⭐ **SCRIPT PRINCIPAL: `full_voice_human_llm_advanced.py`**

**🎯 ESTE ES EL QUE DEBES USAR**

```bash
source env/bin/activate
python full_voice_human_llm_advanced.py
```

**¿Por qué es el principal?**
- ✅ **Chat completo por voz** (hablas y responde con voz)
- ✅ **Memoria inteligente** que recuerda entre sesiones
- ✅ **Aprende sobre ti** automáticamente (nombre, edad, profesión)
- ✅ **Busca conversaciones** anteriores relevantes
- ✅ **Comandos especiales**: "mostrar perfil", "borrar memoria"

---

### 2. `full_voice_human_llm.py` - **Chat Básico**

**Versión más simple sin memoria avanzada**

```bash
source env/bin/activate
python full_voice_human_llm.py
```

**Funcionalidades:**
- Chat bidireccional por voz
- Memoria básica (solo durante sesión)
- Respuestas con velocidad 1.25x

### 2. `grabador.py` - **Grabador con Transcripción**

```bash
python grabador.py
```

**Funcionalidades:**
- Graba audio del micrófono
- Transcribe con Whisper
- Guarda audio y transcripción

### 3. `chat_simple.py` - **Chat de Texto**

```bash
python chat_simple.py
```

**Funcionalidades:**
- Chat simple por texto con Gemini
- Sin grabación de voz

### 4. Scripts de Prueba

- `grabador_test.py` - Prueba grabación con duración fija
- `grabador_simple.py` - Grabación básica sin transcripción
- `chat_human_to_llm.py` - Chat por voz sin respuesta vocal

## 🎮 Uso del Chat Principal (Recomendado)

### Flujo de Conversación

1. **Iniciar**: `python full_voice_human_llm_advanced.py`
2. **Grabar**: Presiona `Enter` para empezar a grabar
3. **Hablar**: Habla normalmente al micrófono
4. **Enviar**: Presiona `Enter` nuevamente para procesar
5. **Escuchar**: Gemini responde con voz
6. **Repetir**: Continúa la conversación

### Comandos Especiales por Voz

| Comando | Acción |
|---------|--------|
| `"mostrar perfil"` | **NUEVO** - Muestra información guardada sobre ti |
| `"mi perfil"` | **NUEVO** - Muestra tu perfil de usuario |
| `"borrar memoria"` | Reinicia la memoria conversacional |
| `"limpiar memoria"` | Borra el historial de chat |
| `"resetear memoria"` | Limpia la conversación |
| `"salir"` | Termina el programa |
| `"adiós"` | Termina el programa |
| `"hasta luego"` | Termina el programa |

### Características Avanzadas (Solo en script principal)

#### 🧠 **Memoria Inteligente**
- **Aprende automáticamente**: Extrae tu nombre, edad, profesión
- **Recuerda entre sesiones**: La información se guarda permanentemente
- **Búsqueda semántica**: Encuentra conversaciones anteriores relevantes
- **Perfil dinámico**: Se actualiza mientras conversas

#### 👤 **Ejemplo de Extracción Automática**
```
👤 Tú dices: "Hola, soy Ana y tengo 25 años"
🧠 Sistema: Automáticamente guarda → name: Ana, age: 25

👤 Más tarde dices: "Trabajo como doctora"
🧠 Sistema: Actualiza → profession: doctora

👤 Después preguntas: "¿Cuál es mi profesión?"
🤖 Gemini: "Eres doctora, Ana, como me dijiste antes"
```

### Indicadores Visuales

```
👤 Tú dijiste: "Hola, ¿cómo estás?"
🧠 Contexto inteligente cargado
💾 Conversación almacenada en memoria avanzada
🤖 Gemini: ¡Hola! Estoy muy bien...
🔊 Generando voz...
🚀 Ajustando velocidad a 1.25x...
🔊 Reproduciendo respuesta...
```

## 📁 Estructura de Archivos

```
speakerman/
├── full_voice_human_llm_advanced.py  # ⭐ SCRIPT PRINCIPAL
├── full_voice_human_llm.py           # Chat básico
├── memory_system.py                  # Sistema de memoria inteligente
├── grabador.py                       # Grabador con transcripción
├── chat_simple.py                    # Chat de texto
├── requirements.txt                  # Dependencias
├── .env                              # API keys (no incluir en git)
├── .gitignore                        # Archivos excluidos
├── manual.md                         # Este manual
└── data/                             # Datos generados
    ├── audio/                        # Archivos de audio (.wav)
    ├── transcripciones/              # Transcripciones (.json)
    ├── chats/                        # Historiales de chat (.json)
    └── memory/                       # 🧠 Base de datos de memoria
        └── conversation.db           # SQLite con memoria inteligente
```

## ⚙️ Configuración Avanzada

### Ajustar Velocidad de Voz

En `full_voice_human_llm.py`, línea 147:

```python
def text_to_speech(self, text, speed=1.25):  # Cambiar velocidad aquí
```

### Cambiar Memoria Conversacional

En `full_voice_human_llm.py`, línea 46:

```python
self.max_history_length = 10  # Cambiar cantidad de intercambios
```

### Cambiar Modelo de Whisper

En cualquier script, cambiar:

```python
self.whisper_model = whisper.load_model("base")  # tiny, small, medium, large
```

## 🔧 Solución de Problemas

### Error: "PortAudio library not found"

```bash
sudo apt install portaudio19-dev
```

### Error: "FFmpeg not found"

```bash
sudo apt install ffmpeg
```

### Error: "API_KEY_GEMINI no encontrada"

1. Verificar que existe el archivo `.env`
2. Verificar que la API key está correcta
3. Verificar que no hay espacios extra

### Audio no se reproduce

```bash
# Instalar reproductor de audio
sudo apt install mpg123
```

### Whisper muy lento

Cambiar a modelo más pequeño:

```python
whisper.load_model("tiny")  # Más rápido, menos preciso
```

## 📊 Comandos Útiles

### Verificar Dependencias

```bash
source env/bin/activate
python -c "
import whisper, sounddevice, gtts, google.generativeai
print('✅ Todas las dependencias instaladas')
"
```

### Limpiar Archivos Generados

```bash
rm -rf data/audio/*.wav
rm -rf data/transcripciones/*.json
rm -rf data/chats/*.json
```

### Actualizar Dependencias

```bash
source env/bin/activate
pip install --upgrade -r requirements.txt
```

## 🎯 Consejos de Uso

### Para Mejor Reconocimiento de Voz

- Hablar claramente y a velocidad normal
- Usar micrófono de buena calidad
- Evitar ruido de fondo
- Esperar a que termine de grabar antes de hablar

### Para Conversaciones Efectivas

- Usar preguntas específicas
- Aprovechar la memoria conversacional
- Usar "borrar memoria" para cambiar de tema
- Hablar naturalmente, no como robot

### Optimización de Rendimiento

- Usar modelo Whisper "base" para balance calidad/velocidad
- Mantener sesiones de chat moderadas (< 50 intercambios)
- Cerrar otros programas que usen micrófono

## 📝 Notas Técnicas

- **Whisper**: Procesamiento local, no requiere internet
- **Gemini**: Requiere conexión a internet
- **gTTS**: Requiere conexión a internet para síntesis
- **Memoria**: Se mantiene solo durante la sesión
- **Archivos**: Se guardan localmente en formato JSON/WAV

## 🆘 Soporte

Si encuentras problemas:

1. Verificar que todas las dependencias están instaladas
2. Comprobar permisos de micrófono
3. Verificar conexión a internet
4. Revisar logs de error en la consola
5. Intentar con modelo Whisper más pequeño

---

**¡Disfruta conversando con tu asistente de voz inteligente!** 🎙️🤖✨