import os
import json
import logging
from threading import Lock
from datetime import datetime

logger = logging.getLogger("backend.services.doc_store")

class DocumentMetadataStore:
    """Thread-safe persistent store for tracking user-uploaded document metadata."""

    def __init__(self, filepath: str = "/data/uploaded_docs.json"):
        self.filepath = filepath
        self.lock = Lock()
        
        # Ensure parent directory exists
        parent_dir = os.path.dirname(os.path.abspath(self.filepath))
        try:
            os.makedirs(parent_dir, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create directory {parent_dir}: {e}")

    def _read(self) -> list[dict]:
        if not os.path.exists(self.filepath):
            return []
        try:
            with open(self.filepath, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read metadata file {self.filepath}: {e}")
            return []

    def _write(self, data: list[dict]):
        try:
            # Atomic write using a temp file
            temp_path = self.filepath + ".tmp"
            with open(temp_path, "w") as f:
                json.dump(data, f, indent=2)
            os.replace(temp_path, self.filepath)
        except Exception as e:
            logger.error(f"Failed to write metadata file {self.filepath}: {e}")

    def load_docs(self) -> list[dict]:
        """Load list of all document metadata dicts."""
        with self.lock:
            return self._read()

    def add_or_update_doc(
        self,
        doc_id: str,
        filename: str,
        title: str,
        status: str,
        active: bool = True,
        error_message: str | None = None,
        chunk_count: int = 0
    ) -> dict:
        """Add a new document entry or update an existing one."""
        with self.lock:
            docs = self._read()
            
            # Check if doc exists
            existing_idx = -1
            for idx, doc in enumerate(docs):
                if doc["id"] == doc_id:
                    existing_idx = idx
                    break

            new_doc = {
                "id": doc_id,
                "filename": filename,
                "title": title,
                "upload_time": docs[existing_idx]["upload_time"] if existing_idx != -1 else datetime.utcnow().isoformat() + "Z",
                "status": status,
                "active": docs[existing_idx]["active"] if existing_idx != -1 else active,
                "error_message": error_message,
                "chunk_count": chunk_count
            }

            if existing_idx != -1:
                docs[existing_idx] = new_doc
            else:
                docs.append(new_doc)

            self._write(docs)
            return new_doc

    def toggle_doc(self, doc_id: str) -> bool:
        """Toggles the active state of a document. Returns the new active state."""
        with self.lock:
            docs = self._read()
            new_state = True
            found = False
            for doc in docs:
                if doc["id"] == doc_id:
                    doc["active"] = not doc["active"]
                    new_state = doc["active"]
                    found = True
                    break
            if found:
                self._write(docs)
            return new_state

    def delete_doc(self, doc_id: str) -> bool:
        """Removes document metadata. Returns True if deleted, False if not found."""
        with self.lock:
            docs = self._read()
            initial_len = len(docs)
            docs = [doc for doc in docs if doc["id"] != doc_id]
            self._write(docs)
            return len(docs) < initial_len

    def get_disabled_ids(self) -> set[str]:
        """Returns a set of all document IDs that are currently disabled."""
        with self.lock:
            docs = self._read()
            return {doc["id"] for doc in docs if not doc.get("active", True)}

    def get_disabled_sources(self) -> set[str]:
        """Returns a set of all source filenames that are currently disabled."""
        with self.lock:
            docs = self._read()
            return {doc["filename"] for doc in docs if not doc.get("active", True)}

