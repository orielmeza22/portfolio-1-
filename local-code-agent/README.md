# Local Code Agent - IA Local para Desarrollo de Código

Una aplicación tipo Cursor o Hermes Agent que utiliza modelos de IA locales a través de Ollama para asistir en el desarrollo de código.

## Características

- **IA 100% Local**: Usa Ollama para ejecutar modelos localmente sin enviar datos a la nube
- **Asistente de Código**: Generación, explicación y refactorización de código
- **Chat Interactivo**: Interfaz de chat para conversar con la IA sobre tu código
- **Soporte Multi-modelo**: Compatible con todos los modelos de Ollama (Llama, Mistral, Codellama, etc.)
- **Contexto de Archivos**: Puede leer y analizar archivos del proyecto

## Requisitos

- Python 3.8+
- Ollama instalado y corriendo ([ollama.ai](https://ollama.ai))
- Modelos descargados en Ollama (ej: `ollama pull codellama` o `ollama pull llama2`)

## Instalación

```bash
cd local-code-agent
pip install -r requirements.txt
```

## Uso

### Iniciar la aplicación

```bash
python main.py
```

### Comandos disponibles

- `/chat [mensaje]` - Iniciar conversación sobre código
- `/explain [archivo]` - Explicar el contenido de un archivo
- `/generate [descripción]` - Generar código nuevo
- `/refactor [archivo]` - Sugerir mejoras para un archivo
- `/model [nombre]` - Cambiar el modelo de IA
- `/help` - Mostrar ayuda
- `/quit` - Salir de la aplicación

## Ejemplos

### Generar una función
```
/generate Una función en Python que calcule el factorial de un número
```

### Explicar un archivo
```
/explain main.py
```

### Refactorizar código
```
/refactor utils.py
```

## Modelos Recomendados

- **codellama**: Especializado en código (recomendado)
- **llama2**: Modelo generalista bueno para explicaciones
- **mistral**: Rápido y eficiente
- **deepseek-coder**: Excelente para tareas de programación

Descargar modelos:
```bash
ollama pull codellama
ollama pull llama2
ollama pull mistral
```

## Configuración

Puedes configurar el modelo por defecto y otras opciones en `config.py`.

## Estructura del Proyecto

```
local-code-agent/
├── main.py           # Punto de entrada principal
├── agent.py          # Lógica del agente de IA
├── ollama_client.py  # Cliente para comunicación con Ollama
├── file_handler.py   # Manejo de archivos y contexto
├── config.py         # Configuración
├── requirements.txt  # Dependencias
└── README.md         # Este archivo
```

## Licencia

MIT License
