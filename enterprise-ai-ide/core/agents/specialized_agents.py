"""
Agentes especializados para tareas de desarrollo
Cada agente tiene responsabilidades específicas y prompts optimizados
"""
from typing import List, Dict, Optional, AsyncGenerator
from dataclasses import dataclass
from enum import Enum
import asyncio

from core.llm.ollama_client import OllamaClient, ChatMessage, ollama_client
from core.context.code_context import context_manager


class AgentType(Enum):
    """Tipos de agentes disponibles"""
    CODE_GENERATOR = "code_generator"
    CODE_REVIEWER = "code_reviewer"
    DEBUGGER = "debugger"
    REFACTORER = "refactorer"
    EXPLAINER = "explainer"
    TEST_GENERATOR = "test_generator"
    DOCUMENTATION = "documentation"
    ARCHITECT = "architect"


@dataclass
class AgentConfig:
    """Configuración de un agente"""
    agent_type: AgentType
    model: str
    system_prompt: str
    temperature: float
    max_context_tokens: int = 4096


class BaseAgent:
    """Clase base para todos los agentes"""
    
    def __init__(self, config: AgentConfig, client: Optional[OllamaClient] = None):
        self.config = config
        self.client = client or ollama_client
        self.conversation_history: List[ChatMessage] = []
    
    async def execute(
        self, 
        input_data: str, 
        context: Optional[str] = None,
        stream: bool = True
    ) -> AsyncGenerator[str, None]:
        """Ejecuta la tarea del agente"""
        raise NotImplementedError
    
    def clear_history(self):
        """Limpia el historial de conversación"""
        self.conversation_history = []
    
    async def _send_request(
        self, 
        messages: List[ChatMessage],
        stream: bool = True
    ) -> AsyncGenerator[str, None]:
        """Envía request al modelo"""
        async for chunk in self.client.chat(
            messages=messages,
            model=self.config.model,
            system_prompt=self.config.system_prompt,
            temperature=self.config.temperature,
            stream=stream
        ):
            yield chunk


class CodeGeneratorAgent(BaseAgent):
    """Agente especializado en generar código"""
    
    def __init__(self, language: str = "python", model: Optional[str] = None):
        config = AgentConfig(
            agent_type=AgentType.CODE_GENERATOR,
            model=model or "codellama:7b-instruct",
            system_prompt=f"""Eres un desarrollador senior experto en {language}.
Genera código limpio, eficiente, bien documentado y siguiendo las mejores prácticas.
Incluye manejo de errores apropiado.
Responde SOLO con código, sin explicaciones a menos que se solicite explícitamente.""",
            temperature=0.3
        )
        super().__init__(config)
        self.language = language
    
    async def execute(
        self,
        input_data: str,
        context: Optional[str] = None,
        stream: bool = True
    ) -> AsyncGenerator[str, None]:
        """Genera código basado en descripción"""
        prompt = f"Tarea: {input_data}"
        if context:
            prompt = f"Contexto:\n{context}\n\n{prompt}"
        
        messages = [ChatMessage(role="user", content=prompt)]
        
        async for chunk in self._send_request(messages, stream):
            yield chunk


class CodeReviewerAgent(BaseAgent):
    """Agente especializado en revisar código"""
    
    def __init__(self, language: str = "python", model: Optional[str] = None):
        config = AgentConfig(
            agent_type=AgentType.CODE_REVIEWER,
            model=model or "codellama:7b-instruct",
            system_prompt=f"""Eres un reviewer de código senior experto en {language}.
Analiza el código buscando:
- Bugs potenciales
- Problemas de seguridad
- Malas prácticas
- Oportunidades de optimización
- Violaciones de principios SOLID
- Problemas de legibilidad

Proporciona feedback constructivo y específico con ejemplos de mejora.""",
            temperature=0.4
        )
        super().__init__(config)
        self.language = language
    
    async def execute(
        self,
        input_data: str,
        context: Optional[str] = None,
        stream: bool = True
    ) -> AsyncGenerator[str, None]:
        """Revisa código y proporciona feedback"""
        prompt = f"Revisa este código:\n\n```{self.language}\n{input_data}\n```"
        
        messages = [ChatMessage(role="user", content=prompt)]
        
        async for chunk in self._send_request(messages, stream):
            yield chunk


