import aiosqlite

RECENT_ENTRY_EDIT_LIMIT = 10
HARD_ENTRY_EDIT_LIMIT = 25

DB_PATH = "wallettracker.db"

async def init_db():
    """ Create the databse tables if they don't exist yet.
    Called once only when the bot starts up.
    """
    print("Connecting to database...")
    async with aiosqlite.connect(DB_PATH) as db:
        print("Connected. Creating tables...")

        # Create a table named `entries` that stores all spending logs
        await db.execute("""
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     TEXT NOT NULL,
                guild_id    TEXT NOT NULL,
                amount      REAL NOT NULL,
                category    TEXT,
                note        TEXT,
                timestamp   TEXT DEFAULT (datetime('now'))
            )
        """) 

        # Create a table named `budgets` that stores user-customised budgets
        await db.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                guild_id       TEXT NOT NULL,
                user_id        TEXT NOT NULL,
                budget_amount  REAL NOT NULL,
                budget_period  TEXT NOT NULL DEFAULT 'weekly',
                opted_in       INTEGER NOT NULL DEFAULT 1,
                PRIMARY KEY (guild_id, user_id)
            )
        """)

        # Create a `summary_channels` table so that the bot knows
        # which channel in the server it should send the summary message in
        await db.execute("""
            CREATE TABLE IF NOT EXISTS summary_channels (
                guild_id    TEXT PRIMARY KEY,
                channel_id  TEXT NOT NULL
            )
        """)
        print("summary_channels table done.")

        # Create a `user_timezones` table to store a user' timezone
        await db.execute(""" 
            CREATE TABLE IF NOT EXISTS user_timezones (
                user_id TEXT PRIMARY KEY,
                timezone TEXT NOT NULL DEFAULT 'UTC'
            )
        """)
        print("user_timezones table done.")

        await db.commit()
        print("Committed.")

async def add_entry(user_id: str,
                    guild_id: str,
                    amount: float,
                    category: str,
                    note: str = None):
    """ Inserts a new spending entry into the database.

    Args:
        user_id (str): the Discord ID of the user logging the spend
        guild_id (str): the Discord ID of the server it was logged in.
        amount (float): how much was spent
        category (str): what it was spent on (e.g. "coffee")
        note (str, optional): optional extra description. Defaults to None.
    """

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """ 
            INSERT INTO entries (user_id, guild_id, amount, category, note)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, guild_id, amount, category, note)
            # ?-style is used to avoid SQL injection
        ) # "entries" is table name
        await db.commit()

async def get_recent_entries(user_id: str,
                             guild_id: str,
                             limit: int = RECENT_ENTRY_EDIT_LIMIT):
    """Fetches the most recent entries for a user in a server.

    Args:
        user_id (str): _description_
        guild_id (str): _description_
        limit (int, optional): how many entries to return. Defaults to 10.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """ 
            SELECT id, amount, category, note, timestamp
            FROM entries
            WHERE user_id = ? AND guild_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (user_id, guild_id, limit)
        ) as cursor:
            return await cursor.fetchall()
        
