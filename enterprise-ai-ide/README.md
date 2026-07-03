# Enterprise AI IDE

IDE empresarial con IA local usando Ollama - Una alternativa open-source a Cursor/Hermes Agent.

## 🚀 Características Principales

- **IA 100% Local**: Ejecuta modelos de IA en tu máquina sin enviar código a servidores externos
- **Detección Automática de Ollama**: Encuentra y conecta automáticamente instancias locales de Ollama
- **Agentes Especializados**: 8 agentes para diferentes tareas (generación, review, debugging, refactorización, etc.)
- **RAG de Código**: Búsqueda semántica de código relevante usando embeddings vectoriales
- **Streaming en Tiempo Real**: Respuestas token por token con soporte WebSocket
- **API REST Completa**: FastAPI con endpoints para todas las funcionalidades
- **Seguridad Empresarial**: Sandboxing, auditoría, gestión de secretos
- **Multi-lenguaje**: Soporte para Python, JavaScript, TypeScript, Java, C++, Go, Rust y más

## 📋 Requisitos

- Python 3.9+
- Ollama instalado y ejecutándose
- 8GB+ RAM recomendado (16GB+ para modelos grandes)
- Qdrant (opcional, para RAG)

## 🛠️ Instalación

### 1. Instalar Ollama

```bash
# macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows: Descargar desde https://ollama.com
```

### 2. Descargar Modelos

```bash
# Modelo principal para código
ollama pull codellama:7b-instruct

# Modelos adicionales opcionales
ollama pull llama2:7b          # Chat general
ollama pull mistral:7b         # Alternativa rápida
ollama pull deepseek-coder     # Especializado en código
```

### 3. Configurar Entorno Python

```bash
cd enterprise-ai-ide

# Crear entorno virtual
python -m venv venv

# Activar entorno
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Instalar dependencias
pip install -e .
```

### 4. Instalar Qdrant (Opcional para RAG)

```bash
# Usando Docker
docker run -d -p 6333:6333 qdrant/qdrant

# O descargar binario desde https://qdrant.tech/documentation/quick-start/
```

## 🚀 Uso

### Iniciar Servidor API

```bash
# Desde la raíz del proyecto
python -m api.server

# O con uvicorn directamente
uvicorn api.server:app --host 0.0.0.0 --port 8000 --reload
```

### Verificar Estado

```bash
curl http://localhost:8000/health
```

### Detectar Instancias Ollama

```bash
curl http://localhost:8000/ollama/detect
```

### Listar Modelos Disponibles

```bash
curl http://localhost:8000/models
```

## 📡 Endpoints API

### Chat

```bash
# Chat básico
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hola"}]}'

# Chat con streaming
curl -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Explica Python"}]}'
```

### Generación de Código

```bash
curl -X POST http://localhost:8000/code/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Función que calcula Fibonacci",
    "language": "python"
  }'
```

### Review de Código

```bash
curl -X POST http://localhost:8000/code/review \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def foo(): return 1",
    "language": "python"
  }'
```

### Explicar Código

```bash
curl -X POST http://localhost:8000/code/explain \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)",
    "language": "python"
  }'
```

### Refactorizar Código

```bash
curl -X POST http://localhost:8000/code/refactor \
  -H "Content-Type: application/json" \
  -d '{
    "code": "...",
    "language": "python",
    "instructions": "Mejora legibilidad y rendimiento"
  }'
```

### RAG - Indexar Archivo

```bash
curl -X POST http://localhost:8000/context/index \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/path/to/file.py",
    "content": "..."
  }'
```

### RAG - Buscar Código Relevante

```bash
curl -X POST http://localhost:8000/context/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "función de autenticación JWT",
    "language_filter": "python",
    "limit": 5
  }'
```

### Ejecutar Agente Especializado

```bash
curl -X POST http://localhost:8000/agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "code_generator",
    "input_data": "Crear API REST con FastAPI",
    "language": "python"
  }'
```

Tipos de agentes disponibles:
- `code_generator`
- `code_reviewer`
- `debugger`
- `refactorer`
- `explainer`
- `test_generator`
- `documentation`
- `architect`

## 🔌 WebSocket

Para chat en tiempo real:

```python
import websockets
import json

async with websockets.connect("ws://localhost:8000/ws/chat") as ws:
    await ws.send(json.dumps({
        "message": "Hola, ¿cómo estás?",
        "model": "codellama:7b-instruct"
    }))
    
    async for response in ws:
        data = json.loads(response)
        if data["type"] == "chunk":
            print(data["content"], end="", flush=True)
```

## ⚙️ Configuración

Crear archivo `.env` en la raíz:

```bash
# Ollama
OLLAMA__BASE_URL=http://localhost:11434
OLLAMA__DEFAULT_MODEL=codellama:7b-instruct
OLLAMA__TIMEOUT=120

# Qdrant (RAG)
QDRANT__HOST=localhost
QDRANT__PORT=6333
QDRANT__COLLECTION_NAME=code_embeddings
QDRANT__EMBEDDING_MODEL=all-MiniLM-L6-v2

# Seguridad
SECURITY__SANDBOX_ENABLED=true
SECURITY__AUDIT_LOGGING=true
SECURITY__MAX_FILE_SIZE_MB=50

# UI
UI__THEME=dark
UI__FONT_SIZE=14
```

## 🧪 Testing

```bash
# Instalar dependencias de desarrollo
pip install -e ".[dev]"

# Ejecutar tests
pytest tests/ -v

# Con cobertura
pytest tests/ --cov=core --cov=api --cov-report=html
```

## 📁 Estructura del Proyecto

```
enterprise-ai-ide/
├── api/                    # API REST FastAPI
│   └── server.py
├── config/                 # Configuración
│   └── settings.py
├── core/                   # Lógica principal
│   ├── agents/             # Agentes especializados
│   │   └── specialized_agents.py
│   ├── context/            # Gestión de contexto RAG
│   │   └── code_context.py
│   ├── llm/                # Cliente Ollama
│   │   └── ollama_client.py
│   └── utils/              # Utilidades
├── tests/                  # Tests unitarios
├── pyproject.toml          # Dependencias y configuración
└── README.md
```

## 🔒 Seguridad Empresarial

- **Sandboxing**: Ejecución de código en entorno aislado
- **Audit Logging**: Registro de todas las interacciones
- **Gestión de Secretos**: Encriptación de credenciales
- **Validación de Archivos**: Límites de tamaño y extensiones permitidas
- **Control de Acceso**: Autenticación y autorización (en desarrollo)

## 🤝 Contribuir

1. Fork el repositorio
2. Crear branch feature (`git checkout -b feature/amazing-feature`)
3. Commit cambios (`git commit -m 'Add amazing feature'`)
4. Push (`git push origin feature/amazing-feature`)
5. Abrir Pull Request

## 📄 Licencia

MIT License - ver LICENSE para detalles

## 🙏 Agradecimientos

- [Ollama](https://ollama.com) - Ejecución local de modelos
- [FastAPI](https://fastapi.tiangolo.com) - Framework API
- [Qdrant](https://qdrant.tech) - Vector database
- [CodeLlama](https://ai.meta.com/blog/code-llama-large-language-model-for-code/) - Modelo de código

---

**Nota**: Este proyecto está en desarrollo activo. Algunas características pueden estar incompletas o cambiar en futuras versiones.
