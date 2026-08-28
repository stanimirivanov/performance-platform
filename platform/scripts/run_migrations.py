import asyncio
import os
import sys
from pathlib import Path

import asyncpg

MIGRATIONS_DIR = Path(__file__).parent.parent / "db" / "migrations"


async def run_migrations(reset: bool = False):
    dsn = os.environ.get(
        "DATABASE_URL", "postgresql://test_user:test_password@localhost:5432/metadata"
    )
    conn = await asyncpg.connect(dsn)

    if reset:
        await conn.execute("DROP SCHEMA IF EXISTS metadata CASCADE;")
        await conn.execute("DROP SCHEMA IF EXISTS audit CASCADE;")
        await conn.execute('DROP EXTENSION IF EXISTS "uuid-ossp";')
        print("Database reset.")

    # Create migrations table if not exists
    await conn.execute("""
        CREATE SCHEMA IF NOT EXISTS metadata;
        CREATE TABLE IF NOT EXISTS metadata.migrations (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
    """)

    # Get already applied migrations
    applied = {row[0] for row in await conn.fetch("SELECT name FROM metadata.migrations")}

    for file in sorted(MIGRATIONS_DIR.glob("*.sql")):
        if file.name in applied:
            print(f"Skipping {file.name} (already applied)")
            continue
        print(f"Applying {file.name}...")
        with open(file) as f:
            await conn.execute(f.read())
        await conn.execute("INSERT INTO metadata.migrations (name) VALUES ($1)", file.name)

    await conn.close()
    print("Migrations complete.")


if __name__ == "__main__":
    reset = "--reset" in sys.argv
    asyncio.run(run_migrations(reset))
