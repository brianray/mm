"""Backwards-compatible alias for ``mm.document_base`` (Marmir 0.x). Prefer ``mm.document``."""

from .document import Document, DocumentWriter

__all__ = ["Document", "DocumentWriter"]
