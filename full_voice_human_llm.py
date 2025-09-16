#!/usr/bin/env python3

import os
import time
import tempfile
import signal
import sys
import re
import json
from datetime import datetime
from pathlib import Path
import subprocess

import sounddevice as sd
import soundfile as sf
import numpy as np
import whisper
import google.generativeai as genai
from gtts import gTTS
from dotenv import load_dotenv


class FullVoiceChatBot:
    def __init__(self, sample_rate=16000, channels=1):
        # Audio settings
        self.sample_rate = sample_rate
        self.channels = channels
        self.recording = False
        self.audio_data = []

        # Load environment variables
        load_dotenv()

        # Initialize Whisper for speech-to-text
        print("🤖 Cargando Whisper...")
        self.whisper_model = whisper.load_model("base")

        # Initialize Gemini for chat
        self.api_key = os.getenv('API_KEY_GEMINI')
        if not self.api_key:
            raise ValueError("❌ API_KEY_GEMINI no encontrada en .env")

        genai.configure(api_key=self.api_key)
        self.gemini_model = genai.GenerativeModel('gemini-2.0-flash')

        # Initialize data directory
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)

        # Initialize conversation memory
        self.conversation_history = []
        self.max_history_length = 10  # Keep last 10 exchanges
        self.memory_file = self.data_dir / "memory" / "conversation_memory.json"

        # Ensure memory directory exists
        (self.data_dir / "memory").mkdir(parents=True, exist_ok=True)

        # Load existing conversation history
        self.load_memory()

        # Setup signal handler for Ctrl+C
        signal.signal(signal.SIGINT, self.signal_handler)

        print("✅ Chat por voz completo listo")
        print(f"🧠 Memoria persistente activada: {len(self.conversation_history)}/{self.max_history_length} intercambios cargados")

    def signal_handler(self, sig, frame):
        """Handle Ctrl+C gracefully"""
        if self.recording:
            print("\n⏹️ Deteniendo grabación...")
            self.recording = False
        else:
            print("\n💾 Guardando memoria...")
            self.save_memory()
            print("👋 Saliendo...")
            sys.exit(0)

    def record_audio(self):
        """Record audio until Enter is pressed again"""
        print("🎙️ Grabando... Presiona Enter para detener y enviar")

        self.recording = True
        self.audio_data = []

        def audio_callback(indata, frames, time, status):
            if status:
                print(f"⚠️ Audio status: {status}")
            if self.recording:
                self.audio_data.append(indata.copy())

        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                callback=audio_callback,
                dtype=np.float32
            ):
                # Wait for Enter to stop recording
                input()  # This will wait for Enter
                self.recording = False

        except Exception as e:
            print(f"❌ Error durante la grabación: {e}")
            return None

        # Process recorded data
        if not self.audio_data:
            print("⚠️ No se capturó audio.")
            return None

        # Concatenate all audio data
        audio_array = np.concatenate(self.audio_data, axis=0)
        audio_data = audio_array.flatten()

        duration = len(audio_data) / self.sample_rate
        print(f"⏱️ Audio grabado: {duration:.1f}s")

        return audio_data

    def transcribe_audio(self, audio_data):
        """Transcribe audio using Whisper"""
        if audio_data is None:
            return None

        # Save audio to temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            sf.write(temp_file.name, audio_data, self.sample_rate)
            temp_path = temp_file.name

        try:
            print("🔄 Transcribiendo...")
            result = self.whisper_model.transcribe(temp_path, language="es")
            transcription = result["text"].strip()
            return transcription
        finally:
            # Clean up temporary file
            os.unlink(temp_path)

    def clean_text_for_speech(self, text):
        """Clean text from markdown formatting for better TTS"""
        # Remove markdown formatting
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Bold **text**
        text = re.sub(r'\*(.*?)\*', r'\1', text)      # Italic *text*
        text = re.sub(r'`(.*?)`', r'\1', text)        # Code `text`
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)  # Code blocks
        text = re.sub(r'#{1,6}\s*', '', text)         # Headers
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # Links [text](url)
        text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)  # List items
        text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)  # Numbered lists
        text = re.sub(r'\n{3,}', '\n\n', text)        # Multiple newlines
        text = re.sub(r'^\s+|\s+$', '', text)         # Leading/trailing whitespace

        return text

    def add_to_conversation_history(self, user_message, assistant_response):
        """Add exchange to conversation history and save to file"""
        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "user": user_message,
            "assistant": assistant_response
        })

        # Keep only the last N exchanges to avoid token limits
        if len(self.conversation_history) > self.max_history_length:
            self.conversation_history = self.conversation_history[-self.max_history_length:]

        # Save to file after each exchange
        self.save_memory()

    def build_context_prompt(self, current_message):
        """Build a prompt with conversation context"""
        if not self.conversation_history:
            return current_message

        # Build context from conversation history
        context = "Contexto de la conversación anterior:\n"
        for exchange in self.conversation_history[-5:]:  # Use last 5 exchanges for context
            context += f"Usuario: {exchange['user']}\n"
            context += f"Asistente: {exchange['assistant']}\n\n"

        # Add current message
        context += f"Usuario actual: {current_message}\n\n"
        context += "Responde al usuario actual teniendo en cuenta el contexto de la conversación:"

        return context

    def load_memory(self):
        """Load conversation history from JSON file"""
        try:
            if self.memory_file.exists():
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.conversation_history = data.get('conversation_history', [])
                    # Ensure we don't exceed max history length
                    if len(self.conversation_history) > self.max_history_length:
                        self.conversation_history = self.conversation_history[-self.max_history_length:]
                        self.save_memory()  # Save the trimmed history
            else:
                self.conversation_history = []
        except Exception as e:
            print(f"⚠️ Error cargando memoria: {e}")
            self.conversation_history = []

    def save_memory(self):
        """Save conversation history to JSON file"""
        try:
            memory_data = {
                "last_updated": datetime.now().isoformat(),
                "total_exchanges": len(self.conversation_history),
                "max_history_length": self.max_history_length,
                "conversation_history": self.conversation_history
            }

            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(memory_data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"⚠️ Error guardando memoria: {e}")

    def clear_memory(self):
        """Clear conversation memory"""
        self.conversation_history = []
        self.save_memory()  # Save the cleared memory
        print("🧠 Memoria de conversación borrada y guardada")

    def send_to_gemini(self, message):
        """Send message to Gemini with conversation context"""
        try:
            print("🤖 Gemini está pensando...")

            # Build prompt with conversation context
            contextual_prompt = self.build_context_prompt(message)

            response = self.gemini_model.generate_content(contextual_prompt)
            if response.text:
                assistant_response = response.text.strip()

                # Add this exchange to conversation history
                self.add_to_conversation_history(message, assistant_response)

                return assistant_response
            else:
                return "⚠️ No se recibió respuesta"
        except Exception as e:
            return f"❌ Error: {e}"

    def text_to_speech(self, text, speed=1.25):
        """Convert text to speech using gTTS and play at specified speed"""
        try:
            print("🔊 Generando voz...")

            # Clean text from markdown formatting
            clean_text = self.clean_text_for_speech(text)

            # Create TTS object with slow=False for more natural speed
            tts = gTTS(text=clean_text, lang='es', slow=False)

            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                original_path = temp_file.name
                tts.save(original_path)

            # Create speed-adjusted version using ffmpeg
            speed_adjusted_path = original_path.replace('.mp3', f'_speed{speed}.mp3')

            print(f"🚀 Ajustando velocidad a {speed}x...")

            # Use ffmpeg to adjust playback speed
            ffmpeg_cmd = [
                'ffmpeg', '-i', original_path,
                '-filter:a', f'atempo={speed}',
                '-y',  # Overwrite output file
                speed_adjusted_path
            ]

            result = subprocess.run(ffmpeg_cmd, capture_output=True)

            if result.returncode == 0:
                # Play the speed-adjusted audio
                print("🔊 Reproduciendo respuesta...")

                # Try different audio players
                audio_players = ['mpg123', 'mpv', 'vlc', 'ffplay']

                for player in audio_players:
                    if subprocess.run(['which', player], capture_output=True).returncode == 0:
                        subprocess.run([player, speed_adjusted_path], capture_output=True)
                        break
                else:
                    print("❌ No se encontró reproductor de audio")

                # Clean up speed-adjusted file
                os.unlink(speed_adjusted_path)
            else:
                print("⚠️ No se pudo ajustar velocidad, reproduciendo audio original...")
                # Fallback to original audio
                subprocess.run(['mpg123', original_path], capture_output=True)

            # Clean up original file
            os.unlink(original_path)

        except Exception as e:
            print(f"❌ Error en text-to-speech: {e}")

    def start_full_voice_chat(self):
        """Start full voice chat loop"""
        print("\n🗣️ Chat Completo por Voz con Gemini")
        print("="*55)
        print("📋 Instrucciones:")
        print("   • Presiona Enter para comenzar a grabar")
        print("   • Habla al micrófono")
        print("   • Presiona Enter nuevamente para enviar")
        print("   • Gemini responderá con voz")
        print("   • 🧠 Gemini recordará la conversación")
        print("   • Di 'borrar memoria' para reiniciar")
        print("   • Escribe 'salir' para terminar")
        print("="*55)

        while True:
            try:
                # Wait for user to start recording
                user_input = input("\n🎤 Presiona Enter para grabar (o escribe 'salir'): ").strip()

                if user_input.lower() in ['salir', 'exit', 'quit']:
                    print("👋 ¡Hasta luego!")
                    break

                # Record audio
                audio_data = self.record_audio()

                if audio_data is None:
                    print("❌ No se pudo grabar audio. Intenta de nuevo.")
                    continue

                # Transcribe audio
                transcription = self.transcribe_audio(audio_data)

                if not transcription:
                    print("❌ No se pudo transcribir el audio. Intenta de nuevo.")
                    continue

                print(f"👤 Tú dijiste: \"{transcription}\"")
                print(f"🧠 Memoria: {len(self.conversation_history)}/{self.max_history_length} intercambios")

                # Check for special commands
                if transcription.lower() in ['borrar memoria', 'limpiar memoria', 'resetear memoria']:
                    self.clear_memory()
                    response = "He borrado la memoria de nuestra conversación. Empezamos de nuevo."
                    print(f"🤖 Gemini: {response}")
                    self.text_to_speech(response)
                    continue

                # Check if user wants to exit
                if transcription.lower() in ['salir', 'adiós', 'hasta luego', 'chao']:
                    print("👋 ¡Hasta luego!")

                    # Say goodbye with voice
                    goodbye_response = "¡Hasta luego! Ha sido un placer hablar contigo."
                    print(f"🤖 Gemini: {goodbye_response}")
                    self.text_to_speech(goodbye_response)

                    # Save memory before exiting
                    print("💾 Guardando memoria...")
                    self.save_memory()
                    break

                # Send to Gemini
                response = self.send_to_gemini(transcription)
                print(f"🤖 Gemini: {response}")

                # Convert response to speech and play
                self.text_to_speech(response)

            except KeyboardInterrupt:
                print("\n👋 ¡Hasta luego!")
                break
            except Exception as e:
                print(f"❌ Error inesperado: {e}")


