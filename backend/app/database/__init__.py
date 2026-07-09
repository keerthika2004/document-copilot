"""Database and models package.

Exports all models and the Base metadata class from the models subpackage.
"""

from app.database.base import Base
from app.database.models import (
    User,
    ChatThread,
    ChatMessage,
    MessageCitation,
    SourceDocument,
    DocumentChunk,
)

__all__ = [
    "Base",
    "User",
    "ChatThread",
    "ChatMessage",
    "MessageCitation",
    "SourceDocument",
    "DocumentChunk",
]
