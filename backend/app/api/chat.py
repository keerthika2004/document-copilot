"""API router for chat thread management and stream completions."""

import re
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import UserSession, get_current_user
from app.chat.orchestrator import orchestrate_chat_stream
from app.database import chats
from app.database.connection import get_db

router = APIRouter()


class CreateThreadRequest(BaseModel):
    """Payload to create a new chat thread."""

    title: str | None = None


class UpdateThreadRequest(BaseModel):
    """Payload to update an existing chat thread's title."""

    title: str


class ChatMessagePayload(BaseModel):
    """Payload representing a single message in the chat history."""

    role: str
    content: str


class ChatStreamRequest(BaseModel):
    """Request payload for streaming completions."""

    threadId: str
    messages: list[ChatMessagePayload]


def summarize_query_for_title(query: str) -> str:
    """Extract a clean 4-7 word title summary from the user's initial question."""
    cleaned = query.strip()
    prefixes_to_strip = [
        r"^(can|could|would|please|will)\s+(you\s+)?(tell|show|explain|give|provide|summarize|list|find|describe)(\s+me)?\s+(what|how|why|where|when|about|the|some)?\s*",
        r"^(what|how|why|where|when|who)\s+(are|is|do|does|did|can|could|would|should)\s+(the|a|an)?\s*",
        r"^(tell|show|explain|give|provide|summarize|list|find|describe)(\s+me)?\s+(what|how|why|where|when|about|the|some)?\s*",
        r"^(i\s+want\s+to\s+know|i('m|\s+am)\s+looking\s+for|do\s+we\s+know)\s+(what|how|why|where|when|about|the)?\s*",
    ]
    for pattern in prefixes_to_strip:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE).strip()

    if not cleaned:
        cleaned = query.strip()

    cleaned = re.sub(r"[?!.,]+$", "", cleaned).strip()

    if cleaned:
        cleaned = cleaned[0].upper() + cleaned[1:]

    words = cleaned.split()
    if len(words) > 7:
        cleaned = " ".join(words[:7]) + "..."
    elif len(cleaned) > 55:
        cleaned = cleaned[:52] + "..."

    return cleaned or "Chat Conversation"


@router.get("/threads")
async def list_threads(
    db: AsyncSession = Depends(get_db),
    current_user: UserSession = Depends(get_current_user),
) -> list[dict]:
    """Retrieve all chat threads belonging to the authenticated user."""
    threads = await chats.get_threads(db, current_user.id)
    return [
        {
            "id": str(t.id),
            "title": t.title,
            "created_at": t.created_at.isoformat(),
            "updated_at": t.updated_at.isoformat(),
        }
        for t in threads
    ]


@router.post("/threads")
async def create_thread(
    payload: CreateThreadRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserSession = Depends(get_current_user),
) -> dict:
    """Create a new chat thread for the authenticated user."""
    thread = await chats.create_thread(db, current_user.id, payload.title)
    return {
        "id": str(thread.id),
        "title": thread.title,
        "created_at": thread.created_at.isoformat(),
        "updated_at": thread.updated_at.isoformat(),
    }


@router.patch("/threads/{thread_id}")
async def update_thread(
    thread_id: str,
    payload: UpdateThreadRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserSession = Depends(get_current_user),
) -> dict:
    """Update a user's chat thread title if owned."""
    thread = await chats.update_thread(db, current_user.id, thread_id, payload.title)
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found or access denied",
        )
    return {
        "id": str(thread.id),
        "title": thread.title,
        "created_at": thread.created_at.isoformat(),
        "updated_at": thread.updated_at.isoformat(),
    }


@router.delete("/threads/{thread_id}")
async def delete_thread(
    thread_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserSession = Depends(get_current_user),
) -> dict:
    """Delete a user's chat thread if owned."""
    success = await chats.delete_thread(db, current_user.id, thread_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found or access denied",
        )
    return {"status": "success"}


@router.get("/threads/{thread_id}/messages")
async def get_messages(
    thread_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserSession = Depends(get_current_user),
) -> list[dict]:
    """Retrieve the message history of a specific chat thread if owned."""
    messages = await chats.get_messages(db, current_user.id, thread_id)
    return [
        {
            "id": str(m.id),
            "role": m.role,
            "content": m.content,
            "created_at": m.created_at.isoformat(),
            "metadata_json": m.metadata_json,
        }
        for m in messages
    ]


@router.post("/chat/stream")
async def stream_chat(
    payload: ChatStreamRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserSession = Depends(get_current_user),
) -> StreamingResponse:
    """Stream response turns and persist inputs/outputs asynchronously."""
    # 1. Verify user owns the thread
    thread = await chats.get_thread(db, current_user.id, payload.threadId)
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat thread not found or access denied.",
        )

    # 2. Extract and save the user's new prompt
    if not payload.messages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message history cannot be empty.",
        )

    last_msg = payload.messages[-1]
    if last_msg.role != "user":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The last message in history must be from the user.",
        )

    # Save user message to database
    await chats.save_message(db, payload.threadId, role="user", content=last_msg.content)

    # 3. Retrieve all messages for the thread context
    db_messages = await chats.get_messages(db, current_user.id, payload.threadId)

    # If this is the first message (or title is still default "New Conversation"/"New Chat"), auto-summarize title
    if thread.title in ("New Conversation", "New Chat", None, "") or len(db_messages) <= 1:
        summary_title = summarize_query_for_title(last_msg.content)
        await chats.update_thread(db, current_user.id, payload.threadId, summary_title)

    # 4. Stream response via the turn orchestrator
    return StreamingResponse(
        orchestrate_chat_stream(
            db=db,
            thread_id=payload.threadId,
            user_prompt=last_msg.content,
            db_messages=db_messages,
        ),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Prevents Nginx proxies from buffering chunks
        },
    )

