import aiosqlite

RECENT_ENTRY_EDIT_LIMIT = 10
DB_PATH = "wallettracker.db"

_conn: aiosqlite.Connection = None

async def get_conn() -> aiosqlite.Connection:
    return _conn

async def init_db():
    """ Create the databse tables if they don't exist yet.
    Called once only when the bot starts up.
    """
    print("Connecting to database...")
    global _conn
    _conn = await aiosqlite.connect(DB_PATH)
    print("Connected. Creating tables...")

    # Create a table named `entries` that stores all spending logs
    await _conn.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     TEXT NOT NULL,
            amount      REAL NOT NULL CHECK (amount > 0),
            category    TEXT NOT NULL CHECK (category IN ('Eat out & Takeaway', 'Entertainment', 'Grocery', 'Snack', 'Utils & Bills', 'Other')),
            note        TEXT,
            timestamp   TEXT DEFAULT (datetime('now'))
        )
    """) 

    # Create a table named `budgets` that stores user-customised budgets
    await _conn.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            user_id        TEXT NOT NULL,
            budget_amount  REAL NOT NULL CHECK (budget_amount > 0),
            budget_period  TEXT NOT NULL DEFAULT 'weekly' CHECK (budget_period IN ('daily', 'weekly', 'monthly')),
            PRIMARY KEY (user_id, budget_period)
        )
    """)

    # Create a `summary_channels` table so that the bot knows
    # which channel in the server it should send the summary message in
    # each user can have one summary channel per server
    await _conn.execute("""
        CREATE TABLE IF NOT EXISTS summary_channels (
            guild_id        TEXT NOT NULL,
            channel_id      TEXT NOT NULL,
            user_id         TEXT NOT NULL,
            budget_period   TEXT NOT NULL DEFAULT 'weekly' CHECK (budget_period IN ('daily', 'weekly', 'monthly')),
            opted_in        INTEGER NOT NULL DEFAULT 1,
            PRIMARY KEY (user_id,budget_period)
        )
    """)
    print("summary_channels table done.")

    await _conn.execute(""" 
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            timezone TEXT NOT NULL DEFAULT 'UTC'
        )
    """)
    print("users table done.")

    await _conn.commit()
    print("Committed.")

async def close_db():
    global _conn
    if _conn:
        await _conn.close()

