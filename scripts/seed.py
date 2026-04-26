import asyncio
import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import hash_password
from app.models.user import User

DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_async_engine(DATABASE_URL)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

SEED_USERS = [
    {"username": "admin", "password": os.environ["SEED_ADMIN_PASSWORD"], "role": "ADMIN"},
    {"username": "user", "password": os.environ["SEED_USER_PASSWORD"], "role": "USER"},
]


async def seed(db: AsyncSession) -> None:
    for u in SEED_USERS:
        user = User(username=u["username"], password_hash=hash_password(u["password"]), role=u["role"])
        db.add(user)
    await db.commit()
    print(f"Seeded {len(SEED_USERS)} users.")


async def main() -> None:
    async with SessionLocal() as db:
        await seed(db)
    await engine.dispose()


asyncio.run(main())
