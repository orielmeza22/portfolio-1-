"""
Configuración del agente de código local
"""

# Modelo por defecto para usar con Ollama
DEFAULT_MODEL = "codellama"

# URL de la API de Ollama
OLLAMA_BASE_URL = "http://localhost:11434"

# Timeout para las requests a Ollama (en segundos)
REQUEST_TIMEOUT = 120

# Temperatura para la generación (0.0 a 1.0)
TEMPERATURE = 0.7

# Máximo de tokens en la respuesta
MAX_TOKENS = 2048

# Directorio de trabajo por defecto
WORKING_DIRECTORY = "."
