#!/usr/bin/env python3

import asyncio
import subprocess
import sys
import time
from pathlib import Path

async def start_memory_server():
    """Start the MCP Memory Server"""
    print("🚀 Iniciando servidor de memoria MCP...")

    # Start the memory server
    process = await asyncio.create_subprocess_exec(
        sys.executable, "memory_server.py",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    print(f"📡 Servidor MCP iniciado con PID: {process.pid}")
    print("💡 Para detener el servidor, presiona Ctrl+C")

    try:
        # Wait for the process to complete
        stdout, stderr = await process.communicate()

        if stdout:
            print("📝 Stdout:", stdout.decode())
        if stderr:
            print("❌ Stderr:", stderr.decode())

    except KeyboardInterrupt:
        print("\n⏹️ Deteniendo servidor MCP...")
        process.terminate()
        await process.wait()
        print("✅ Servidor MCP detenido")

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import mcp
        print("✅ MCP library disponible")
        return True
    except ImportError:
        print("❌ MCP library no encontrada")
        print("💡 Instala con: pip install mcp")
        return False

async def main():
    """Main function"""
    print("=== Servidor de Memoria MCP ===")
    print()

    if not check_dependencies():
        return

    # Check if database directory exists
    db_dir = Path("data/memory")
    db_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Directorio de base de datos: {db_dir}")

    await start_memory_server()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Saliendo...")
    except Exception as e:
        print(f"❌ Error: {e}")