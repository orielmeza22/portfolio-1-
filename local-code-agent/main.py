#!/usr/bin/env python3
"""
Local Code Agent - Interfaz de línea de comandos
Un asistente de código tipo Cursor/Hermes que usa IA local con Ollama
"""

import sys
from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.formatted_text import HTML

from agent import CodeAgent
from config import DEFAULT_MODEL


def print_banner():
    """Mostrar banner de bienvenida"""
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║           LOCAL CODE AGENT - IA Local para Código         ║
    ║                    Powered by Ollama                      ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_help():
    """Mostrar ayuda de comandos"""
    help_text = """
    ═══════════════════════════════════════════════════════════
    COMANDOS DISPONIBLES:
    ═══════════════════════════════════════════════════════════
    
    /chat [mensaje]      - Conversar sobre código (usa historial)
    /explain [archivo]   - Explicar el contenido de un archivo
    /generate [desc]     - Generar código nuevo
    /refactor [archivo]  - Sugerir mejoras para un archivo
    /model [nombre]      - Cambiar modelo de IA
    /models              - Listar modelos disponibles
    /clear               - Limpiar historial de conversación
    /help                - Mostrar esta ayuda
    /quit o /exit        - Salir de la aplicación
    
    Ejemplos:
    -------
    /chat ¿Cómo funciona la recursividad en Python?
    /explain main.py
    /generate Una función que ordene una lista usando quicksort
    /refactor utils.py
    /model codellama
    
    ═══════════════════════════════════════════════════════════
    """
    print(help_text)


def main():
    """Función principal"""
    print_banner()
    
    # Inicializar agente
    agent = CodeAgent(DEFAULT_MODEL)
    
    # Verificar conexión con Ollama
    print("\n[INFO] Verificando conexión con Ollama...")
    if not agent.check_connection():
        print("❌ ERROR: No se pudo conectar con Ollama.")
        print("\nAsegúrate de que:")
        print("  1. Ollama esté instalado (https://ollama.ai)")
        print("  2. El servicio esté corriendo: ollama serve")
        print("  3. Hayas descargado un modelo: ollama pull codellama")
        print("\nSaliendo...")
        sys.exit(1)
    
    print(f"✅ Conectado con Ollama")
    print(f"📦 Modelo actual: {agent.get_current_model()}")
    
    # Listar modelos disponibles
    models = agent.list_models()
    if models:
        print(f"📚 Modelos disponibles: {', '.join(models)}")
    else:
        print("⚠️  No hay modelos descargados. Ejecuta: ollama pull codellama")
    
    print("\nEscribe /help para ver los comandos disponibles\n")
    print("=" * 60)
    
    # Loop principal
    while True:
        try:
            # Obtener input del usuario
            user_input = prompt(
                [('class:prompt', f'\n🤖 [{agent.get_current_model()}] > ')],
                history=FileHistory('.local_agent_history'),
                auto_suggest=AutoSuggestFromHistory(),
            ).strip()
            
            if not user_input:
                continue
            
            # Procesar comandos
            if user_input.startswith('/'):
                parts = user_input.split(' ', 1)
                command = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""
                
                if command in ['/quit', '/exit']:
                    print("\n👋 ¡Hasta luego!")
                    break
                
                elif command == '/help':
                    print_help()
                
                elif command == '/chat':
                    if not args:
                        print("❌ Uso: /chat [tu mensaje]")
                        continue
                    print(f"\n💬 Respondiendo...\n")
                    agent.chat(args)
                
                elif command == '/explain':
                    if not args:
                        print("❌ Uso: /explain [archivo]")
                        continue
                    print(f"\n📖 Explicando {args}...\n")
                    agent.explain_file(args)
                
                elif command == '/generate':
                    if not args:
                        print("❌ Uso: /generate [descripción]")
                        continue
                    print(f"\n✨ Generando código...\n")
                    agent.generate_code(args)
                
                elif command == '/refactor':
                    if not args:
                        print("❌ Uso: /refactor [archivo]")
                        continue
                    print(f"\n🔧 Refactorizando {args}...\n")
                    agent.refactor_file(args)
                
                elif command == '/model':
                    if not args:
                        print(f"ℹ️  Modelo actual: {agent.get_current_model()}")
                        print("Uso: /model [nombre_del_modelo]")
                        continue
                    
                    if agent.set_model(args):
                        print(f"✅ Modelo cambiado a: {args}")
                        agent.clear_history()  # Limpiar historial al cambiar modelo
                    else:
                        print(f"❌ Error al cambiar modelo")
                
                elif command == '/models':
                    models = agent.list_models()
                    if models:
                        print("\n📚 Modelos disponibles:")
                        for model in models:
                            print(f"  • {model}")
                    else:
                        print("⚠️  No hay modelos descargados")
                
                elif command == '/clear':
                    agent.clear_history()
                    print("✅ Historial limpiado")
                
                else:
                    print(f"❌ Comando desconocido: {command}")
                    print("Escribe /help para ver los comandos disponibles")
            
            else:
                # Si no es un comando, tratar como chat directo
                print(f"\n💬 Respondiendo...\n")
                agent.chat(user_input)
        
        except KeyboardInterrupt:
            print("\n\n👋 Usa /quit para salir")
            continue
        
        except EOFError:
            print("\n\n👋 ¡Hasta luego!")
            break
        
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            print("Intenta nuevamente o escribe /help")


if __name__ == "__main__":
    main()
