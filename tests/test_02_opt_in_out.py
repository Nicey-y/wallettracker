import pytest
import sqlite3
import pytest_asyncio
from helpers import *
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.validate import *
from database import set_budget, set_summary_channel_for_budget, \
    set_opted_out_for_period, get_opted_in_for_period, get_all_opted_in_budgets

pytest_asyncio_mode = "auto"
# pytest tests/test_02_opt_in_out.py -v

class TestOptInOut:
    async def test_default_opt_in(self, db):
        await set_budget(db, 'user1', 20.00, 'daily')
        await set_summary_channel_for_budget(db, 'guild1', 'channel1', 'user1', 'daily')
        assert await get_opted_in_for_period(db, 'user1', 'daily')

    async def test_opt_out(self, db):
        await set_budget(db, 'user1', 20.00, 'daily')
        await set_summary_channel_for_budget(db, 'guild1', 'channel1', 'user1', 'daily')
        assert await set_opted_out_for_period(db, 'user1', 'daily') > 0 # opt out

        assert not await get_opted_in_for_period(db, 'user1', 'daily')

    async def test_opt_back_in(self, db):
        await set_budget(db, 'user1', 20.00, 'daily')
        await set_summary_channel_for_budget(db, 'guild1', 'channel1', 'user1', 'daily')

        # opt out
        assert await set_opted_out_for_period(db, 'user1', 'daily') > 0
        assert not await get_opted_in_for_period(db, 'user1', 'daily')

        # opt back in
        await set_summary_channel_for_budget(db, 'guild1', 'channel1', 'user1', 'daily')
        assert await get_opted_in_for_period(db, 'user1', 'daily')

    async def test_opt_out_non_existent_budget(self, db):
        assert await set_opted_out_for_period(db, 'user1', 'daily') == 0 

    async def test_get_all_opted_in(self, db):
        period = ['daily', 'weekly', 'monthly']
        for i in range(1, 6):
            await set_budget(db, f'user{i}', 10.00 * i, period[i%3])
            await set_summary_channel_for_budget(db, f'guild{i}', f'channel{i}', f'user{i}', period[i%3])

        summaries = await get_all_opted_in_budgets(db)
        assert len(summaries) == 5

    async def test_no_opt_in(self, db):
        summaries = await get_all_opted_in_budgets(db)
        assert len(summaries) == 0