class DebuggerAgent(BaseAgent):
    """Agente especializado en debugging"""
    
    def __init__(self, language: str = "python", model: Optional[str] = None):
        config = AgentConfig(
            agent_type=AgentType.DEBUGGER,
            model=model or "codellama:7b-instruct",
            system_prompt=f"""Eres un experto en debugging de {language}.
Analiza el código y el error proporcionado.
Identifica la causa raíz del problema.
Proporciona una solución clara y explica por qué funciona.
Si es necesario, sugiere herramientas de debugging adicionales.""",
            temperature=0.3
        )
        super().__init__(config)
        self.language = language
    
    async def execute(
        self,
        input_data: str,
        context: Optional[str] = None,
        stream: bool = True
    ) -> AsyncGenerator[str, None]:
        """Debugga código con error"""
        prompt = f"Código y error:\n{input_data}"
        if context:
            prompt = f"Contexto adicional:\n{context}\n\n{prompt}"
        
        messages = [ChatMessage(role="user", content=prompt)]
        
        async for chunk in self._send_request(messages, stream):
            yield chunk


class RefactorerAgent(BaseAgent):
    """Agente especializado en refactorización"""
    
    def __init__(self, language: str = "python", model: Optional[str] = None):
        config = AgentConfig(
            agent_type=AgentType.REFACTORER,
            model=model or "codellama:7b-instruct",
            system_prompt=f"""Eres un arquitecto de software experto en {language}.
Refactoriza el código mejorando:
- Legibilidad
- Mantenibilidad
- Rendimiento
- Seguimiento de principios SOLID
- Reducción de duplicación
- Mejora de estructura

Mantén la funcionalidad original. Responde SOLO con el código refactorizado.""",
            temperature=0.2
        )
        super().__init__(config)
        self.language = language
    
    async def execute(
        self,
        input_data: str,
        context: Optional[str] = None,
        stream: bool = True
    ) -> AsyncGenerator[str, None]:
        """Refactoriza código"""
        prompt = f"Refactoriza este código:\n\n```{self.language}\n{input_data}\n```"
        if context:
            prompt = f"Instrucciones: {context}\n\n{prompt}"
        
        messages = [ChatMessage(role="user", content=prompt)]
        
        async for chunk in self._send_request(messages, stream):
            yield chunk


class ExplainerAgent(BaseAgent):
    """Agente especializado en explicar código"""
    
    def __init__(self, language: str = "python", model: Optional[str] = None):
        config = AgentConfig(
            agent_type=AgentType.EXPLAINER,
            model=model or "codellama:7b-instruct",
            system_prompt=f"""Eres un profesor experto en {language}.
Explica el código de manera clara y didáctica.
Incluye:
- Propósito general
- Flujo lógico
- Funciones/métodos clave
- Estructuras de datos importantes
- Posibles mejoras

Adapta el nivel técnico según la complejidad del código.""",
            temperature=0.5
        )
        super().__init__(config)
        self.language = language
    
    async def execute(
        self,
        input_data: str,
        context: Optional[str] = None,
        stream: bool = True
    ) -> AsyncGenerator[str, None]:
        """Explica código"""
        prompt = f"Explica este código:\n\n```{self.language}\n{input_data}\n```"
        
        messages = [ChatMessage(role="user", content=prompt)]
        
        async for chunk in self._send_request(messages, stream):
            yield chunk


class TestGeneratorAgent(BaseAgent):
    """Agente especializado en generar tests"""
    
    def __init__(self, language: str = "python", framework: str = "pytest", model: Optional[str] = None):
        config = AgentConfig(
            agent_type=AgentType.TEST_GENERATOR,
            model=model or "codellama:7b-instruct",
            system_prompt=f"""Eres un experto en testing de {language} usando {framework}.
Genera tests completos que cubran:
- Casos normales
- Casos edge
- Casos de error
- Pruebas de integración cuando sea apropiado

Incluye asserts significativos y nombres descriptivos.
Sigue las mejores prácticas de testing.""",
            temperature=0.3
        )
        super().__init__(config)
        self.language = language
        self.framework = framework
    
    async def execute(
        self,
        input_data: str,
        context: Optional[str] = None,
        stream: bool = True
    ) -> AsyncGenerator[str, None]:
        """Genera tests para el código"""
        prompt = f"Genera tests para este código usando {self.framework}:\n\n```{self.language}\n{input_data}\n```"
        
        messages = [ChatMessage(role="user", content=prompt)]
        
        async for chunk in self._send_request(messages, stream):
            yield chunk


