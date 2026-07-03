"""
Gestor de contexto de código para RAG (Retrieval-Augmented Generation)
Indexa y recupera fragmentos de código relevantes usando embeddings
"""
import asyncio
from typing import List, Dict, Optional
from pathlib import Path
import hashlib
from dataclasses import dataclass
from datetime import datetime

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    from sentence_transformers import SentenceTransformer
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

from config.settings import settings


@dataclass
class CodeChunk:
    """Fragmento de código indexado"""
    file_path: str
    content: str
    language: str
    start_line: int
    end_line: int
    hash: str
    timestamp: datetime


class CodeContextManager:
    """Gestiona el contexto de código para IA"""
    
    def __init__(self):
        self.client: Optional[QdrantClient] = None
        self.embedding_model: Optional[SentenceTransformer] = None
        self.collection_name = settings.vector_db.collection_name
        self._initialized = False
        
        # Mapeo de extensiones a lenguajes
        self.language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'cpp',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php',
            '.cs': 'csharp',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala'
        }
    
    async def initialize(self):
        """Inicializa cliente de Qdrant y modelo de embeddings"""
        if not QDRANT_AVAILABLE:
            print("⚠️  Qdrant o sentence-transformers no disponibles. RAG deshabilitado.")
            return
        
        try:
            # Inicializar cliente Qdrant
            self.client = QdrantClient(
                host=settings.vector_db.host,
                port=settings.vector_db.port
            )
            
            # Inicializar modelo de embeddings
            self.embedding_model = SentenceTransformer(
                settings.vector_db.embedding_model
            )
            
            # Crear colección si no existe
            collections = self.client.get_collections().collections
            collection_exists = any(
                c.name == self.collection_name for c in collections
            )
            
            if not collection_exists:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=384,  # Dimensiones del modelo all-MiniLM-L6-v2
                        distance=Distance.COSINE
                    )
                )
            
            self._initialized = True
            print(f"✅ Context Manager inicializado: {self.collection_name}")
            
        except Exception as e:
            print(f"❌ Error inicializando Context Manager: {e}")
            self._initialized = False
    
    def _get_language(self, file_path: str) -> str:
        """Detecta lenguaje desde la extensión del archivo"""
        ext = Path(file_path).suffix.lower()
        return self.language_map.get(ext, 'unknown')
    
    def _chunk_code(self, content: str, language: str, max_chunk_size: int = 500) -> List[CodeChunk]:
        """Divide código en chunks manejables"""
        chunks = []
        lines = content.split('\n')
        
        current_chunk = []
        current_size = 0
        start_line = 1
        
        for i, line in enumerate(lines, 1):
            line_size = len(line)
            
            if current_size + line_size > max_chunk_size and current_chunk:
                chunk_content = '\n'.join(current_chunk)
                chunks.append(CodeChunk(
                    file_path="",  # Se asigna después
                    content=chunk_content,
                    language=language,
                    start_line=start_line,
                    end_line=i-1,
                    hash=hashlib.md5(chunk_content.encode()).hexdigest(),
                    timestamp=datetime.now()
                ))
                current_chunk = [line]
                current_size = line_size
                start_line = i
            else:
                current_chunk.append(line)
                current_size += line_size
        
        # Último chunk
        if current_chunk:
            chunk_content = '\n'.join(current_chunk)
            chunks.append(CodeChunk(
                file_path="",
                content=chunk_content,
                language=language,
                start_line=start_line,
                end_line=len(lines),
                hash=hashlib.md5(chunk_content.encode()).hexdigest(),
                timestamp=datetime.now()
            ))
        
        return chunks
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Genera embedding vector para texto"""
        if not self.embedding_model:
            return []
        return self.embedding_model.encode(text).tolist()
    
    async def index_file(self, file_path: str, content: str) -> int:
        """Indexa un archivo completo"""
        if not self._initialized:
            await self.initialize()
        
        if not self._initialized:
            return 0
        
        language = self._get_language(file_path)
        chunks = self._chunk_code(content, language)
        
        points = []
        for chunk in chunks:
            chunk.file_path = file_path
            embedding = self._generate_embedding(
                f"{language} {chunk.content[:200]}"  # Contexto breve
            )
            
            if embedding:
                point = PointStruct(
                    id=int(hashlib.md5(
                        f"{file_path}:{chunk.start_line}".encode()
                    ).hexdigest(), 16) % (2**63),
                    vector=embedding,
                    payload={
                        "file_path": file_path,
                        "content": chunk.content,
                        "language": language,
                        "start_line": chunk.start_line,
                        "end_line": chunk.end_line,
                        "hash": chunk.hash
                    }
                )
                points.append(point)
        
        if points:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
        
        return len(chunks)
    
    async def search_relevant_code(
        self, 
        query: str, 
        limit: int = 5,
        language_filter: Optional[str] = None
    ) -> List[Dict]:
        """Busca código relevante para una consulta"""
        if not self._initialized:
            return []
        
        query_embedding = self._generate_embedding(query)
        
        if not query_embedding:
            return []
        
        search_filter = None
        if language_filter:
            search_filter = {
                "must": [
                    {"key": "language", "match": {"value": language_filter}}
                ]
            }
        
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=limit,
            query_filter=search_filter
        )
        
        return [
            {
                "file_path": hit.payload["file_path"],
                "content": hit.payload["content"],
                "language": hit.payload["language"],
                "start_line": hit.payload["start_line"],
                "end_line": hit.payload["end_line"],
                "score": hit.score
            }
            for hit in results
        ]
    
    async def get_file_context(self, file_path: str) -> List[Dict]:
        """Obtiene todo el contexto indexado de un archivo"""
        if not self._initialized:
            return []
        
        # Búsqueda simple por path
        # En producción usaríamos filtros más sofisticados
        return []
    
    async def remove_file(self, file_path: str):
        """Elimina un archivo del índice"""
        if not self._initialized:
            return
        
        # Implementación simplificada - en producción usaríamos filtros
        pass
    
    async def get_stats(self) -> Dict:
        """Obtiene estadísticas del índice"""
        if not self._initialized:
            return {"indexed_files": 0, "total_chunks": 0}
        
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "indexed_files": "N/A",  # Requeriría tracking adicional
                "total_chunks": info.points_count,
                "vector_size": info.config.params.vectors.size
            }
        except Exception:
            return {"indexed_files": 0, "total_chunks": 0}


# Instancia global
context_manager = CodeContextManager()
