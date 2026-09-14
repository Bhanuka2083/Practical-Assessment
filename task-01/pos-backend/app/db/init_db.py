import asyncio
import logging
from sqlalchemy import select

from app.core.database import engine, AsyncSessionLocal
from app.core.security import hash_password
from app.core.database import Base
from app.models.enums import UserRole
from app.models.user import User

# CRITICAL: Import all models so Base.metadata knows about them
import app.models.user  # noqa: F401
import app.models.product  # noqa: F401
import app.models.cart  # noqa: F401
import app.models.order  # noqa: F401
import app.models.payment  # noqa: F401

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("db_init")

async def init_database() -> None:
    logger.info("Initializing database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Tables created or verified.")

    logger.info("Checking for default admin account...")
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.role == "ADMIN")
        result = await session.execute(stmt)
        existing_admin = result.scalar_one_or_none()

        if not existing_admin:
            admin = User(
                email="admin@pos.com",
                hashed_password=hash_password("admin12345678"),
                role=UserRole.ADMIN,
            )
            session.add(admin)
            await session.commit()
            logger.info("Default admin seeded: admin@pos.com / admin12345678")
        else:
            logger.info("Admin account already exists. Skipping seed.")

if __name__ == "__main__":
    asyncio.run(init_database())