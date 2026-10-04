import pytest
import sqlite3
import pytest_asyncio
from helpers import *
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.validate import *
from database import set_budget, get_budget_for_period, \
                    set_summary_channel_for_budget, get_summary_channel, get_entries_for_user_since

pytest_asyncio_mode = "auto"
# pytest tests/test_02_summary.py -v

class TestSummary:
    async def test_set_summary_channel_pass(self, db):
        # Set budget
        await set_budget(db, 'user1', 20.00, 'daily')

        # Set channel
        await set_summary_channel_for_budget(db, 'guild1', 'channel1', 'user1', 'daily')
        guild, channel = await get_summary_channel(db, 'user1', 'daily')
        assert guild == 'guild1'
        assert channel == 'channel1'

    async def test_change_summary_channel(self, db):
        # Set budget
        await set_budget(db, 'user1', 20.00, 'daily')

        # Set channel
        await set_summary_channel_for_budget(db, 'guild1', 'channel1', 'user1', 'daily')
        await set_summary_channel_for_budget(db, 'guild1', 'channel2', 'user1', 'daily')
        guild, channel = await get_summary_channel(db, 'user1', 'daily')
        assert guild == 'guild1'
        assert channel == 'channel2'

    async def test_change_summary_server(self, db):
        # Set budget
        await set_budget(db, 'user1', 20.00, 'daily')

        # Set channel
        await set_summary_channel_for_budget(db, 'guild1', 'channel1', 'user1', 'daily')
        await set_summary_channel_for_budget(db, 'guild2', 'channel2', 'user1', 'daily')
        guild, channel = await get_summary_channel(db, 'user1', 'daily')
        assert guild == 'guild2'
        assert channel == 'channel2'

    async def set_same_summary_channel_for_multiple_budgets(self, db):
        # Set budget
        await set_budget(db, 'user1', 20.00, 'daily')
        await set_budget(db, 'user1', 40.00, 'weekly')
        await set_budget(db, 'user1', 110.00, 'monthly')

        await set_summary_channel_for_budget(db, 'guild1', 'channel1', 'user1', 'daily')
        await set_summary_channel_for_budget(db, 'guild1', 'channel1', 'user1', 'weekly')
        await set_summary_channel_for_budget(db, 'guild1', 'channel1', 'user1', 'monthly')

        daily_server, daily_channel = await get_summary_channel(db, 'user1', 'daily')
        assert daily_server == 'guild1'
        assert daily_channel == 'channel1'

        weekly_server, weekly_channel = await get_summary_channel(db, 'user1', 'weekly')
        assert weekly_server == 'guild1'
        assert weekly_channel == 'channel1'

        monthly_server, monthly_channel = await get_summary_channel(db, 'user1', 'monthly')
        assert monthly_server == 'guild1'
        assert monthly_channel == 'channel1'

    async def set_different_summary_channel_for_multiple_budgets(self, db):
        await set_budget(db, 'user1', 20.00, 'daily')
        await set_budget(db, 'user1', 40.00, 'weekly')
        await set_budget(db, 'user1', 110.00, 'monthly')
        
        await set_summary_channel_for_budget(db, 'guild1', 'channel1', 'user1', 'daily')
        await set_summary_channel_for_budget(db, 'guild2', 'channel2', 'user1', 'weekly')
        await set_summary_channel_for_budget(db, 'guild3', 'channel3', 'user1', 'monthly')

        daily_server, daily_channel = await get_summary_channel(db, 'user1', 'daily')
        assert daily_server == 'guild1'
        assert daily_channel == 'channel1'

        weekly_server, weekly_channel = await get_summary_channel(db, 'user1', 'weekly')
        assert weekly_server == 'guild2'
        assert weekly_channel == 'channel2'

        monthly_server, monthly_channel = await get_summary_channel(db, 'user1', 'monthly')
        assert monthly_server == 'guild3'
        assert monthly_channel == 'channel3'

    async def test_set_summary_channel_invalid_budget_period(self, db):
        with pytest.raises(Exception) as e:
            await set_summary_channel_for_budget(db, 'guild1', 'channel1', 'user1', 'Daily')
        assert "Cannot set channel for a non-existent budget" in str(e)

    async def test_get_none_if_none_set(self, db):
        server, channel = await get_summary_channel(db, 'user1', 'daily')
        assert server is None
        assert channel is None