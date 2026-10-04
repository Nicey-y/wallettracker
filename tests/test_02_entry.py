import aiosqlite
import pytest
import pytest_asyncio
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.validate import *
from database import add_entry, get_recent_entries_by_user, RECENT_ENTRY_EDIT_LIMIT, \
                    get_entry_by_id, edit_entry, \
                    delete_entry

pytest_asyncio_mode = "auto"
# pytest tests/test_02_entry.py -v

async def add_1_entry_return_id(conn: aiosqlite.Connection) -> int: 
    """Add one entry by 'user1' to the database and return the entry ID

    Args:
        conn (aiosqlite.Connection): _description_

    Returns:
        int: _description_
    """
    await add_entry('user1', 20.00, 'Grocery', conn=conn)
    entry = await get_recent_entries_by_user('user1', 1, conn=conn)
    return entry[0][0]
class TestAddEntry:
    # pytest tests/test_02_add_entry.py::TestAddEntry::test_add_single_entry -v
    async def test_add_single_entry(self, db):
        await add_entry(user_id='user1',
                        amount=20.0,
                        category='Grocery', conn=db)

        entries = await get_recent_entries_by_user('user1', conn=db)

        assert len(entries) == 1
        assert entries[0][1] == 20.0
        assert entries[0][2] == 'Grocery'
        assert entries[0][3] is None
        assert entries[0][4] is not None

    async def test_add_single_entry_with_note(self, db):
        await add_entry(user_id='user1',
                        amount=20.0,
                        category='Grocery',
                        note='test note', conn=db)

        entries = await get_recent_entries_by_user('user1', conn=db)

        assert len(entries) == 1
        assert entries[0][1] == 20.0
        assert entries[0][2] == 'Grocery'
        assert entries[0][3] == 'test note'
        assert entries[0][4] is not None

    async def test_add_multiple_entries_same_user(self, db):
        await add_entry(user_id='user1',
                        amount=20.0,
                        category='Grocery',
                        note='test 1', conn=db)
        await add_entry(user_id='user1',
                        amount=15.50,
                        category='Snack',
                        note='test 2', conn=db)
        await add_entry(user_id='user1',
                        amount=50.0,
                        category='Eat out & Takeaway', conn=db)

        entries = await get_recent_entries_by_user('user1', conn=db)

        assert len(entries) == 3

        assert entries[0][1] == 20.0
        assert entries[0][2] == 'Grocery'
        assert entries[0][3] == 'test 1'
        assert entries[0][4] is not None

        assert entries[1][1] == 15.50
        assert entries[1][2] == 'Snack'
        assert entries[1][3] == 'test 2'
        assert entries[1][4] is not None

        assert entries[2][1] == 50.0
        assert entries[2][2] == 'Eat out & Takeaway'
        assert entries[2][3] is None
        assert entries[2][4] is not None

    async def test_add_entries_diff_users(self, db):
        await add_entry(user_id='user1',
                        amount=20.0,
                        category='Grocery',
                        note='test 1', conn=db)
        await add_entry(user_id='user2',
                        amount=15.50,
                        category='Snack',
                        note='test 2', conn=db)

        # GET is scoped to user
        entries_1 = await get_recent_entries_by_user('user1', conn=db)
        assert len(entries_1) == 1
        assert entries_1[0][1] == 20.0
        assert entries_1[0][2] == 'Grocery'
        assert entries_1[0][3] == 'test 1'
        assert entries_1[0][4] is not None

        entries_2 = await get_recent_entries_by_user('user2', conn=db)
        assert entries_2[0][1] == 15.50
        assert entries_2[0][2] == 'Snack'
        assert entries_2[0][3] == 'test 2'
        assert entries_2[0][4] is not None

    async def test_get_entry_limit(self, db, seed_15_entries_same_user):
        entries_5 = await get_recent_entries_by_user('user1', limit=5, conn=db)
        assert len(entries_5) == 5

        entries_max = await get_recent_entries_by_user('user1', conn=db)
        assert len(entries_max) == RECENT_ENTRY_EDIT_LIMIT

    async def test_get_entry_empty(self, db):
        entries = await get_recent_entries_by_user('user1', conn=db)
        assert len(entries) == 0

class TestEditEntry:
    # pytest tests/test_02_entry.py::TestEditEntry::test_edit_single_field -v
    async def test_edit_single_field(self, db):
        entry_id = await add_1_entry_return_id(db)

        # edit amount
        assert await edit_entry(entry_id, 'user1', amount=50.00, conn=db)
        entry = await get_entry_by_id(entry_id, 'user1', conn=db)
        assert entry[1] == 50.00

        # edit category
        assert await edit_entry(entry_id, 'user1', category='Snack', conn=db)
        entry = await get_entry_by_id(entry_id, 'user1', conn=db)
        assert entry[2] == 'Snack'

        # edit note
        assert await edit_entry(entry_id, 'user1', note='new note', conn=db)
        entry = await get_entry_by_id(entry_id, 'user1', conn=db)
        assert entry[3] == 'new note'

    async def test_edit_2_fields(self, db):
        entry_id = await add_1_entry_return_id(db)
        
        # edit amount & category
        assert await edit_entry(entry_id, 'user1', amount=50.00, category='Snack', conn=db)
        entry = await get_entry_by_id(entry_id, 'user1', conn=db)
        assert entry[1] == 50.00
        assert entry[2] == 'Snack'

        # edit amount & note
        assert await edit_entry(entry_id, 'user1', amount=30.00, note='new note 1', conn=db)
        entry = await get_entry_by_id(entry_id, 'user1', conn=db)
        assert entry[1] == 30.00
        assert entry[3] == 'new note 1'

        # edit category & note
        assert await edit_entry(entry_id, 'user1', category='Other', note='new note 2', conn=db)
        entry = await get_entry_by_id(entry_id, 'user1', conn=db)
        assert entry[2] == 'Other'
        assert entry[3] == 'new note 2'

    async def test_edit_all_fields(self, db):
        entry_id = await add_1_entry_return_id(db)
                
        # edit amount & category
        assert await edit_entry(entry_id, 'user1', 
                                amount=50.00, 
                                category='Snack',
                                note='new note', conn=db)
        entry = await get_entry_by_id(entry_id, 'user1', conn=db)
        assert entry[1] == 50.00
        assert entry[2] == 'Snack'
        assert entry[3] == 'new note'

    async def test_edit_non_existent_entry(self, db):
        assert await get_entry_by_id(999, 'user1', conn=db) is None
        assert not await edit_entry(999, 'user1', amount=50.00, conn=db)

class TestDeleteEntry:
    async def test_delete_single_entry(self, db):
        entry_id = await add_1_entry_return_id(db)
        assert await delete_entry(entry_id, 'user1', conn=db)
        assert await get_entry_by_id(entry_id, 'user1', conn=db) is None

    async def test_delete_non_existent_entry(self, db):
        assert not await delete_entry(999, 'user1', conn=db)