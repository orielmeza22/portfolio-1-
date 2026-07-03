"""
Cliente para comunicarse con la API de Ollama
"""

import requests
import json
from typing import Optional, Generator, Dict, Any
from config import OLLAMA_BASE_URL, REQUEST_TIMEOUT, TEMPERATURE, MAX_TOKENS


class OllamaClient:
    """Cliente para interactuar con la API de Ollama"""
    
    def __init__(self, base_url: str = OLLAMA_BASE_URL):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        
    def check_connection(self) -> bool:
        """Verificar si Ollama está disponible"""
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=10)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def list_models(self) -> list:
        """Obtener lista de modelos disponibles"""
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return [model['name'] for model in data.get('models', [])]
            return []
        except requests.exceptions.RequestException:
            return []
    
    def generate(
        self, 
        prompt: str, 
        model: str = "codellama",
        system_prompt: Optional[str] = None,
        stream: bool = True
    ) -> Generator[str, None, None] | str:
        """
        Generar una respuesta usando el modelo especificado
        
        Args:
            prompt: El prompt del usuario
            model: Nombre del modelo a usar
            system_prompt: Prompt del sistema para contextualizar
            stream: Si True, devuelve un generador para streaming
            
        Returns:
            Generator o string con la respuesta
        """
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": TEMPERATURE,
                "num_predict": MAX_TOKENS
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        if not stream:
            try:
                response = self.session.post(url, json=payload, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                return response.json().get('response', '')
            except requests.exceptions.RequestException as e:
                return f"Error: {str(e)}"
        else:
            def stream_response():
                try:
                    response = self.session.post(url, json=payload, timeout=REQUEST_TIMEOUT, stream=True)
                    response.raise_for_status()
                    
                    for line in response.iter_lines():
                        if line:
                            try:
                                data = json.loads(line)
                                if 'response' in data:
                                    yield data['response']
                                if data.get('done', False):
                                    break
                            except json.JSONDecodeError:
                                continue
                except requests.exceptions.RequestException as e:
                    yield f"\nError: {str(e)}"
            
            return stream_response()
    
    def chat(
        self,
        messages: list,
        model: str = "codellama",
        stream: bool = True
    ) -> Generator[str, None, None] | str:
        """
        Conversación tipo chat con historial
        
        Args:
            messages: Lista de mensajes [{role: 'user|assistant', content: '...'}]
            model: Nombre del modelo
            stream: Si True, devuelve streaming
            
        Returns:
            Generator o string con la respuesta
        """
        url = f"{self.base_url}/api/chat"
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": TEMPERATURE,
                "num_predict": MAX_TOKENS
            }
        }
        
        if not stream:
            try:
                response = self.session.post(url, json=payload, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                return response.json().get('message', {}).get('content', '')
            except requests.exceptions.RequestException as e:
                return f"Error: {str(e)}"
        else:
            def stream_response():
                try:
                    response = self.session.post(url, json=payload, timeout=REQUEST_TIMEOUT, stream=True)
                    response.raise_for_status()
                    
                    for line in response.iter_lines():
                        if line:
                            try:
                                data = json.loads(line)
                                if 'message' in data and 'content' in data['message']:
                                    yield data['message']['content']
                                if data.get('done', False):
                                    break
                            except json.JSONDecodeError:
                                continue
                except requests.exceptions.RequestException as e:
                    yield f"\nError: {str(e)}"
            
            return stream_response()
