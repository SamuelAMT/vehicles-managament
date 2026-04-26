from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.user import TokenResponse


async def authenticate(db: AsyncSession, username: str, password: str) -> TokenResponse | None:
    result = await db.execute(select(User).where(User.username == username, User.ativo == True))  # noqa: E712
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.password_hash):
        return None
    token = create_access_token({"sub": user.username, "role": user.role})
    return TokenResponse(access_token=token)


async def create_user(db: AsyncSession, username: str, password: str, role: str) -> User:
    user = User(username=username, password_hash=hash_password(password), role=role)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
