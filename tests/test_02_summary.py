import pytest
import sqlite3
import pytest_asyncio
from helpers import *
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.validate import *
from database import set_budget, \
                    set_summary_channel_for_budget, get_summary_channel

pytest_asyncio_mode = "auto"
# pytest tests/test_02_summary.py -v

class TestSummary:
    async def test_set_summary_channel_pass(self, db):
        # Set budget
        await set_budget('user1', 20.00, 'daily', conn=db)

        # Set channel
        await set_summary_channel_for_budget('guild1', 'channel1', 'user1', 'daily', conn=db)
        guild, channel = await get_summary_channel('user1', 'daily', conn=db)
        assert guild == 'guild1'
        assert channel == 'channel1'

    async def test_change_summary_channel(self, db):
        # Set budget
        await set_budget('user1', 20.00, 'daily', conn=db)

        # Set channel
        await set_summary_channel_for_budget('guild1', 'channel1', 'user1', 'daily', conn=db)
        await set_summary_channel_for_budget('guild1', 'channel2', 'user1', 'daily', conn=db)
        guild, channel = await get_summary_channel('user1', 'daily', conn=db)
        assert guild == 'guild1'
        assert channel == 'channel2'

    async def test_change_summary_server(self, db):
        # Set budget
        await set_budget('user1', 20.00, 'daily', conn=db)

        # Set channel
        await set_summary_channel_for_budget('guild1', 'channel1', 'user1', 'daily', conn=db)
        await set_summary_channel_for_budget('guild2', 'channel2', 'user1', 'daily', conn=db)
        guild, channel = await get_summary_channel('user1', 'daily', conn=db)
        assert guild == 'guild2'
        assert channel == 'channel2'

    async def set_same_summary_channel_for_multiple_budgets(self, db):
        # Set budget
        await set_budget('user1', 20.00, 'daily', conn=db)
        await set_budget('user1', 40.00, 'weekly', conn=db)
        await set_budget('user1', 110.00, 'monthly', conn=db)

        await set_summary_channel_for_budget('guild1', 'channel1', 'user1', 'daily', conn=db)
        await set_summary_channel_for_budget('guild1', 'channel1', 'user1', 'weekly', conn=db)
        await set_summary_channel_for_budget('guild1', 'channel1', 'user1', 'monthly', conn=db)

        daily_server, daily_channel = await get_summary_channel('user1', 'daily', conn=db)
        assert daily_server == 'guild1'
        assert daily_channel == 'channel1'

        weekly_server, weekly_channel = await get_summary_channel('user1', 'weekly', conn=db)
        assert weekly_server == 'guild1'
        assert weekly_channel == 'channel1'

        monthly_server, monthly_channel = await get_summary_channel('user1', 'monthly', conn=db)
        assert monthly_server == 'guild1'
        assert monthly_channel == 'channel1'

    async def set_different_summary_channel_for_multiple_budgets(self, db):
        await set_budget('user1', 20.00, 'daily', conn=db)
        await set_budget('user1', 40.00, 'weekly', conn=db)
        await set_budget('user1', 110.00, 'monthly', conn=db)
        
        await set_summary_channel_for_budget('guild1', 'channel1', 'user1', 'daily', conn=db)
        await set_summary_channel_for_budget('guild2', 'channel2', 'user1', 'weekly', conn=db)
        await set_summary_channel_for_budget('guild3', 'channel3', 'user1', 'monthly', conn=db)

        daily_server, daily_channel = await get_summary_channel('user1', 'daily', conn=db)
        assert daily_server == 'guild1'
        assert daily_channel == 'channel1'

        weekly_server, weekly_channel = await get_summary_channel('user1', 'weekly', conn=db)
        assert weekly_server == 'guild2'
        assert weekly_channel == 'channel2'

        monthly_server, monthly_channel = await get_summary_channel('user1', 'monthly', conn=db)
        assert monthly_server == 'guild3'
        assert monthly_channel == 'channel3'

    async def test_set_summary_channel_invalid_budget_period(self, db):
        with pytest.raises(Exception) as e:
            await set_summary_channel_for_budget('guild1', 'channel1', 'user1', 'Daily', conn=db)
        assert "Cannot set channel for a non-existent budget" in str(e)

    async def test_get_none_if_none_set(self, db):
        server, channel = await get_summary_channel('user1', 'daily', conn=db)
        assert server is None
        assert channel is None