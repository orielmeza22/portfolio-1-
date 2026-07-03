"""
API REST asíncrona con FastAPI para Enterprise AI IDE
Proporciona endpoints para chat, generación de código, RAG y gestión de agentes
"""
from fastapi import FastAPI, WebSocket, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import asyncio
import json

from config.settings import settings
from core.llm.ollama_client import ollama_client, ChatMessage
from core.context.code_context import context_manager
from core.agents.specialized_agents import (
    AgentFactory, 
    AgentType,
    generate_code,
    review_code,
    explain_code
)


# ==================== Modelos de Request/Response ====================

class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]
    model: Optional[str] = None
    system_prompt: Optional[str] = None
    temperature: float = 0.7
    stream: bool = True


class CodeGenerationRequest(BaseModel):
    prompt: str
    language: str = "python"
    context: Optional[str] = None
    model: Optional[str] = None


class CodeReviewRequest(BaseModel):
    code: str
    language: str = "python"
    focus_areas: Optional[List[str]] = None


class CodeExplanationRequest(BaseModel):
    code: str
    language: str = "python"
    detail_level: str = "intermediate"


class RefactorRequest(BaseModel):
    code: str
    language: str = "python"
    instructions: Optional[str] = None


class SearchRequest(BaseModel):
    query: str
    language_filter: Optional[str] = None
    limit: int = 5


class IndexFileRequest(BaseModel):
    file_path: str
    content: str


class AgentRequest(BaseModel):
    agent_type: str
    input_data: str
    language: str = "python"
    context: Optional[str] = None
    model: Optional[str] = None


# ==================== Aplicación FastAPI ====================

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="API para IDE empresarial con IA local (Ollama)"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Eventos de Inicio/Cierre ====================

@app.on_event("startup")
async def startup_event():
    """Inicializa componentes al iniciar la aplicación"""
    print(f"🚀 Iniciando {settings.app_name} v{settings.version}")
    
    # Conectar a Ollama
    connected = await ollama_client.connect()
    if connected:
        print(f"✅ Conectado a Ollama: {ollama_client.base_url}")
        print(f"📦 Modelos disponibles: {ollama_client.available_models}")
    else:
        print("⚠️  No se pudo conectar a Ollama")
    
    # Inicializar contexto RAG
    await context_manager.initialize()
    
    # Verificar recursos del sistema
    resources = settings.check_system_resources()
    print(f"💻 Recursos: {resources['memory_available_gb']}GB RAM disponible")


@app.on_event("shutdown")
async def shutdown_event():
    """Limpia recursos al cerrar la aplicación"""
    print("\n🛑 Cerrando aplicación...")
    await ollama_client.disconnect()


# ==================== Endpoints de Salud ====================

@app.get("/health")
async def health_check():
    """Verifica estado de la aplicación"""
    ollama_health = await ollama_client.health_check()
    context_stats = await context_manager.get_stats()
    
    return {
        "status": "healthy",
        "version": settings.version,
        "ollama": ollama_health,
        "context": context_stats,
        "system": settings.check_system_resources()
    }


@app.get("/models")
async def list_models():
    """Lista modelos disponibles en Ollama"""
    await ollama_client.refresh_models()
    return {"models": ollama_client.available_models}


@app.get("/ollama/detect")
async def detect_ollama_instances():
    """Detecta instancias locales de Ollama automáticamente"""
    instances = await settings.detect_ollama_instances()
    return {"instances": instances}


# ==================== Endpoints de Chat ====================

