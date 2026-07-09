"""Unit tests for PydanticAI document assistant agent and structured outputs."""

from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from pydantic import ValidationError
from pydantic_ai.messages import ModelRequest, ModelResponse

from app.assistant import Citation, GroundedAnswer, SourcePassage, document_agent
from app.chat.orchestrator import build_message_history
from app.database.models.chat_message import ChatMessage


@pytest.fixture
def anyio_backend() -> str:
    """Specify asyncio backend for anyio tests."""
    return "asyncio"


def test_grounded_answer_schema() -> None:
    """Test serialization and validation of GroundedAnswer, Citation, and SourcePassage."""
    citation = Citation(
        ticker="AAPL",
        fiscal_year=2023,
        section_name="Risk Factors",
        chunk_id=str(uuid4()),
        exact_quote="We face significant competition.",
    )
    answer = GroundedAnswer(
        answer="Apple faces competition [1].",
        citations=[citation],
        has_sufficient_evidence=True,
        confidence_summary="High confidence based on FY23 10-K.",
    )

    assert answer.answer == "Apple faces competition [1]."
    assert len(answer.citations) == 1
    assert answer.citations[0].ticker == "AAPL"
    assert answer.has_sufficient_evidence is True

    # Test invalid schema (missing required fields)
    with pytest.raises(ValidationError):
        GroundedAnswer.model_validate({"answer": "Incomplete answer"})


def test_source_passage_schema() -> None:
    """Test validation of SourcePassage schema."""
    passage = SourcePassage(
        chunk_id=str(uuid4()),
        document_id=str(uuid4()),
        ticker="MSFT",
        fiscal_year=2024,
        filing_type="10-K",
        section_name="MD&A",
        chunk_index=5,
        text_content="Cloud revenue increased.",
        score=0.0321,
    )
    assert passage.ticker == "MSFT"
    assert passage.score == 0.0321


def test_agent_tools_registered() -> None:
    """Verify that all required retrieval tools are registered on the agent."""
    tool_names = set(document_agent._function_toolset.tools.keys())
    assert {"search_filings", "read_chunk_with_context", "list_available_filings"}.issubset(tool_names)


@pytest.mark.anyio
async def test_read_chunk_with_context_invalid_uuid() -> None:
    """Test that read_chunk_with_context tool returns error string on invalid UUID."""
    tool_func = document_agent._function_toolset.tools["read_chunk_with_context"].function
    mock_ctx = MagicMock()

    result = await tool_func(mock_ctx, chunk_id="not-a-uuid", window=1)
    assert isinstance(result, str)
    assert "Invalid chunk_id format" in result


def test_build_message_history() -> None:
    """Test that build_message_history successfully converts DB messages."""
    thread_id = uuid4()
    msg_user = ChatMessage(
        id=uuid4(),
        thread_id=thread_id,
        role="user",
        content="What is Apple's revenue?",
    )
    msg_assistant = ChatMessage(
        id=uuid4(),
        thread_id=thread_id,
        role="assistant",
        content="Apple's revenue is 383B.",
    )
    msg_active_user = ChatMessage(
        id=uuid4(),
        thread_id=thread_id,
        role="user",
        content="What about Microsoft?",
    )

    db_messages = [msg_user, msg_assistant, msg_active_user]
    history = build_message_history(db_messages)

    # Excludes the active user prompt at the end
    assert len(history) == 2
    assert isinstance(history[0], ModelRequest)
    assert history[0].parts[0].content == "What is Apple's revenue?"
    assert isinstance(history[1], ModelResponse)
    assert history[1].parts[0].content == "Apple's revenue is 383B."

