"""Async SQLAlchemy engine, session, and declarative base."""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Shared declarative base for all models."""
    pass


async def get_db() -> AsyncSession:
    """FastAPI dependency — yields an async DB session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


from sqlalchemy import text

async def init_db():
    """Create all tables and apply non-destructive schema migrations."""
    import models.user
    import models.project
    import models.requirement
    import models.approval
    import models.audit
    import models.document
    import models.revoked_token

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Non-destructive migration for newly added columns
        try:
            await conn.execute(text("ALTER TABLE projects ADD COLUMN current_stage VARCHAR(50) DEFAULT 'interview'"))
        except Exception:
            pass  # Column already exists
