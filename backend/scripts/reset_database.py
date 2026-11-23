"""Script to inspect and cleanly reset all application data in local SQLite database."""
import asyncio
import os
import shutil
import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import settings
from database import engine, Base, async_session_factory
from sqlalchemy import text, func, select
from models import (
    User, Project, Requirement, RequirementVersion,
    Document, DocumentChunk, ApprovalRequest, ApprovalAction,
    AuditLog, KnowledgeItem
)
from models.revoked_token import RevokedToken


async def inspect_counts():
    async with async_session_factory() as session:
        counts = {}
        models = [
            ("users", User),
            ("projects", Project),
            ("requirements", Requirement),
            ("requirement_versions", RequirementVersion),
            ("documents", Document),
            ("document_chunks", DocumentChunk),
            ("approval_requests", ApprovalRequest),
            ("approval_actions", ApprovalAction),
            ("audit_logs", AuditLog),
            ("revoked_tokens", RevokedToken),
        ]
        for name, model in models:
            res = await session.execute(select(func.count()).select_from(model))
            counts[name] = res.scalar()
        return counts


async def reset_database():
    # 1. Safety check
    db_url = settings.DATABASE_URL
    print(f"Target DATABASE_URL: {db_url}")
    if "aifre.db" not in db_url and not db_url.startswith("sqlite"):
        raise RuntimeError("Safety check failed: DATABASE_URL does not point to a local SQLite database!")

    print("\n--- Current Record Counts Before Reset ---")
    counts_before = await inspect_counts()
    for table, count in counts_before.items():
        print(f"  {table}: {count}")

    # 2. Delete rows in order of foreign key dependency
    async with engine.begin() as conn:
        print("\nDeleting application data in reverse dependency order...")
        # Disable foreign keys temporarily if needed or delete in order
        await conn.execute(text("DELETE FROM approval_actions;"))
        await conn.execute(text("DELETE FROM approval_requests;"))
        await conn.execute(text("DELETE FROM requirement_versions;"))
        await conn.execute(text("DELETE FROM requirements;"))
        await conn.execute(text("DELETE FROM document_chunks;"))
        await conn.execute(text("DELETE FROM documents;"))
        await conn.execute(text("DELETE FROM audit_logs;"))
        await conn.execute(text("DELETE FROM revoked_tokens;"))
        await conn.execute(text("DELETE FROM projects;"))
        await conn.execute(text("DELETE FROM users;"))
        print("SQL delete statements executed successfully.")

    # 3. Clean up SRS files on disk
    srs_dir = Path(settings.BASE_DIR) / "data" / "srs"
    if srs_dir.exists():
        print(f"\nCleaning generated SRS files in: {srs_dir}")
        for item in srs_dir.iterdir():
            if item.is_dir():
                shutil.rmtree(item, ignore_errors=True)
            elif item.is_file():
                item.unlink(missing_ok=True)
        print("SRS directory cleaned.")

    # 4. Clean up uploaded documents on disk if any
    uploads_dir = Path(settings.BASE_DIR) / "data" / "uploads"
    if uploads_dir.exists():
        print(f"\nCleaning uploaded files in: {uploads_dir}")
        for item in uploads_dir.iterdir():
            if item.is_dir():
                shutil.rmtree(item, ignore_errors=True)
            elif item.is_file():
                item.unlink(missing_ok=True)
        print("Uploads directory cleaned.")

    # 5. Verify counts after reset
    print("\n--- Record Counts After Reset ---")
    counts_after = await inspect_counts()
    for table, count in counts_after.items():
        print(f"  {table}: {count}")
        assert count == 0, f"Table {table} still has {count} records!"

    print("\n[SUCCESS] Local database reset completed cleanly. Schemas and structure preserved.")


if __name__ == "__main__":
    asyncio.run(reset_database())
