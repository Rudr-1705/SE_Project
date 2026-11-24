"""Script to inspect and cleanly reset all application data in local SQLite database."""
import os
import shutil
import sqlite3
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from config import settings


def reset_database():
    # 1. Locate database
    db_path = backend_dir / "data" / "aifre.db"
    print(f"Target Database File: {db_path}")
    if not db_path.exists():
        print("Database file does not exist yet. Nothing to reset.")
        return

    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    # Discover all user tables
    tables = [
        row[0]
        for row in cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
    ]

    print("\n--- Current Record Counts Before Reset ---")
    counts_before = {}
    for table in tables:
        count = cur.execute(f'SELECT count(*) FROM "{table}"').fetchone()[0]
        counts_before[table] = count
        print(f"  {table}: {count}")

    # 2. Delete rows from all application tables with foreign keys disabled
    print("\nDeleting application data from all tables...")
    cur.execute("PRAGMA foreign_keys = OFF;")
    for table in tables:
        cur.execute(f'DELETE FROM "{table}";')
    con.commit()
    cur.execute("PRAGMA foreign_keys = ON;")
    cur.execute("VACUUM;")
    con.commit()
    print("All application data deleted and database vacuumed.")

    # 3. Clean up SRS files on disk
    srs_dir = backend_dir / "data" / "srs"
    if srs_dir.exists():
        print(f"\nCleaning generated SRS files in: {srs_dir}")
        for item in srs_dir.iterdir():
            if item.is_dir():
                shutil.rmtree(item, ignore_errors=True)
            elif item.is_file():
                item.unlink(missing_ok=True)
        print("SRS directory cleaned.")

    # 4. Clean up uploaded documents on disk if any
    uploads_dir = backend_dir / "data" / "uploads"
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
    for table in tables:
        count = cur.execute(f'SELECT count(*) FROM "{table}"').fetchone()[0]
        print(f"  {table}: {count}")
        assert count == 0, f"Table {table} still has {count} records!"

    con.close()
    print("\n[SUCCESS] Local database reset completed cleanly. Schemas and structure preserved.")


if __name__ == "__main__":
    reset_database()
