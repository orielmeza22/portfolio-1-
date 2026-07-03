"""
Cliente avanzado para Ollama con soporte de streaming y múltiples modelos
Gestiona conexiones, reintentos y detección automática de instancias
"""
import asyncio
import json
from typing import AsyncGenerator, Dict, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import httpx

from config.settings import settings


@dataclass
class ModelInfo:
    """Información de un modelo disponible"""
    name: str
    size: int
    digest: str
    modified_at: str
    details: Dict


@dataclass
class ChatMessage:
    """Mensaje de chat estructurado"""
    role: str  # "system", "user", "assistant"
    content: str
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict:
        return {
            "role": self.role,
            "content": self.content
        }


class OllamaClient:
    """Cliente asíncrono para Ollama con características empresariales"""
    
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or settings.ollama.base_url
        self.timeout = settings.ollama.timeout
        self.max_retries = settings.ollama.max_retries
        self._client: Optional[httpx.AsyncClient] = None
        self._available_models: List[ModelInfo] = []
        self._connected = False
    
    async def connect(self) -> bool:
        """Establece conexión con Ollama"""
        try:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout, connect=5.0)
            )
            
            # Verificar conexión
            response = await self._client.get("/api/tags")
            if response.status_code == 200:
                self._connected = True
                await self.refresh_models()
                return True
            return False
        except Exception as e:
            print(f"❌ Error conectando a Ollama: {e}")
            self._connected = False
            return False
    
    async def disconnect(self):
        """Cierra la conexión"""
        if self._client:
            await self._client.aclose()
            self._connected = False
    
    async def refresh_models(self) -> List[ModelInfo]:
        """Refresca la lista de modelos disponibles"""
        if not self._connected:
            return []
        
        try:
            response = await self._client.get("/api/tags")
            response.raise_for_status()
            data = response.json()
            
            self._available_models = [
                ModelInfo(
                    name=model["name"],
                    size=model.get("size", 0),
                    digest=model.get("digest", ""),
                    modified_at=model.get("modified_at", ""),
                    details=model.get("details", {})
                )
                for model in data.get("models", [])
            ]
            
            return self._available_models
        except Exception as e:
            print(f"❌ Error obteniendo modelos: {e}")
            return []
    
    @property
    def available_models(self) -> List[str]:
        """Retorna lista de nombres de modelos disponibles"""
        return [m.name for m in self._available_models]
    
    async def _generate_with_retry(
        self,
        endpoint: str,
        payload: Dict,
        stream: bool = False
    ) -> httpx.Response:
        """Genera request con reintentos automáticos"""
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                response = await self._client.post(
                    endpoint,
                    json=payload,
                    timeout=None if stream else httpx.Timeout(self.timeout)
                )
                response.raise_for_status()
                return response
            except httpx.HTTPError as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    await asyncio.sleep(wait_time)
        
        raise last_error
    
    async def chat(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        stream: bool = True
    ) -> AsyncGenerator[str, None]:
        """
        Envía mensajes al modelo y recibe respuesta con streaming
        """
        if not self._connected:
            raise ConnectionError("No conectado a Ollama")
        
        model = model or settings.ollama.default_model
        
        # Preparar mensajes
        api_messages = []
        if system_prompt:
            api_messages.append({
                "role": "system",
                "content": system_prompt
            })
        api_messages.extend([m.to_dict() for m in messages])
        
        payload = {
            "model": model,
            "messages": api_messages,
            "stream": stream,
            "options": {
                "temperature": temperature
            }
        }
        
        try:
            response = await self._generate_with_retry(
                "/api/chat",
                payload,
                stream=stream
            )
            
            if stream:
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if "message" in data:
                                content = data["message"].get("content", "")
                                if content:
                                    yield content
                                if data.get("done", False):
                                    break
                        except json.JSONDecodeError:
                            continue
            else:
                data = response.json()
                if "message" in data:
                    yield data["message"].get("content", "")
        
        except Exception as e:
            error_msg = f"Error en chat: {str(e)}"
            yield f"\n\n⚠️ {error_msg}"
    
    async def generate_code(
        self,
        prompt: str,
        context: str = "",
        language: str = "python",
        model: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Genera código con contexto específico"""
        system_prompt = f"""Eres un desarrollador experto en {language}.
Genera código limpio, eficiente y bien documentado.
Sigue las mejores prácticas del lenguaje.
Responde SOLO con código, sin explicaciones adicionales."""

        messages = [
            ChatMessage(role="user", content=f"Contexto:\n{context}\n\nTarea:\n{prompt}")
        ]
        
        async for chunk in self.chat(
            messages=messages,
            model=model,
            system_prompt=system_prompt,
            temperature=0.3  # Más determinista para código
        ):
            yield chunk
    
    async def explain_code(
        self,
        code: str,
        language: str = "python",
        detail_level: str = "intermediate"
    ) -> AsyncGenerator[str, None]:
        """Explica código existente"""
        system_prompt = f"""Eres un profesor experto en {language}.
Explica el código de manera clara y didáctica.
Nivel de detalle: {detail_level}.
Incluye: propósito, flujo lógico, funciones clave y posibles mejoras."""

        messages = [
            ChatMessage(role="user", content=f"Explica este código:\n\n```{language}\n{code}\n```")
        ]
        
        async for chunk in self.chat(
            messages=messages,
            system_prompt=system_prompt,
            temperature=0.5
        ):
            yield chunk
    
    async def refactor_code(
        self,
        code: str,
        instructions: str = "",
        language: str = "python"
    ) -> AsyncGenerator[str, None]:
        """Refactoriza código según instrucciones"""
        system_prompt = f"""Eres un arquitecto de software senior experto en {language}.
Refactoriza el código siguiendo estas instrucciones: {instructions or 'Mejora legibilidad, rendimiento y mantenibilidad'}.
Mantén la funcionalidad original.
Responde SOLO con el código refactorizado."""

        messages = [
            ChatMessage(role="user", content=f"Refactoriza:\n\n```{language}\n{code}\n```")
        ]
        
        async for chunk in self.chat(
            messages=messages,
            system_prompt=system_prompt,
            temperature=0.3
        ):
            yield chunk
    
    async def pull_model(self, model_name: str) -> AsyncGenerator[Dict, None]:
        """Descarga un modelo desde Ollama"""
        if not self._connected:
            raise ConnectionError("No conectado a Ollama")
        
        payload = {"name": model_name}
        
        try:
            response = await self._client.post(
                "/api/pull",
                json=payload,
                timeout=None
            )
            response.raise_for_status()
            
            async for line in response.aiter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        yield data
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            yield {"error": str(e)}
    
    async def get_model_info(self, model_name: str) -> Dict:
        """Obtiene información detallada de un modelo"""
        if not self._connected:
            return {}
        
        try:
            response = await self._client.post(
                "/api/show",
                json={"name": model_name}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    async def health_check(self) -> Dict:
        """Verifica estado del servidor Ollama"""
        if not self._connected:
            return {"status": "disconnected"}
        
        try:
            response = await self._client.get("/api/tags")
            return {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "models_count": len(self._available_models),
                "url": self.base_url
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}


# Instancia global
ollama_client = OllamaClient()
