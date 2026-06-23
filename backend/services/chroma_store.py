import sys
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import os
import json
import chromadb
from backend.data.seed import chunk_article

class ChromaStore:
    """Manages Chroma vector database collections and persistence."""

    def __init__(self, persist_path: str = "/data/chroma_db"):
        self.client = chromadb.PersistentClient(path=persist_path)
        self._collections: dict[str, chromadb.Collection] = {}

    def initialize(self, embedding_service):
        """Initialize or load collections. Seed if empty."""
        # Create or fetch collections
        self._collections["docs_body"] = self.client.get_or_create_collection(
            name="docs_body",
            metadata={
                "hnsw:space": "cosine",
                "hnsw:construction_ef": 200,
                "hnsw:search_ef": 100,
            },
        )
        self._collections["docs_title"] = self.client.get_or_create_collection(
            name="docs_title",
            metadata={"hnsw:space": "cosine"},
        )

        # Seed database if docs_body is empty
        if self._collections["docs_body"].count() == 0:
            self._seed(embedding_service)

    def _seed(self, embedding_service):
        """Load articles, chunk, embed, and upsert into collections."""
        # Dynamically locate articles.json
        possible_paths = [
            "/app/data/articles.json",
            "backend/data/articles.json",
            "data/articles.json",
            "../data/articles.json",
            "../backend/data/articles.json"
        ]
        
        articles_path = None
        for path in possible_paths:
            if os.path.exists(path):
                articles_path = path
                break
                
        if not articles_path:
            # Check relative to this file's directory as absolute path
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            file_relative = os.path.join(base_dir, "data", "articles.json")
            if os.path.exists(file_relative):
                articles_path = file_relative

        if not articles_path:
            raise FileNotFoundError(
                f"articles.json not found in any expected location. Checked: {possible_paths}"
            )

        with open(articles_path, "r") as f:
            articles = json.load(f)

        # Seed docs_body collection
        all_chunks = []
        for article in articles:
            all_chunks.extend(chunk_article(article))

        # Batch embed and upsert (batch size 32)
        for i in range(0, len(all_chunks), 32):
            batch = all_chunks[i : i + 32]
            texts = [c["text"] for c in batch]
            embeddings = embedding_service.encode(texts).tolist()

            self._collections["docs_body"].upsert(
                ids=[c["id"] for c in batch],
                documents=texts,
                embeddings=embeddings,
                metadatas=[c["metadata"] for c in batch],
            )

        # Seed docs_title collection
        titles = [a["title"] for a in articles]
        title_embeddings = embedding_service.encode(titles).tolist()

        self._collections["docs_title"].upsert(
            ids=[a["id"] for a in articles],
            documents=titles,
            embeddings=title_embeddings,
            metadatas=[a["metadata"] for a in articles],
        )

    def get_collection(self, name: str) -> chromadb.Collection:
        return self._collections[name]

    def get_stats(self) -> dict:
        return {
            name: col.count()
            for name, col in self._collections.items()
        }

    def add_documents(self, articles: list[dict], embedding_service) -> int:
        """Add new articles, chunk them, encode them, and upsert them into both collections."""
        # 1. Body chunks
        all_chunks = []
        for article in articles:
            all_chunks.extend(chunk_article(article))

        # Batch embed and upsert (batch size 32)
        for i in range(0, len(all_chunks), 32):
            batch = all_chunks[i : i + 32]
            texts = [c["text"] for c in batch]
            embeddings = embedding_service.encode(texts).tolist()

            self._collections["docs_body"].upsert(
                ids=[c["id"] for c in batch],
                documents=texts,
                embeddings=embeddings,
                metadatas=[c["metadata"] for c in batch],
            )

        # 2. Titles
        titles = [a["title"] for a in articles]
        title_embeddings = embedding_service.encode(titles).tolist()

        self._collections["docs_title"].upsert(
            ids=[a["id"] for a in articles],
            documents=titles,
            embeddings=title_embeddings,
            metadatas=[a["metadata"] for a in articles],
        )

        return len(all_chunks)