async def edit_entry(entry_id: int,
                     user_id: str,
                     guild_id: str,
                     amount: float = None,
                     category: str = None,
                     note: str = None):
    """Edits an existing entry. Only updates fields that are provided.

    The user_id and guild_id checks ensure a user can only edit their own
    entries within their server — not someone else's.

    Args:
        entry_id (int):             the ID of the entry to edit.
        user_id (str):              must match the entry's owner.
        guild_id (str):             must match the entry's server.
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
    values.extend([entry_id, user_id, guild_id])

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            f""" 
            UPDATE entries
            SET {', '.join(fields)}
            WHERE id = ? AND user_id = ? AND guild_id = ?
            """,
            values
        )
        await db.commit()
        # rowcount tells us how many rows were actually updated
        # if 0, the entry didn't exist or didn't belong to this user
        return cursor.rowcount > 0

# Need to get an entry for the confirmation step
# where we show the user what they're about to delete 
# before we actually remove it    
async def get_entry_by_id(entry_id: int,
                          user_id: str,
                          guild_id: str):
    """Fetches a single entry by ID, only if it belongs to this user in this server.
    Returns (id, amount, category, note, timestamp) or None if not found.

    Args:
        entry_id (int): _description_
        user_id (str): _description_
        guild_id (str): _description_
    """

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """ 
            SELECT id, amount, category, note, timestamp
            FROM entries
            WHERE id = ? AND user_id = ? AND guild_id = ?
            """,
            (entry_id, user_id, guild_id)
        ) as cursor:
            return await cursor.fetchone()
        
async def delete_entry(entry_id: str,
                       user_id: str,
                       guild_id: str):
    """Deletes an entry by ID. Only deletes if it belongs to this user in this server.
    Return True if a row was deleted, False if no matching entry was found.

    Args:
        entry_id (str): _description_
        user_id (str): _description_
        guild_id (str): _description_
    """
    
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """ 
            DELETE FROM entries
            WHERE id = ? AND user_id = ? AND guild_id = ?
            """,
            (entry_id, user_id, guild_id)
        )
        await db.commit()
        return cursor.rowcount > 0

async def set_budget(user_id: str,
                     guild_id: str,
                     amount: float,
                     period: str):
    """ Saves a user's budget. Overwrites if one already exists for this user in this server.

    Args:
        user_id (str): the Discord ID of the user logging the spend
        guild_id (str): the Discord ID of the server it was logged in.
        amount (float): the budget amount (e.g. 100.00)
        period (str): how often the budget resets (e.g. 'weekly', 'monthly')
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO budgets (user_id, guild_id, budget_amount, budget_period)
            VALUES (?, ?, ?, ?)
            ON CONFLICT (guild_id, user_id) DO UPDATE SET
                budget_amount = excluded.budget_amount,
                budget_period = excluded.budget_period
            """,
            (user_id, guild_id, amount, period)
        )   # 'ON CONFLICT ... DO UPDATE': upsert -  try to insert a new row, 
            # but if a row with the same guild_id and user_id already exists 
            # (which is the primary key we defined), update it instead of throwing an error
        await db.commit()

async def set_opted_in(user_id: str, guild_id: str, opted_in: bool):
    """Sets the opted_in flag for a user's budget.
    
    Args:
        opted_in: True to opt in, False to opt out.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            UPDATE budgets
            SET opted_in = ?
            WHERE user_id = ? AND guild_id = ?
            """,
            (1 if opted_in else 0, user_id, guild_id)
        )
        await db.commit()


async def get_opted_in(user_id: str, guild_id: str) -> bool:
    """Returns True if the user is opted in to automatic summaries, False otherwise."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """
            SELECT opted_in FROM budgets
            WHERE user_id = ? AND guild_id = ?
            """,
            (user_id, guild_id)
        ) as cursor:
            row = await cursor.fetchone()
            # If no budget row exists at all, treat as opted out
            return bool(row[0]) if row else False

async def get_budget(user_id: str, guild_id: str):
    """ Fetches the budget for a user in a server.
    Returns a row (budget_amount, budget_period) or None if no budget is set.

    Args:
        user_id (str): _description_
        guild_id (str): _description_
    """

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """
            SELECT budget_amount, budget_period
            FROM budgets
            WHERE user_id = ? AND guild_id = ?
            """,
            (user_id, guild_id)
        ) as cursor:
            return await cursor.fetchone()
            # fetchone() returns a single row as a tuple e.g. (500.0, 'monthly')
            # or None if no row was found

async def get_entries(user_id: str,
                      guild_id: str,
                      since: str):
    """ Fetches all spending entries for a user since a given timestamp.

    Args:
        user_id (str): _description_
        guild_id (str): _description_
        since (str): an ISO timestamp string e.g. '2024-01-01 00:00:00'
                    only entries after this point are returned.
    Returns a list of rows, each row being (amount, category, note, timestamp).
    """

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """
            SELECT amount, category, note, timestamp
            FROM entries
            WHERE user_id = ? AND guild_id = ? AND timestamp >= ?
            ORDER BY timestamp DESC
            """,
            (user_id, guild_id, since)
        ) as cursor:
            return await cursor.fetchall()
            # fetchall() returns a list of tuples, e.g.
            # [(12.50, 'coffee', None, '2024-01-03 09:00:00'),
            #  (8.00, 'transport', 'bus', '2024-01-02 08:30:00')]

async def get_all_budgets():
    """Fetches every budget row across all users and servers.
    Returns a list of (user_id, guild_id, budget_amount, budget_period, opted_in).
    """
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """
            SELECT user_id, guild_id, budget_amount, budget_period, opted_in
            FROM budgets
            """
        ) as cursor:
            return await cursor.fetchall()
        
async def set_summary_channel(guild_id: str, channel_id: str):
    """ Saves the channel where automatic summaries should be posted for a server.

    Args:
        guild_id (str): _description_
        channel_id (str): _description_
    """

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """ 
            INSERT INTO summary_channels (guild_id, channel_id)
            VALUES (?, ?)
            ON CONFLICT (guild_id) DO UPDATE SET
                channel_id = excluded.channel_id
            """,
            (guild_id, channel_id)
        )
        await db.commit()

async def get_summary_channel(guild_id: str):
    """ Fetches the summary channel ID for a server.
    Returns the channel_id string, or None of not set.

    Args:
        guild_id (str): _description_
    """
    # print("--- from get_summary_channel")
    # print(guild_id)
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """ 
            SELECT channel_id FROM summary_channels
            WHERE guild_id = ?
            """,
            (guild_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None
        
async def set_user_timezone(user_id: str, tz: str):
    """Saves a user's preferred timezone.
    
    Args:
        user_id: The Discord ID of the user.
        tz:      A valid timezone string e.g. 'Australia/Melbourne'.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO user_timezones (user_id, timezone)
            VALUES (?, ?)
            ON CONFLICT (user_id) DO UPDATE SET
                timezone = excluded.timezone
            """,
            (user_id, tz)
        )
        await db.commit()

async def get_user_timezone(user_id: str) -> str:
    """Fetches a user's timezone. Return 'UTC' if not set.

    Args:
        user_id (str): _description_

    Returns:
        str: _description_
    """

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """
            SELECT timezone
            FROM user_timezones
            WHERE user_id = ?
            """,
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else "UTC"