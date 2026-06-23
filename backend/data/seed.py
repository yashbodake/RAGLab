"""Chunking logic for the Industrial RAG Demonstrator."""

def chunk_article(article: dict, chunk_size: int = 150, overlap: int = 20) -> list[dict]:
    """
    Split an article body into overlapping chunks.

    Args:
        article: Article dict with id, title, body, metadata.
        chunk_size: Target chunk size in whitespace-separated tokens.
        overlap: Number of overlapping tokens between consecutive chunks.

    Returns:
        List of chunk dicts ready for Chroma insertion.
    """
    words = article["body"].split()
    chunks = []
    start = 0
    chunk_index = 0

    while start < len(words):
        end = start + chunk_size
        chunk_text = " ".join(words[start:end])

        # Clean/normalize metadata values for Chroma compatibility (replace None with empty string or similar if required)
        # Chroma requires metadata values to be str, int, float, or bool. None is not allowed.
        # Let's check error_code: if None, we omit or set to "" or "NONE" or we can filter it out.
        # Wait, the spec says: "error_code: null" -> but in Chroma it's better to store empty string or delete the key if it is null
        # Let's check: Chroma collections will fail if metadata values are None.
        # Let's handle None by setting it to "" or removing the key.
        # Let's see: in specs/05, "applied filter: {'error_code': 'E452'}"
        # Let's check: "Not all articles have an error_code; approximately 120 of 200 articles include one."
        # If error_code is None/null, let's set it to "" or keep it as "" so that it's Chroma-compatible.
        # Let's check if the query filter extracts E452. If we set error_code to "", it is a string and valid in Chroma.
        # Let's make sure that if a key's value is None, we store it as empty string "" in Chroma metadata.
        metadata = {}
        for k, v in article["metadata"].items():
            metadata[k] = "" if v is None else v
            
        metadata["chunk_index"] = chunk_index
        metadata["article_id"] = article["id"]

        chunk = {
            "id": f"{article['id']}_chunk_{chunk_index}",
            "text": chunk_text,
            "metadata": metadata,
        }
        chunks.append(chunk)

        chunk_index += 1
        start = end - overlap  # Slide forward by (chunk_size - overlap)

        # Prevent infinite loop on very short remaining text
        if start >= len(words):
            break

    return chunks