def check_audio_dependencies():
    """Check if audio playback dependencies are available"""
    print("🔍 Verificando dependencias de audio...")

    # Check ffmpeg for speed adjustment
    ffmpeg_available = subprocess.run(['which', 'ffmpeg'], capture_output=True).returncode == 0
    if ffmpeg_available:
        print("✅ FFmpeg disponible para ajuste de velocidad")
    else:
        print("⚠️ FFmpeg no encontrado - se usará velocidad normal")
        print("💡 Instala FFmpeg con: sudo apt install ffmpeg")

    # Check audio players
    audio_players = ['mpg123', 'mpv', 'vlc', 'ffplay']
    available_players = []

    for player in audio_players:
        if subprocess.run(['which', player], capture_output=True).returncode == 0:
            available_players.append(player)

    if available_players:
        print(f"✅ Reproductores disponibles: {', '.join(available_players)}")
        return True
    else:
        print("⚠️ No se encontraron reproductores de audio.")
        print("💡 Instala uno con: sudo apt install mpg123")
        return False


def main():
    """Main function"""
    print("=== Chat Completo por Voz con Gemini ===")
    print()

    # Check dependencies
    if not check_audio_dependencies():
        print("❌ Instala un reproductor de audio antes de continuar.")
        return

    try:
        chat_bot = FullVoiceChatBot()
        chat_bot.start_full_voice_chat()
    except Exception as e:
        print(f"❌ Error al inicializar: {e}")


if __name__ == "__main__":
    main()