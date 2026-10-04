import pytest
import pytest_asyncio

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.validate import *
from database import add_entry, get_recent_entries_by_user, RECENT_ENTRY_EDIT_LIMIT

pytest_asyncio_mode = "auto"
# pytest tests/test_02_add_entry.py -v

class TestAddEntry:
    # pytest tests/test_02_add_entry.py::TestAddEntry::test_add_single_entry -v
    async def test_add_single_entry(self, db):
        await add_entry(db,
                        user_id='user1',
                        amount=20.0,
                        category='Grocery')

        entries = await get_recent_entries_by_user(db, 'user1')

        assert len(entries) == 1
        assert entries[0][1] == 20.0
        assert entries[0][2] == 'Grocery'
        assert entries[0][3] is None
        assert entries[0][4] is not None

    async def test_add_single_entry_with_note(self, db):
        await add_entry(db,
                        user_id='user1',
                        amount=20.0,
                        category='Grocery',
                        note='test note')

        entries = await get_recent_entries_by_user(db, 'user1')

        assert len(entries) == 1
        assert entries[0][1] == 20.0
        assert entries[0][2] == 'Grocery'
        assert entries[0][3] == 'test note'
        assert entries[0][4] is not None

    async def test_add_multiple_entries_same_user(self, db):
        await add_entry(db,
                        user_id='user1',
                        amount=20.0,
                        category='Grocery',
                        note='test 1')
        await add_entry(db, 
                        user_id='user1',
                        amount=15.50,
                        category='Snack',
                        note='test 2')
        await add_entry(db,
                        user_id='user1',
                        amount=50.0,
                        category='Eat out & Takeaway')

        entries = await get_recent_entries_by_user(db, 'user1')

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
        await add_entry(db,
                        user_id='user1',
                        amount=20.0,
                        category='Grocery',
                        note='test 1')
        await add_entry(db,
                        user_id='user2',
                        amount=15.50,
                        category='Snack',
                        note='test 2')

        # GET is scoped to user
        entries_1 = await get_recent_entries_by_user(db, 'user1')
        assert len(entries_1) == 1
        assert entries_1[0][1] == 20.0
        assert entries_1[0][2] == 'Grocery'
        assert entries_1[0][3] == 'test 1'
        assert entries_1[0][4] is not None

        entries_2 = await get_recent_entries_by_user(db, 'user2')
        assert entries_2[0][1] == 15.50
        assert entries_2[0][2] == 'Snack'
        assert entries_2[0][3] == 'test 2'
        assert entries_2[0][4] is not None

    async def test_get_entry_limit(self, db, seed_15_entries_same_user):
        entries_5 = await get_recent_entries_by_user(db, 'user1', limit=5)
        assert len(entries_5) == 5

        entries_max = await get_recent_entries_by_user(db, 'user1')
        assert len(entries_max) == RECENT_ENTRY_EDIT_LIMIT

    async def test_get_entry_empty(self, db):
        entries = await get_recent_entries_by_user(db, 'user1')
        assert len(entries) == 0

# class TestEditEntry:
#     async def test_edit_single_field(self, db):