async def add_entry(user_id: str,
                    amount: float,
                    category: str,
                    note: str = None,
                    conn: aiosqlite.Connection = None):
    """ Inserts a new spending entry into the database.

    Args:
        user_id (str): the Discord ID of the user logging the spend
        amount (float): how much was spent
        category (str): what it was spent on (e.g. "coffee")
        note (str, optional): optional extra description. Defaults to None.
    """
    if conn is None:
        conn = await get_conn()
    await conn.execute(
        """ 
        INSERT INTO entries (user_id, amount, category, note)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, amount, category, note)
        # ?-style is used to avoid SQL injection
    ) # "entries" is table name
    await conn.commit()

async def get_recent_entries_by_user(user_id: str,
                                    limit: int = RECENT_ENTRY_EDIT_LIMIT,
                                    conn: aiosqlite.Connection = None):
    """Fetches the most recent entries for a user in a server.

    Args:
        user_id (str): _description_
        limit (int, optional): how many entries to return. Defaults to 10.
    Return:
        list of entries, each is a tuple of (id, amount, category, note, timestamp)
    """
    if conn is None:
            conn = await get_conn()
    async with conn.execute(
        """ 
        SELECT id, amount, category, note, timestamp
        FROM entries
        WHERE user_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
        """,
        (user_id, limit)
    ) as cursor:
        return await cursor.fetchall()
        
async def edit_entry(entry_id: int,
                     user_id: str,
                     amount: float = None,
                     category: str = None,
                     note: str = None,
                     conn: aiosqlite.Connection = None) -> bool:
    """Edits an existing entry. Only updates fields that are provided.

    The user_id and guild_id checks ensure a user can only edit their own
    entries within their server and not someone else's.

    Args:
        entry_id (int):             the ID of the entry to edit.
        user_id (str):              must match the entry's owner.
        amount (float, optional):   new amount, or None to leave unchanged.
        category (str, optional):   new category, or None to leave unchanged.
        note (str, optional):       new note, or None to leave unchanged.
    
    Returns True if a row was updated, False if no matching entry was found.
    """
    # Build the SET clause dynamically based on which fields were provided
    # All three fields (amount, category, note) are optional, we can't hardcode 
    # SET amount = ?, category = ?, note = ? 
    # since the user might only want to change one of them
    # -> build them programmatically
    if conn is None:
        conn = await get_conn()
    fields = []
    values = []

    if amount is not None:
        fields.append("amount = ?")
        values.append(amount)
    if category is not None:
        fields.append("category = ?")
        values.append(category)
    if note is not None:
        fields.append("note = ?")
        values.append(note)

    if not fields:
        # Nothing to update
        return False
    
    # Add the WHERE clause values
    values.extend([entry_id, user_id])
    cursor = await conn.execute(
        f""" 
        UPDATE entries
        SET {', '.join(fields)}
        WHERE id = ? AND user_id = ?
        """,
        values
    )
    await conn.commit()
    # rowcount tells us how many rows were actually updated
    # if 0, the entry didn't exist or didn't belong to this user
    return cursor.rowcount > 0

# Need to get an entry for the confirmation step
# where we show the user what they're about to delete 
# before we actually remove it
async def get_entry_by_id(entry_id: int,
                          user_id: str,
                          conn: aiosqlite.Connection = None):
    """Fetches a single entry by ID, only if it belongs to this user in this server.
    Returns (id, amount, category, note, timestamp) or None if not found.

    Args:
        entry_id (int): _description_
        user_id (str): _description_
    """
    if conn is None:
        conn = await get_conn()
    async with conn.execute(
        """ 
        SELECT id, amount, category, note, timestamp
        FROM entries
        WHERE id = ? AND user_id = ?
        """,
        (entry_id, user_id)
    ) as cursor:
        return await cursor.fetchone()
        
async def delete_entry(entry_id: str,
                       user_id: str,
                        conn: aiosqlite.Connection = None) -> bool:
    """Deletes an entry by ID. Only deletes if it belongs to this user in this server.
    Return True if a row was deleted, False if no matching entry was found.

    Args:
        entry_id (str): _description_
        user_id (str): _description_
    """
    if conn is None:
        conn = await get_conn()
    cursor = await conn.execute(
        """ 
        DELETE FROM entries
        WHERE id = ? AND user_id = ?
        """,
        (entry_id, user_id)
    )
    await conn.commit()
    return cursor.rowcount > 0

async def set_budget(user_id: str,
                     amount: float,
                     period: str,
                    conn: aiosqlite.Connection = None):
    """ Saves a user's budget. Overwrites if one already exists for this user.
    Error raised for invalid amount or period.

    Args:
        user_id (str): the Discord ID of the user logging the spend
        amount (float): the budget amount (e.g. 100.00)
        period (str): how often the budget resets (e.g. 'weekly', 'monthly')
    """
    if conn is None:
        conn = await get_conn()
    try:
        await conn.execute(
            """
            INSERT INTO budgets (user_id, budget_amount, budget_period)
            VALUES (?, ?, ?)
            ON CONFLICT (user_id, budget_period) DO UPDATE SET
                budget_amount = excluded.budget_amount
            """,
            (user_id, amount, period)
        )   # 'ON CONFLICT ... DO UPDATE': upsert - try to insert a new row, 
            # but if a row with the same budget_period and user_id already exists 
            # (which is the primary key we defined), update it instead of throwing an error
    except Exception as e:
        raise Exception(f"Error setting budget: {e}")
    await conn.commit()

async def get_budget_for_period(user_id: str, 
                                budget_period: str,
                          conn: aiosqlite.Connection = None):
    """ Fetches the budget of a period for a user.
    Returns a row (budget_amount, budget_period) or None if no budget is set.

    Args:
        user_id (str): _description_
    """
    if conn is None:
        conn = await get_conn()
    try:
        async with conn.execute(
            """
            SELECT budget_amount, budget_period
            FROM budgets
            WHERE user_id = ? AND budget_period = ?
            """,
            (user_id, budget_period)
        ) as cursor:
            return await cursor.fetchone()
    except Exception as e:
        raise Exception(f"Error getting budget for period: {e}")

async def set_summary_channel_for_budget(guild_id: str, 
                                        channel_id: str,
                                        user_id: str,
                                        budget_period: str,
                                        opted_in: bool = True,
                          conn: aiosqlite.Connection = None):
    """ Saves the channel where automatic summary for a budget should be posted.
    Each (user, period) can only have 1 summary channel across all servers,
    setting new channel means overwriting old channel.

    Args:
        guild_id (str): _description_
        channel_id (str): _description_
    """
    if conn is None:
        conn = await get_conn()    
    try:
        assert await get_budget_for_period(conn, user_id, budget_period)
    except Exception as e:
        raise Exception(f"Cannot set channel for a non-existent budget: {e}")

    try:
        await conn.execute(
            """ 
            INSERT INTO summary_channels (guild_id, channel_id, user_id, budget_period, opted_in)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT (user_id, budget_period) DO UPDATE SET
                guild_id = excluded.guild_id,
                channel_id = excluded.channel_id
            """,
            (guild_id, channel_id, user_id, budget_period, 1 if opted_in else 0)
        )
        await conn.commit()
    except Exception as e:
        raise Exception(f"Error setting summary channel: {e}")

async def get_summary_channel(user_id: str,
                              budget_period: str,
                          conn: aiosqlite.Connection = None):
    """ Fetches the summary channel ID for a server.
    Returns (guild_id, channel_id), or (None, None) of not set.

    Args:
        user_id (str): _description_
        budget_period (str): _description_
    """
    if conn is None:
        conn = await get_conn()
    async with conn.execute(
        """ 
        SELECT guild_id, channel_id FROM summary_channels
        WHERE user_id = ? AND budget_period = ?
        """,
        (user_id, budget_period)
    ) as cursor:
        row = await cursor.fetchone()
        return row if row else (None, None)

async def get_entries_for_user_since(user_id: str,
                                    since: str,
                          conn: aiosqlite.Connection = None):
    """ Fetches all spending entries for a user since a given timestamp.

    Args:
        user_id (str): _description_
        since (str): an ISO timestamp string e.g. '2024-01-01 00:00:00'
                    only entries after this point are returned.
    Returns a list of rows, each row being (amount, category, note, timestamp).
    """
    if conn is None:
        conn = await get_conn()
    async with conn.execute(
        """
        SELECT amount, category, note, timestamp
        FROM entries
        WHERE user_id = ? AND timestamp >= ?
        ORDER BY timestamp DESC
        """,
        (user_id, since)
    ) as cursor:
        return await cursor.fetchall()

async def set_opted_out_for_period(user_id: str,
                                budget_period: str,
                          conn: aiosqlite.Connection = None) -> int:
    """ Delete summary channel info as opt out method.
    Return the number of rows affected, 0 if no deletion happened.
    """
    if conn is None:
        conn = await get_conn()
    async with conn.execute(
        """
        DELETE FROM summary_channels
        WHERE user_id = ? AND budget_period = ?
        """,
        (user_id, budget_period)
    ) as cursor:
        await conn.commit()
        return cursor.rowcount

async def get_opted_in_for_period(user_id: str, 
                                budget_period: str,
                          conn: aiosqlite.Connection = None) -> bool:
    """Check if user is opted in to a certain type of budget period.
    Returns True if the user is opted in to automatic summaries, False otherwise."""
    if conn is None:
        conn = await get_conn()
    async with conn.execute(
        """
        SELECT opted_in FROM summary_channels
        WHERE user_id = ? AND budget_period = ?
        """,
        (user_id, budget_period)
    ) as cursor:
        row = await cursor.fetchone()
        # If no row exists at all, treat as opted out
        return bool(row[0]) if row else False

async def get_all_opted_in_budgets(conn: aiosqlite.Connection = None):
    """Fetches every budget row across all users.
    Returns a list of (user_id, budget_amount, budget_period, guild_id, channel_id).
    """
    if conn is None:
        conn = await get_conn()
    async with conn.execute(
        """
        SELECT b.user_id AS user_id, budget_amount, 
                b.budget_period AS budget_period, 
                s.guild_id AS guild_id, 
                S.channel_id AS channel_id
        FROM budgets AS b 
        INNER JOIN summary_channels AS s
            ON  b.user_id = s.user_id
            AND b.budget_period = s.budget_period
        WHERE s.opted_in = 1
        """
    ) as cursor:
        return await cursor.fetchall()
        
async def set_user_timezone(user_id: str, 
                            tz: str,
                          conn: aiosqlite.Connection = None):
    """Saves a user's preferred timezone.
    
    Args:
        user_id: The Discord ID of the user.
        tz:      A valid timezone string e.g. 'Australia/Melbourne'.
    """
    if conn is None:
        conn = await get_conn()
    await conn.execute(
        """
        INSERT INTO users (user_id, timezone)
        VALUES (?, ?)
        ON CONFLICT (user_id) DO UPDATE SET
            timezone = excluded.timezone
        """,
        (user_id, tz)
    )
    await conn.commit()

async def get_user_timezone(user_id: str,
                          conn: aiosqlite.Connection = None) -> str:
    """Fetches a user's timezone. Return 'UTC' if not set.

    Args:
        user_id (str): _description_

    Returns:
        str: _description_
    """
    if conn is None:
        conn = await get_conn()
    async with conn.execute(
        """
        SELECT timezone
        FROM users
        WHERE user_id = ?
        """,
        (user_id,)
    ) as cursor:
        row = await cursor.fetchone()
        return row[0] if row else "UTC"