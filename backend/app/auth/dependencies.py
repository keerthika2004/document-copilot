from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.supabase import create_user_client
from app.database.connection import get_db
from app.database.models.user import User

logger = structlog.get_logger()

# Security scheme to extract "Authorization: Bearer <token>" from request headers
security_scheme = HTTPBearer(
    scheme_name="SupabaseAuth",
    description="Bearer token issued by Supabase Auth",
    auto_error=True,
)


class UserSession(BaseModel):
    """Pydantic model representing the authenticated user's session details."""

    id: str
    email: str


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> UserSession:
    """FastAPI dependency to extract and verify the Supabase JWT bearer token.

    Verifies the token by requesting user details from the Supabase Auth service.
    Ensures the user profile is synced to the public database schema.
    Returns a UserSession object or raises HTTP 401 Unauthorized.
    """
    token = credentials.credentials
    try:
        # Create a user-scoped client using the JWT
        client = await create_user_client(token)

        # Retrieve the user object from Supabase Auth by passing the JWT token explicitly.
        # This serves as a secure server-side validation of the JWT token.
        response = await client.auth.get_user(token)
        if not response or not getattr(response, "user", None):
            logger.warn("auth_failed", reason="No user returned from Supabase Auth")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
            )
        user = response.user

        if not user.email:
            logger.warn("auth_failed", reason="No email returned from Supabase Auth")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
            )

        # Self-healing sync: Ensure the user exists in our local PostgreSQL 'users' table
        user_uuid = UUID(user.id)
        stmt = select(User).where(User.id == user_uuid)
        result = await db.execute(stmt)
        local_user = result.scalar_one_or_none()

        if not local_user:
            logger.info("syncing_missing_user", user_id=user.id, email=user.email)
            local_user = User(id=user_uuid, email=user.email)
            db.add(local_user)
            await db.commit()

        return UserSession(id=user.id, email=user.email)

    except HTTPException:
        raise
    except Exception as e:
        logger.warn("auth_verification_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
