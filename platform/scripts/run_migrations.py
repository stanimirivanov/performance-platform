import asyncio
from pathlib import Path

import asyncpg


async def run_migrations():
    dsn = "postgresql://test_user:test_password@localhost:5432/metadata"
    conn = await asyncpg.connect(dsn)
    migrations_dir = Path(__file__).parent.parent / "db" / "migrations"
    for file in sorted(migrations_dir.glob("*.sql")):
        print(f"Applying {file.name}...")
        with open(file) as f:
            await conn.execute(f.read())
    await conn.close()
    print("Migrations complete.")


if __name__ == "__main__":
    asyncio.run(run_migrations())
