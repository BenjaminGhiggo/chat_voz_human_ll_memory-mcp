#!/usr/bin/env python3

import asyncio
import sqlite3
from pathlib import Path
from memory_server import MemoryDatabase

async def test_memory_database():
    """Test the memory database functionality"""
    print("🧪 Probando base de datos de memoria...")

    # Create test database
    db = MemoryDatabase("data/memory/test_conversation.db")

    # Test 1: Store conversations
    print("\n📝 Prueba 1: Almacenar conversaciones")
    conv_id1 = db.store_conversation(
        "Hola, mi nombre es Juan",
        "¡Hola Juan! Encantado de conocerte.",
        "test_session",
        1.5
    )
    print(f"   Conversación 1 almacenada con ID: {conv_id1}")

    conv_id2 = db.store_conversation(
        "Tengo 25 años y estudio ingeniería",
        "Qué interesante, Juan. ¿Qué tipo de ingeniería estudias?",
        "test_session",
        1.2
    )
    print(f"   Conversación 2 almacenada con ID: {conv_id2}")

    # Test 2: Get recent conversations
    print("\n📚 Prueba 2: Obtener conversaciones recientes")
    recent = db.get_recent_conversations(limit=5, session_id="test_session")
    for i, conv in enumerate(recent):
        print(f"   {i+1}. Usuario: {conv['user']}")
        print(f"      Asistente: {conv['assistant']}")
        print(f"      Importancia: {conv['importance']}")

    # Test 3: Search conversations
    print("\n🔍 Prueba 3: Buscar conversaciones")
    results = db.search_conversations("Juan", limit=3)
    print(f"   Encontradas {len(results)} conversaciones con 'Juan':")
    for conv in results:
        print(f"   - {conv['user'][:50]}...")

    # Test 4: User profile
    print("\n👤 Prueba 4: Perfil de usuario")
    db.update_user_profile("name", "Juan")
    db.update_user_profile("age", "25")
    db.update_user_profile("study", "ingeniería")

    profile = db.get_user_profile()
    print("   Perfil guardado:")
    for key, value in profile.items():
        print(f"   - {key}: {value}")

    # Test 5: Database stats
    print("\n📊 Prueba 5: Estadísticas de la base de datos")
    with sqlite3.connect(db.db_path) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM conversations")
        conv_count = cursor.fetchone()[0]
        print(f"   Total conversaciones: {conv_count}")

        cursor.execute("SELECT COUNT(*) FROM user_profile")
        profile_count = cursor.fetchone()[0]
        print(f"   Elementos en perfil: {profile_count}")

    print("\n✅ Todas las pruebas completadas exitosamente!")

    # Cleanup
    db.db_path.unlink()
    print("🧹 Base de datos de prueba eliminada")

async def test_memory_server_tools():
    """Test memory server tools simulation"""
    print("\n🛠️ Probando herramientas del servidor MCP...")

    from memory_server import MemoryServer

    server = MemoryServer()

    # Test list tools
    tools_result = await server.list_tools(None)
    print(f"📋 Herramientas disponibles: {len(tools_result.tools)}")
    for tool in tools_result.tools:
        print(f"   - {tool.name}: {tool.description}")

    print("\n✅ Herramientas MCP verificadas!")

async def main():
    """Main test function"""
    print("=== Pruebas del Sistema de Memoria MCP ===")
    print()

    try:
        await test_memory_database()
        await test_memory_server_tools()

        print("\n🎉 ¡Todas las pruebas pasaron exitosamente!")
        print("💡 El sistema de memoria MCP está listo para usar")

    except Exception as e:
        print(f"\n❌ Error en las pruebas: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())