import aiosqlite
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database import add_entry, get_recent_entries_by_user

async def add_1_entry_return_id(conn: aiosqlite.Connection) -> int: 
    """Add one entry by 'user1' to the database and return the entry ID

    Args:
        conn (aiosqlite.Connection): _description_

    Returns:
        int: _description_
    """
    await add_entry('user1', 20.00, 'Grocery', conn)
    entry = await get_recent_entries_by_user('user1', 1, conn)
    return entry[0][0]