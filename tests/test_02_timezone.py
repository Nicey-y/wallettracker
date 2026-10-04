import pytest
import sqlite3
import pytest_asyncio
from helpers import *
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database import set_user_timezone, get_user_timezone

pytest_asyncio_mode = "auto"
# pytest tests/test_02_timezone.py -v

class TestUserTimezone:

    async def test_set_and_get_timezone(self, db):
        await set_user_timezone("user1", "Australia/Melbourne", conn=db)
        tz = await get_user_timezone("user1", conn=db)
        assert tz == "Australia/Melbourne"

    async def test_get_timezone_default(self, db):
        """User's default timezone is UTC.
        """
        tz = await get_user_timezone("user1", conn=db)
        assert tz == "UTC"

    async def test_set_timezone_overwrites(self, db):
        await set_user_timezone("user1", "Australia/Melbourne", conn=db)
        await set_user_timezone("user1", "America/New_York", conn=db)
        tz = await get_user_timezone("user1", conn=db)
        assert tz == "America/New_York"