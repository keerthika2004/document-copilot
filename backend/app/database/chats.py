"""Database persistence CRUD layer for chat threads and messages."""

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.chat_message import ChatMessage
from app.database.models.chat_thread import ChatThread


async def get_threads(db: AsyncSession, user_id: str) -> list[ChatThread]:
    """Retrieve all chat threads owned by the user, ordered by updated_at desc."""
    user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
    stmt = (
        select(ChatThread)
        .where(ChatThread.user_id == user_uuid)
        .order_by(ChatThread.updated_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_thread(db: AsyncSession, user_id: str, thread_id: str) -> ChatThread | None:
    """Retrieve a single chat thread owned by the user."""
    user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
    thread_uuid = UUID(thread_id) if isinstance(thread_id, str) else thread_id
    stmt = select(ChatThread).where(
        ChatThread.id == thread_uuid, ChatThread.user_id == user_uuid
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_thread(
    db: AsyncSession, user_id: str, title: str | None = None
) -> ChatThread:
    """Create a new chat thread for the user."""
    user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
    thread = ChatThread(
        user_id=user_uuid,
        title=title or "New Chat",
    )
    db.add(thread)
    await db.commit()
    return thread


async def update_thread(
    db: AsyncSession, user_id: str, thread_id: str, title: str
) -> ChatThread | None:
    """Update the title of a chat thread if owned by the user."""
    user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
    thread_uuid = UUID(thread_id) if isinstance(thread_id, str) else thread_id

    thread = await get_thread(db, user_uuid, thread_uuid)
    if not thread:
        return None

    thread.title = title[:255]  # Ensure title fits within String(255) schema
    await db.commit()
    await db.refresh(thread)
    return thread



async def delete_thread(db: AsyncSession, user_id: str, thread_id: str) -> bool:
    """Delete a user's chat thread if they own it. Returns True if deleted."""
    user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
    thread_uuid = UUID(thread_id) if isinstance(thread_id, str) else thread_id

    # Verify ownership before deleting
    thread = await get_thread(db, user_uuid, thread_uuid)
    if not thread:
        return False

    stmt = delete(ChatThread).where(ChatThread.id == thread_uuid)
    await db.execute(stmt)
    await db.commit()
    return True


async def get_messages(
    db: AsyncSession, user_id: str, thread_id: str
) -> list[ChatMessage]:
    """Retrieve all messages in a chat thread after verifying user ownership."""
    user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
    thread_uuid = UUID(thread_id) if isinstance(thread_id, str) else thread_id

    # Verify thread ownership
    thread = await get_thread(db, user_uuid, thread_uuid)
    if not thread:
        return []

    stmt = (
        select(ChatMessage)
        .where(ChatMessage.thread_id == thread_uuid)
        .order_by(ChatMessage.created_at.asc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def save_message(
    db: AsyncSession,
    thread_id: str,
    role: str,
    content: str,
    metadata_json: dict | None = None,
) -> ChatMessage:
    """Append a new message to a chat thread."""
    thread_uuid = UUID(thread_id) if isinstance(thread_id, str) else thread_id
    message = ChatMessage(
        thread_id=thread_uuid,
        role=role,
        content=content,
        metadata_json=metadata_json,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message
