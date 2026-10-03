import pytest
import aiosqlite
import pytest_asyncio
import database

pytest_asyncio_mode = "auto"

# sqlite in-memory database
# data cease to exist when connection is close
DB_PATH = ":memory:"  

async def db():
    """ Create the databse tables if they don't exist yet.
    Called once only when the bot starts up.
    """
    print("Connecting to database...")
    db = aiosqlite.connect(DB_PATH)
    print("Connected. Creating tables...")

    await db.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     TEXT NOT NULL,
            amount      REAL NOT NULL,
            category    TEXT,
            note        TEXT,
            timestamp   TEXT DEFAULT (datetime('now'))
        )
    """) 

    await db.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            user_id        TEXT NOT NULL,
            budget_amount  REAL NOT NULL,
            budget_period  TEXT NOT NULL DEFAULT 'weekly',
            PRIMARY KEY (budget_period, user_id)
        )
    """)

    # Each user can have only one summary channel across all servers
    await db.execute("""
        CREATE TABLE IF NOT EXISTS summary_channels (
            guild_id        TEXT PRIMARY KEY,
            channel_id      TEXT NOT NULL,
            user_id         TEXT NOT NULL,
            budget_period   TEXT NOT NULL DEFAULT 'weekly',
            opted_in        INTEGER NOT NULL DEFAULT 1,
        )
    """)
    print("summary_channels table done.")

    await db.execute(""" 
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            timezone TEXT NOT NULL DEFAULT 'UTC'
        )
    """)
    print("users table done.")

    await db.commit()
    print("Committed.")

    yield db

    await db.close()

        