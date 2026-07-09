"""PydanticAI assistant agent and instructions package."""

from app.assistant.agent import document_agent
from app.assistant.deps import DocumentAgentDeps
from app.assistant.outputs import Citation, GroundedAnswer, SourcePassage

__all__ = [
    "Citation",
    "DocumentAgentDeps",
    "GroundedAnswer",
    "SourcePassage",
    "document_agent",
]
