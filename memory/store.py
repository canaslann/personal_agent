"""
Basit, local, ücretsiz memory sistemi.
ChromaDB embedded mod kullanıyor - sunucu gerekmiyor, hepsi disk üzerinde.
"""
import chromadb
from pathlib import Path

_DB_PATH = Path(__file__).parent / "chroma_store"


class AgentMemory:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=str(_DB_PATH))
        self.collection = self.client.get_or_create_collection(name="conversation_memory")
        self._counter = self.collection.count()

    def remember(self, text: str, metadata: dict = None):
        """Bir bilgiyi hafızaya kaydeder."""
        self._counter += 1
        # Chroma boş dict metadata kabul etmiyor, en az bir alan olmalı
        meta = metadata if metadata else {"source": "conversation"}
        self.collection.add(
            documents=[text],
            metadatas=[meta],
            ids=[f"mem_{self._counter}"],
        )

    def recall(self, query: str, n_results: int = 3) -> list[str]:
        """Sorguya en yakın hafıza kayıtlarını getirir."""
        if self.collection.count() == 0:
            return []
        n = min(n_results, self.collection.count())
        results = self.collection.query(query_texts=[query], n_results=n)
        return results["documents"][0] if results["documents"] else []
