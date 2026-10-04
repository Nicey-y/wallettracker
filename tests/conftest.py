import pytest
import aiosqlite
import pytest_asyncio
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import database

pytest_asyncio_mode = "auto"

# sqlite in-memory database
# data cease to exist when connection is close
DB_PATH = ":memory:"  

@pytest.fixture(scope="function")
async def db():
    """ Create the databse tables if they don't exist yet.
    Called once only when the bot starts up.
    """
    print("Connecting to database...")
    conn = await aiosqlite.connect(DB_PATH)
    print("Connected. Creating tables...")

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     TEXT NOT NULL,
            amount      REAL NOT NULL CHECK (amount > 0),
            category    TEXT NOT NULL CHECK (category IN ('Eat out & Takeaway', 'Entertainment', 'Grocery', 'Snack', 'Utils & Bills', 'Other')),
            note        TEXT,
            timestamp   TEXT DEFAULT (datetime('now'))
        )
    """) 

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            user_id        TEXT NOT NULL,
            budget_amount  REAL NOT NULL CHECK (budget_amount > 0),
            budget_period  TEXT NOT NULL DEFAULT 'weekly' CHECK (budget_period IN ('daily', 'weekly', 'monthly')),
            PRIMARY KEY (budget_period, user_id)
        )
    """)

    # Each user can have only one summary channel across all servers
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS summary_channels (
            guild_id        TEXT NOT NULL,
            channel_id      TEXT NOT NULL,
            user_id         TEXT NOT NULL,
            budget_period  TEXT NOT NULL DEFAULT 'weekly' CHECK (budget_period IN ('daily', 'weekly', 'monthly')),
            opted_in        INTEGER NOT NULL DEFAULT 1,
            PRIMARY KEY (budget_period, user_id)
        )
    """)
    print("summary_channels table done.")

    await conn.execute(""" 
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            timezone TEXT NOT NULL DEFAULT 'UTC'
        )
    """)
    print("users table done.")

    await conn.commit()
    print("Committed.")

    yield conn

    await conn.close()

@pytest.fixture
async def seed_15_entries_same_user(db):
    categories = ['Eat out & Takeaway', 'Entertainment', 'Grocery', 'Snack', 'Utils & Bills', 'Other']
    for i in range(1, 17):
        await database.add_entry(db, 'user1', float(i), categories[i%6], None)    