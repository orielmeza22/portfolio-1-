"""
Configuración centralizada para Enterprise AI IDE
Gestiona configuración de Ollama, vectores, seguridad y UI
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List, Optional
import psutil
import httpx
import asyncio


class OllamaSettings(BaseSettings):
    """Configuración de Ollama con auto-detección"""
    base_url: str = Field(default="http://localhost:11434")
    default_model: str = Field(default="codellama:7b-instruct")
    timeout: int = Field(default=120)
    max_retries: int = Field(default=3)
    
    class Config:
        env_prefix = "OLLAMA_"


class VectorDBSettings(BaseSettings):
    """Configuración de Qdrant para RAG"""
    host: str = Field(default="localhost")
    port: int = Field(default=6333)
    collection_name: str = Field(default="code_embeddings")
    embedding_model: str = Field(default="all-MiniLM-L6-v2")
    
    class Config:
        env_prefix = "QDRANT_"


class SecuritySettings(BaseSettings):
    """Configuración de seguridad empresarial"""
    sandbox_enabled: bool = Field(default=True)
    audit_logging: bool = Field(default=True)
    max_file_size_mb: int = Field(default=50)
    allowed_extensions: List[str] = Field(default=[
        ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cpp", ".c", ".h",
        ".go", ".rs", ".rb", ".php", ".cs", ".swift", ".kt", ".scala"
    ])
    encryption_key: Optional[str] = Field(default=None)
    
    class Config:
        env_prefix = "SECURITY_"


class UISettings(BaseSettings):
    """Configuración de interfaz de usuario"""
    theme: str = Field(default="dark")
    font_size: int = Field(default=14)
    show_line_numbers: bool = Field(default=True)
    auto_save: bool = Field(default=True)
    
    class Config:
        env_prefix = "UI_"


class Settings(BaseSettings):
    """Configuración principal"""
    app_name: str = "Enterprise AI IDE"
    version: str = "0.1.0"
    debug: bool = Field(default=False)
    
    ollama: OllamaSettings = Field(default_factory=OllamaSettings)
    vector_db: VectorDBSettings = Field(default_factory=VectorDBSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    ui: UISettings = Field(default_factory=UISettings)
    
    async def detect_ollama_instances(self) -> List[dict]:
        """Detecta instancias locales de Ollama automáticamente"""
        instances = []
        
        # Puertos comunes de Ollama
        ports = [11434, 11435, 8080]
        
        for port in ports:
            urls = [
                f"http://localhost:{port}",
                f"http://127.0.0.1:{port}"
            ]
            
            for url in urls:
                try:
                    async with httpx.AsyncClient(timeout=2.0) as client:
                        response = await client.get(f"{url}/api/tags")
                        if response.status_code == 200:
                            models_data = response.json()
                            instances.append({
                                "url": url,
                                "models": models_data.get("models", []),
                                "port": port
                            })
                except Exception:
                    continue
        
        return instances
    
    async def validate_ollama_connection(self) -> bool:
        """Valida la conexión con Ollama"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.ollama.base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False
    
    def check_system_resources(self) -> dict:
        """Verifica recursos del sistema para IA local"""
        return {
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "memory_available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
            "disk_usage_percent": psutil.disk_usage('/').percent
        }
    
    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"


# Instancia global de configuración
settings = Settings()
