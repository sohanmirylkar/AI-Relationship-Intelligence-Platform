import hashlib
import mimetypes
import re
from pathlib import Path
from uuid import UUID

from fastapi import UploadFile
from pypdf import PdfReader

from backend.app.core.config import get_settings
from backend.app.models.schemas import Chunk, DocumentRecord
from backend.app.services.storage import store


async def persist_upload(file: UploadFile, company_id: UUID | None = None) -> DocumentRecord:
    settings = get_settings()
    raw = await file.read()
    digest = hashlib.sha256(raw).hexdigest()
    safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", file.filename or f"upload_{digest[:8]}")
    path = settings.upload_dir / f"{digest[:10]}_{safe_name}"
    path.write_bytes(raw)
    mime_type = file.content_type or mimetypes.guess_type(safe_name)[0] or "application/octet-stream"
    document = DocumentRecord(
        company_id=company_id,
        file_name=safe_name,
        mime_type=mime_type,
        storage_uri=str(path),
        hash=digest,
    )
    saved = store.append("documents", document)
    text = extract_text(path, mime_type)
    chunks = chunk_text(text)
    for index, content in enumerate(chunks):
        store.append(
            "chunks",
            Chunk(
                document_id=saved["id"],
                chunk_index=index,
                content=content,
                metadata={
                    "doc_title": safe_name,
                    "source_type": _source_type(mime_type, safe_name),
                    "security_scope": "internal",
                    "hash": digest,
                },
            ),
        )
    return DocumentRecord(**saved)


def extract_text(path: Path, mime_type: str) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf" or mime_type == "application/pdf":
        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if suffix in {".txt", ".md", ".json", ".csv"}:
        return path.read_text(encoding="utf-8", errors="ignore")
    if suffix == ".docx":
        try:
            import docx

            doc = docx.Document(str(path))
            return "\n".join(p.text for p in doc.paragraphs)
        except Exception:
            return ""
    if suffix in {".xlsx", ".xls"}:
        try:
            import pandas as pd

            frames = pd.read_excel(path, sheet_name=None)
            return "\n\n".join(frame.to_csv(index=False) for frame in frames.values())
        except Exception:
            return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def chunk_text(text: str, chunk_words: int = 650, overlap_words: int = 90) -> list[str]:
    words = re.findall(r"\S+", text or "")
    if not words:
        return []
    chunks = []
    step = max(1, chunk_words - overlap_words)
    for start in range(0, len(words), step):
        chunk = " ".join(words[start : start + chunk_words])
        if chunk:
            chunks.append(chunk)
    return chunks


def _source_type(mime_type: str, filename: str) -> str:
    suffix = Path(filename).suffix.lower().lstrip(".")
    if suffix in {"txt", "md", "json"}:
        return "transcript"
    if suffix == "pdf":
        return "pdf"
    if suffix in {"xlsx", "xls", "csv"}:
        return "spreadsheet"
    if suffix in {"docx", "pptx"}:
        return "document"
    return mime_type
