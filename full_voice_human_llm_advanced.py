#!/usr/bin/env python3

import os
import time
import tempfile
import signal
import sys
import re
import json
import asyncio
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

# Import our advanced memory system
from memory_system import MemoryManager


class FullVoiceChatBotAdvanced:
    def __init__(self, sample_rate=16000, channels=1):
        # Audio settings
        self.sample_rate = sample_rate
        self.channels = channels
        self.recording = False
        self.audio_data = []

        # Load environment variables
        load_dotenv()

        # Initialize data directory
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)

        # Initialize Whisper for speech-to-text
        print("🤖 Cargando Whisper...")
        self.whisper_model = whisper.load_model("base")

        # Initialize Gemini for chat
        self.api_key = os.getenv('API_KEY_GEMINI')
        if not self.api_key:
            raise ValueError("❌ API_KEY_GEMINI no encontrada en .env")

        genai.configure(api_key=self.api_key)
        self.gemini_model = genai.GenerativeModel('gemini-2.0-flash')

        # Initialize advanced memory system
        self.memory = MemoryManager()
        print("🧠 Sistema de memoria avanzado inicializado")

        # Setup signal handler for Ctrl+C
        signal.signal(signal.SIGINT, self.signal_handler)

        print("✅ Chat por voz avanzado listo")

    def signal_handler(self, sig, frame):
        """Handle Ctrl+C gracefully"""
        if self.recording:
            print("\n⏹️ Deteniendo grabación...")
            self.recording = False
        else:
            print("\n👋 Saliendo...")
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

    async def send_to_gemini(self, message):
        """Send message to Gemini with advanced context"""
        try:
            print("🤖 Gemini está pensando...")

            # Get intelligent context from memory system
            contextual_prompt = await self.memory.get_context(message)
            print("🧠 Contexto inteligente cargado")

            response = self.gemini_model.generate_content(contextual_prompt)
            if response.text:
                assistant_response = response.text.strip()

                # Store this exchange in advanced memory
                await self.memory.store_conversation(message, assistant_response)
                print("💾 Conversación almacenada en memoria avanzada")

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

    async def start_advanced_voice_chat(self):
        """Start advanced voice chat loop"""
        print("\n🗣️ Chat Avanzado por Voz con Gemini")
        print("="*65)
        print("📋 Instrucciones:")
        print("   • Presiona Enter para comenzar a grabar")
        print("   • Habla al micrófono")
        print("   • Presiona Enter nuevamente para enviar")
        print("   • Gemini responderá con voz")
        print("   • 🧠 Memoria inteligente con búsqueda semántica")
        print("   • 👤 Perfil de usuario automático")
        print("   • Di 'borrar memoria' para reiniciar")
        print("   • Di 'mostrar perfil' para ver información guardada")
        print("   • Escribe 'salir' para terminar")
        print("="*65)

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

                # Check for special commands
                if transcription.lower() in ['borrar memoria', 'limpiar memoria', 'resetear memoria']:
                    await self.memory.clear_memory()
                    response = "He borrado la memoria de nuestra conversación. Empezamos de nuevo."
                    print(f"🤖 Gemini: {response}")
                    self.text_to_speech(response)
                    continue

                if transcription.lower() in ['mostrar perfil', 'mi perfil', 'perfil usuario']:
                    profile_data = await self.memory.get_profile()
                    if profile_data == "No profile information stored":
                        response = "Aún no tengo información guardada sobre ti. Cuéntame algo sobre ti."
                    else:
                        # Convert JSON to natural speech
                        profile_dict = json.loads(profile_data)
                        profile_parts = []
                        for key, value in profile_dict.items():
                            if key == "name":
                                profile_parts.append(f"Tu nombre es {value}")
                            elif key == "age":
                                profile_parts.append(f"tienes {value} años")
                            elif key == "profession":
                                profile_parts.append(f"estudias {value}")
                            else:
                                profile_parts.append(f"tu {key} es {value}")
                        response = "Lo que sé sobre ti: " + ", ".join(profile_parts) + "."

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
                    break

                # Send to Gemini with advanced memory
                response = await self.send_to_gemini(transcription)
                print(f"🤖 Gemini: {response}")

                # Convert response to speech and play
                self.text_to_speech(response)

            except KeyboardInterrupt:
                print("\n👋 ¡Hasta luego!")
                break
            except Exception as e:
                print(f"❌ Error inesperado: {e}")


async def main():
    """Main function"""
    print("=== Chat Avanzado por Voz con Gemini ===")
    print()

    try:
        chat_bot = FullVoiceChatBotAdvanced()
        await chat_bot.start_advanced_voice_chat()
    except Exception as e:
        print(f"❌ Error al inicializar: {e}")


if __name__ == "__main__":
    asyncio.run(main())