class DocumentationAgent(BaseAgent):
    """Agente especializado en documentación"""
    
    def __init__(self, language: str = "python", model: Optional[str] = None):
        config = AgentConfig(
            agent_type=AgentType.DOCUMENTATION,
            model=model or "codellama:7b-instruct",
            system_prompt=f"""Eres un escritor técnico experto en {language}.
Genera documentación clara y completa incluyendo:
- Docstrings para funciones y clases
- Comentarios explicativos
- Ejemplos de uso
- Descripción de parámetros y valores de retorno

Sigue el estándar de documentación del lenguaje (PEP 257 para Python, JSDoc para JS, etc.).""",
            temperature=0.3
        )
        super().__init__(config)
        self.language = language
    
    async def execute(
        self,
        input_data: str,
        context: Optional[str] = None,
        stream: bool = True
    ) -> AsyncGenerator[str, None]:
        """Genera documentación para el código"""
        prompt = f"Documenta este código:\n\n```{self.language}\n{input_data}\n```"
        
        messages = [ChatMessage(role="user", content=prompt)]
        
        async for chunk in self._send_request(messages, stream):
            yield chunk


class ArchitectAgent(BaseAgent):
    """Agente especializado en arquitectura de software"""
    
    def __init__(self, model: Optional[str] = None):
        config = AgentConfig(
            agent_type=AgentType.ARCHITECT,
            model=model or "codellama:7b-instruct",
            system_prompt="""Eres un arquitecto de software senior con experiencia en múltiples lenguajes y patrones.
Analiza requerimientos y propone soluciones arquitectónicas considerando:
- Escalabilidad
- Mantenibilidad
- Seguridad
- Rendimiento
- Costos
- Trade-offs

Proporciona diagramas conceptuales en texto y justifica tus decisiones.""",
            temperature=0.5
        )
        super().__init__(config)
    
    async def execute(
        self,
        input_data: str,
        context: Optional[str] = None,
        stream: bool = True
    ) -> AsyncGenerator[str, None]:
        """Propone solución arquitectónica"""
        prompt = f"Diseña una arquitectura para: {input_data}"
        if context:
            prompt = f"Contexto:\n{context}\n\n{prompt}"
        
        messages = [ChatMessage(role="user", content=prompt)]
        
        async for chunk in self._send_request(messages, stream):
            yield chunk


class AgentFactory:
    """Fábrica para crear agentes"""
    
    _agents_cache: Dict[AgentType, BaseAgent] = {}
    
    @classmethod
    def create_agent(
        cls,
        agent_type: AgentType,
        language: str = "python",
        model: Optional[str] = None,
        **kwargs
    ) -> BaseAgent:
        """Crea un agente del tipo especificado"""
        cache_key = (agent_type, language, model)
        
        if cache_key in cls._agents_cache:
            return cls._agents_cache[cache_key]
        
        agent_classes = {
            AgentType.CODE_GENERATOR: CodeGeneratorAgent,
            AgentType.CODE_REVIEWER: CodeReviewerAgent,
            AgentType.DEBUGGER: DebuggerAgent,
            AgentType.REFACTORER: RefactorerAgent,
            AgentType.EXPLAINER: ExplainerAgent,
            AgentType.TEST_GENERATOR: TestGeneratorAgent,
            AgentType.DOCUMENTATION: DocumentationAgent,
            AgentType.ARCHITECT: ArchitectAgent
        }
        
        agent_class = agent_classes.get(agent_type)
        if not agent_class:
            raise ValueError(f"Agente desconocido: {agent_type}")
        
        agent = agent_class(language=language, model=model, **kwargs)
        cls._agents_cache[cache_key] = agent
        
        return agent
    
    @classmethod
    def clear_cache(cls):
        """Limpia el cache de agentes"""
        cls._agents_cache.clear()


# Funciones utilitarias para acceso rápido
async def generate_code(prompt: str, language: str = "python", context: str = "") -> AsyncGenerator[str, None]:
    """Genera código rápidamente"""
    agent = AgentFactory.create_agent(AgentType.CODE_GENERATOR, language)
    async for chunk in agent.execute(prompt, context):
        yield chunk


async def review_code(code: str, language: str = "python") -> AsyncGenerator[str, None]:
    """Revisa código rápidamente"""
    agent = AgentFactory.create_agent(AgentType.CODE_REVIEWER, language)
    async for chunk in agent.execute(code):
        yield chunk


async def explain_code(code: str, language: str = "python") -> AsyncGenerator[str, None]:
    """Explica código rápidamente"""
    agent = AgentFactory.create_agent(AgentType.EXPLAINER, language)
    async for chunk in agent.execute(code):
        yield chunk
