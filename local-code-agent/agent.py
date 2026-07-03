"""
Agente de código que usa IA local para asistir en desarrollo
"""

from typing import Optional, List
from ollama_client import OllamaClient
from file_handler import FileHandler
from config import DEFAULT_MODEL


class CodeAgent:
    """Agente de código asistido por IA local"""
    
    def __init__(self, model: str = DEFAULT_MODEL):
        self.client = OllamaClient()
        self.file_handler = FileHandler()
        self.model = model
        self.conversation_history: List[dict] = []
        
        # Prompts del sistema para diferentes tareas
        self.system_prompts = {
            "chat": """Eres un asistente de programación experto. Ayudas a desarrolladores con:
- Explicar conceptos de programación
- Resolver dudas sobre código
- Sugerir mejores prácticas
- Debuggear problemas

Responde de forma clara y concisa. Incluye ejemplos de código cuando sea relevante.""",
            
            "explain": """Eres un experto en análisis de código. Tu tarea es explicar el código proporcionado:
1. Describe qué hace el código en general
2. Explica las partes importantes
3. Menciona patrones o técnicas utilizadas
4. Sugiere posibles mejoras si las hay

Sé claro y educativo en tus explicaciones.""",
            
            "generate": """Eres un desarrollador senior experto en múltiples lenguajes de programación.
Tu tarea es generar código limpio, eficiente y bien documentado según las especificaciones.

Incluye:
- Código funcional y probado mentalmente
- Comentarios cuando sea necesario
- Manejo apropiado de errores
- Sigue las mejores prácticas del lenguaje""",
            
            "refactor": """Eres un experto en refactorización y clean code.
Analiza el código proporcionado y sugiere mejoras considerando:
- Legibilidad y claridad
- Principios SOLID
- DRY (Don't Repeat Yourself)
- Manejo de errores
- Performance
- Seguridad

Proporciona el código refactorizado y explica los cambios realizados."""
        }
    
    def check_connection(self) -> bool:
        """Verificar conexión con Ollama"""
        return self.client.check_connection()
    
    def list_models(self) -> list:
        """Listar modelos disponibles"""
        return self.client.list_models()
    
    def set_model(self, model_name: str) -> bool:
        """Cambiar el modelo actual"""
        available = self.list_models()
        if model_name in available or model_name:  # Permitir cualquier nombre (puede no estar descargado aún)
            self.model = model_name
            return True
        return False
    
    def chat(self, message: str, use_history: bool = True) -> str:
        """
        Conversación tipo chat con historial
        
        Args:
            message: Mensaje del usuario
            use_history: Si True, usa el historial de conversación
            
        Returns:
            Respuesta de la IA
        """
        system_prompt = self.system_prompts["chat"]
        
        if use_history:
            self.conversation_history.append({"role": "user", "content": message})
            
            response = ""
            for chunk in self.client.chat(
                messages=[{"role": "system", "content": system_prompt}] + self.conversation_history,
                model=self.model,
                stream=True
            ):
                response += chunk
                print(chunk, end='', flush=True)
            
            print()  # Nueva línea después de la respuesta
            
            self.conversation_history.append({"role": "assistant", "content": response})
            return response
        else:
            response = ""
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ]
            
            for chunk in self.client.chat(messages, model=self.model, stream=True):
                response += chunk
                print(chunk, end='', flush=True)
            
            print()
            return response
    
    def explain_file(self, filepath: str) -> str:
        """
        Explicar el contenido de un archivo
        
        Args:
            filepath: Ruta del archivo a explicar
            
        Returns:
            Explicación del código
        """
        content = self.file_handler.read_file(filepath)
        
        if content.startswith("Error"):
            return content
        
        prompt = f"""Explica el siguiente código del archivo '{filepath}':

```
{content}
```
"""
        
        response = ""
        system_prompt = self.system_prompts["explain"]
        
        for chunk in self.client.generate(prompt, model=self.model, system_prompt=system_prompt, stream=True):
            response += chunk
            print(chunk, end='', flush=True)
        
        print()
        return response
    
    def generate_code(self, description: str) -> str:
        """
        Generar código basado en una descripción
        
        Args:
            description: Descripción de lo que se debe generar
            
        Returns:
            Código generado
        """
        prompt = f"Genera código para: {description}"
        
        response = ""
        system_prompt = self.system_prompts["generate"]
        
        for chunk in self.client.generate(prompt, model=self.model, system_prompt=system_prompt, stream=True):
            response += chunk
            print(chunk, end='', flush=True)
        
        print()
        return response
    
    def refactor_file(self, filepath: str) -> str:
        """
        Sugerir refactorización para un archivo
        
        Args:
            filepath: Ruta del archivo a refactorizar
            
        Returns:
            Sugerencias de refactorización
        """
        content = self.file_handler.read_file(filepath)
        
        if content.startswith("Error"):
            return content
        
        prompt = f"""Refactoriza y mejora el siguiente código del archivo '{filepath}':

```
{content}
```
"""
        
        response = ""
        system_prompt = self.system_prompts["refactor"]
        
        for chunk in self.client.generate(prompt, model=self.model, system_prompt=system_prompt, stream=True):
            response += chunk
            print(chunk, end='', flush=True)
        
        print()
        return response
    
    def clear_history(self):
        """Limpiar el historial de conversación"""
        self.conversation_history = []
    
    def get_current_model(self) -> str:
        """Obtener el modelo actual"""
        return self.model
