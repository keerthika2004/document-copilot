"""Turn Orchestrator for coordinating PydanticAI agent runs and database persistence."""

import logging
from collections.abc import AsyncGenerator
from uuid import UUID

from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, TextPart, UserPromptPart
from sqlalchemy.ext.asyncio import AsyncSession

from app.assistant import document_agent, DocumentAgentDeps
from app.chat.streaming import format_data, format_error, format_text_delta
from app.database import chats
from app.database.models.chat_message import ChatMessage
from app.retrieval import HybridRetriever

logger = logging.getLogger(__name__)


def build_message_history(db_messages: list[ChatMessage]) -> list[ModelMessage]:
    """Convert DB chat messages into PydanticAI compatible model messages.

    Excludes the final user message since that represents the active prompt.
    """
    history: list[ModelMessage] = []
    # We only build history from completed rounds (excluding the active user prompt at the end)
    for msg in db_messages[:-1]:
        if msg.role == "user":
            history.append(ModelRequest(parts=[UserPromptPart(content=msg.content)]))
        elif msg.role == "assistant":
            history.append(ModelResponse(parts=[TextPart(content=msg.content)]))
    return history


async def orchestrate_chat_stream(
    db: AsyncSession,
    thread_id: str,
    user_prompt: str,
    db_messages: list[ChatMessage],
) -> AsyncGenerator[str, None]:
    """Orchestrate agent run, yield text deltas, and persist final response and citations."""
    # 1. Initialize retriever and dependencies
    retriever = HybridRetriever()
    deps = DocumentAgentDeps(
        db=db,
        retriever=retriever,
        user_id=None,
        thread_id=thread_id,
    )

    # 2. Build message history context
    history = build_message_history(db_messages)

    # 3. Execute agent streaming
    last_len = 0
    final_answer = ""
    citations_to_save = []
    confidence_summary = ""
    has_sufficient_evidence = True

    try:
        async with document_agent.run_stream(
            user_prompt,
            deps=deps,
            message_history=history,
        ) as result:
            # Stream structured output deltas as they are partially validated
            async for model in result.stream_output(debounce_by=0.05):
                if model and hasattr(model, "answer") and model.answer:
                    # Extract and yield text delta
                    delta = model.answer[last_len:]
                    if delta:
                        yield format_text_delta(delta)
                        last_len = len(model.answer)
                        final_answer = model.answer

                # Continuously capture the latest state of citations and metadata
                if model and hasattr(model, "citations") and model.citations:
                    citations_to_save = model.citations
                if model and hasattr(model, "confidence_summary") and model.confidence_summary:
                    confidence_summary = model.confidence_summary
                if model and hasattr(model, "has_sufficient_evidence") and model.has_sufficient_evidence is not None:
                    has_sufficient_evidence = model.has_sufficient_evidence

            # After streaming completes, extract the final validated structured output
            try:
                output = await result.get_output()
                if output:
                    if hasattr(output, "citations") and output.citations:
                        citations_to_save = output.citations
                    if hasattr(output, "confidence_summary") and output.confidence_summary:
                        confidence_summary = output.confidence_summary
                    if hasattr(output, "has_sufficient_evidence") and output.has_sufficient_evidence is not None:
                        has_sufficient_evidence = output.has_sufficient_evidence
                    if hasattr(output, "answer") and output.answer:
                        final_answer = output.answer
            except Exception as e:
                logger.warning("Could not extract final output via get_output: %s", e)

        # Validate citations and grounding against existing database chunks
        existing_chunk_ids = None
        if citations_to_save:
            from sqlalchemy import select
            from app.database.models.document_chunk import DocumentChunk
            candidate_uuids = []
            for citation in citations_to_save:
                try:
                    candidate_uuids.append(UUID(getattr(citation, "chunk_id", "") or ""))
                except (ValueError, TypeError):
                    pass
            if candidate_uuids:
                stmt = select(DocumentChunk.id).where(DocumentChunk.id.in_(candidate_uuids))
                result = await db.execute(stmt)
                existing_chunk_ids = set(result.scalars().all())

        from app.grounding.validator import validate_grounded_answer
        citations_to_save, has_sufficient_evidence, confidence_summary = validate_grounded_answer(
            answer_text=final_answer or "",
            citations=citations_to_save,
            has_sufficient_evidence=has_sufficient_evidence,
            confidence_summary=confidence_summary,
            valid_chunk_ids=existing_chunk_ids,
        )

        # 4. Persist completed assistant message (include citation metadata for frontend)
        citations_metadata = []
        for citation in citations_to_save:
            citations_metadata.append({
                "ticker": getattr(citation, "ticker", None),
                "fiscal_year": getattr(citation, "fiscal_year", None),
                "section_name": getattr(citation, "section_name", None),
                "filing_type": "10-K",
                "chunk_id": getattr(citation, "chunk_id", None),
                "exact_quote": getattr(citation, "exact_quote", None),
            })

        metadata_json = {
            "confidence_summary": confidence_summary,
            "has_sufficient_evidence": has_sufficient_evidence,
            "citations": citations_metadata,
        }
        assistant_msg = await chats.save_message(
            db=db,
            thread_id=thread_id,
            role="assistant",
            content=final_answer or "No response generated.",
            metadata_json=metadata_json,
        )
        yield format_data(metadata_json)

        # 5. Persist citations to message_citations table
        if citations_to_save and existing_chunk_ids:
            from app.database.models.message_citation import MessageCitation

            for citation in citations_to_save:
                try:
                    chunk_uuid = UUID(getattr(citation, "chunk_id", "") or "")
                    if chunk_uuid in existing_chunk_ids:
                        citation_row = MessageCitation(
                            message_id=assistant_msg.id,
                            chunk_id=chunk_uuid,
                        )
                        db.add(citation_row)
                except (ValueError, TypeError):
                    pass

            await db.commit()

    except Exception as e:
        logger.error("Error in orchestrate_chat_stream: %s", str(e), exc_info=True)
        yield format_error(f"Stream error: {str(e)}")
