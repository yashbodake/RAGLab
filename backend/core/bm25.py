import re
from pydantic import BaseModel
from rank_bm25 import BM25Okapi

class BM25Result(BaseModel):
    doc_id: str
    text: str
    metadata: dict
    score: float

class BM25Index:
    """In-memory BM25 index built from chunk texts."""

    def __init__(self):
        self.index: BM25Okapi | None = None
        self.doc_ids: list[str] = []
        self.doc_texts: list[str] = []
        self.doc_metadata: list[dict] = []

    def build(self, chunks: list[dict]):
        """
        Build BM25 index from chunk documents.

        Args:
            chunks: List of {id, text, metadata} dicts.
        """
        self.doc_ids = [c["id"] for c in chunks]
        self.doc_texts = [c["text"] for c in chunks]
        self.doc_metadata = [c["metadata"] for c in chunks]

        tokenized = [self._tokenize(text) for text in self.doc_texts]
        self.index = BM25Okapi(tokenized)

    def search(self, query: str, top_n: int = 10) -> list[BM25Result]:
        """Search the BM25 index and return ranked results."""
        if self.index is None:
            raise RuntimeError("BM25 index not built. Call build() first.")

        tokens = self._tokenize(query)
        scores = self.index.get_scores(tokens)

        # Get top-N indices
        top_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True
        )[:top_n]

        return [
            BM25Result(
                doc_id=self.doc_ids[i],
                text=self.doc_texts[i],
                metadata=self.doc_metadata[i],
                score=float(scores[i]),
            )
            for i in top_indices
            if scores[i] > 0  # Exclude zero-score matches
        ]

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """Simple whitespace + lowering tokenizer."""
        text = text.lower()
        text = re.sub(r"[^\w\s]", " ", text)
        return text.split()

def build_bm25_index(chroma_store) -> BM25Index:
    """Build BM25 index from all docs_body chunks in Chroma Store."""
    collection = chroma_store.get_collection("docs_body")
    count = collection.count()

    if count == 0:
        # Avoid retrieving if empty to prevent error
        index = BM25Index()
        index.build([])
        return index

    # Fetch all documents from Chroma
    results = collection.get(
        include=["documents", "metadatas"],
        limit=count,
    )

    chunks = [
        {"id": doc_id, "text": text, "metadata": meta}
        for doc_id, text, meta in zip(
            results["ids"], results["documents"], results["metadatas"]
        )
    ]

    index = BM25Index()
    index.build(chunks)
    return index