@app.post("/chat")
async def chat(request: ChatRequest):
    """Endpoint de chat básico (no streaming)"""
    messages = [ChatMessage(**msg) for msg in request.messages]
    
    response_text = ""
    async for chunk in ollama_client.chat(
        messages=messages,
        model=request.model,
        system_prompt=request.system_prompt,
        temperature=request.temperature,
        stream=False
    ):
        response_text += chunk
    
    return {"response": response_text}


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Endpoint de chat con streaming"""
    messages = [ChatMessage(**msg) for msg in request.messages]
    
    async def generate():
        async for chunk in ollama_client.chat(
            messages=messages,
            model=request.model,
            system_prompt=request.system_prompt,
            temperature=request.temperature,
            stream=True
        ):
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )


# ==================== Endpoints de Código ====================

@app.post("/code/generate")
async def generate_code_endpoint(request: CodeGenerationRequest):
    """Genera código a partir de descripción"""
    agent = AgentFactory.create_agent(
        AgentType.CODE_GENERATOR,
        language=request.language,
        model=request.model
    )
    
    response_text = ""
    async for chunk in agent.execute(request.prompt, request.context, stream=False):
        response_text += chunk
    
    return {"code": response_text}


@app.post("/code/generate/stream")
async def generate_code_stream(request: CodeGenerationRequest):
    """Genera código con streaming"""
    agent = AgentFactory.create_agent(
        AgentType.CODE_GENERATOR,
        language=request.language,
        model=request.model
    )
    
    async def generate():
        async for chunk in agent.execute(request.prompt, request.context, stream=True):
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@app.post("/code/review")
async def review_code_endpoint(request: CodeReviewRequest):
    """Revisa código y proporciona feedback"""
    agent = AgentFactory.create_agent(
        AgentType.CODE_REVIEWER,
        language=request.language
    )
    
    context = ""
    if request.focus_areas:
        context = f"Enfócate en: {', '.join(request.focus_areas)}"
    
    response_text = ""
    async for chunk in agent.execute(request.code, context, stream=False):
        response_text += chunk
    
    return {"review": response_text}


@app.post("/code/explain")
async def explain_code_endpoint(request: CodeExplanationRequest):
    """Explica código"""
    agent = AgentFactory.create_agent(
        AgentType.EXPLAINER,
        language=request.language
    )
    
    response_text = ""
    async for chunk in agent.execute(request.code, stream=False):
        response_text += chunk
    
    return {"explanation": response_text}


@app.post("/code/refactor")
async def refactor_code_endpoint(request: RefactorRequest):
    """Refactoriza código"""
    agent = AgentFactory.create_agent(
        AgentType.REFACTORER,
        language=request.language
    )
    
    response_text = ""
    async for chunk in agent.execute(request.code, request.instructions, stream=False):
        response_text += chunk
    
    return {"refactored_code": response_text}


# ==================== Endpoints RAG ====================

@app.post("/context/index")
async def index_file(request: IndexFileRequest):
    """Indexa un archivo para búsqueda semántica"""
    chunks_count = await context_manager.index_file(
        request.file_path,
        request.content
    )
    return {
        "status": "success",
        "file_path": request.file_path,
        "chunks_indexed": chunks_count
    }


@app.post("/context/search")
async def search_context(request: SearchRequest):
    """Busca código relevante usando RAG"""
    results = await context_manager.search_relevant_code(
        request.query,
        limit=request.limit,
        language_filter=request.language_filter
    )
    return {"results": results}


@app.get("/context/stats")
async def get_context_stats():
    """Obtiene estadísticas del índice de contexto"""
    stats = await context_manager.get_stats()
    return stats


# ==================== Endpoints de Agentes ====================

@app.post("/agent/execute")
async def execute_agent(request: AgentRequest):
    """Ejecuta un agente especializado"""
    try:
        agent_type = AgentType(request.agent_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Agente desconocido: {request.agent_type}")
    
    agent = AgentFactory.create_agent(
        agent_type,
        language=request.language,
        model=request.model
    )
    
    response_text = ""
    async for chunk in agent.execute(request.input_data, request.context, stream=False):
        response_text += chunk
    
    return {
        "agent_type": request.agent_type,
        "response": response_text
    }


@app.post("/agent/execute/stream")
async def execute_agent_stream(request: AgentRequest):
    """Ejecuta un agente con streaming"""
    try:
        agent_type = AgentType(request.agent_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Agente desconocido: {request.agent_type}")
    
    agent = AgentFactory.create_agent(
        agent_type,
        language=request.language,
        model=request.model
    )
    
    async def generate():
        async for chunk in agent.execute(request.input_data, request.context, stream=True):
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


# ==================== WebSocket para Chat en Tiempo Real ====================

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket para chat en tiempo real con streaming"""
    await websocket.accept()
    
    conversation_history = []
    
    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                request_data = json.loads(data)
                message = request_data.get("message", "")
                model = request_data.get("model")
                system_prompt = request_data.get("system_prompt")
                
                # Agregar mensaje del usuario
                conversation_history.append({
                    "role": "user",
                    "content": message
                })
                
                messages = [ChatMessage(**msg) for msg in conversation_history]
                
                # Enviar respuesta con streaming
                full_response = ""
                async for chunk in ollama_client.chat(
                    messages=messages,
                    model=model,
                    system_prompt=system_prompt,
                    stream=True
                ):
                    full_response += chunk
                    await websocket.send_json({
                        "type": "chunk",
                        "content": chunk
                    })
                
                # Agregar respuesta al historial
                conversation_history.append({
                    "role": "assistant",
                    "content": full_response
                })
                
                await websocket.send_json({
                    "type": "complete",
                    "content": full_response
                })
                
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "JSON inválido"
                })
    
    except Exception as e:
        print(f"Error en WebSocket: {e}")
    finally:
        await websocket.close()


# ==================== Punto de entrada principal ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.server:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
