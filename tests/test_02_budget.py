import pytest
import sqlite3
import pytest_asyncio
from helpers import *
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.validate import *
from database import set_budget, get_budget_for_user_period

pytest_asyncio_mode = "auto"
# pytest tests/test_02_budget.py -v

class TestBudget:
    async def test_set_new_valid_budget_pass(self, db):
        # Daily
        await set_budget('user1', 10.00, 'daily', db)
        budget = await get_budget_for_user_period('user1', 'daily', db)
        assert budget
        assert budget[0] == 10.00
        assert budget[1] == 'daily'

        # Weekly
        await set_budget('user1', 40.00, 'weekly', conn=db)
        budget = await get_budget_for_user_period('user1', 'weekly', conn=db)
        assert budget
        assert budget[0] == 40.00
        assert budget[1] == 'weekly'

        # Monthly
        await set_budget('user1', 160.00, 'monthly', conn=db)
        budget = await get_budget_for_user_period('user1', 'monthly', conn=db)
        assert budget
        assert budget[0] == 160.00
        assert budget[1] == 'monthly'

    async def test_change_budget_for_valid_period_pass(self, db):
        # Daily
        await set_budget('user1', 10.00, 'daily', conn=db)
        await set_budget('user1', 20.00, 'daily', conn=db)
        budget = await get_budget_for_user_period('user1', 'daily', conn=db)
        assert budget
        assert budget[0] == 20.00
        assert budget[1] == 'daily'

        # Weekly
        await set_budget('user1', 40.00, 'weekly', conn=db)
        await set_budget('user1', 80.00, 'weekly', conn=db)
        budget = await get_budget_for_user_period('user1', 'weekly', conn=db)
        assert budget
        assert budget[0] == 80.00
        assert budget[1] == 'weekly'

        # Monthly
        await set_budget('user1', 160.00, 'monthly', conn=db)
        await set_budget('user1', 320.00, 'monthly', conn=db)
        budget = await get_budget_for_user_period('user1', 'monthly', conn=db)
        assert budget
        assert budget[0] == 320.00
        assert budget[1] == 'monthly'

    async def test_get_for_no_budget_set(self, db):
        assert await get_budget_for_user_period('user1', 'daily', conn=db) is None

    async def test_get_invalid_budget_period(self, db):
        await set_budget('user1', 160.00, 'monthly', conn=db)
        assert await get_budget_for_user_period('user1', 'Monthly', conn=db) is None

    async def test_invalid_budget_period_set_exception(self, db):
        with pytest.raises(Exception) as e:
            await set_budget('user1', 160.00, 'Monthly', conn=db)
        assert "CHECK constraint failed" in str(e)

    async def test_invalid_budget_amount_set_exception(self, db):
        with pytest.raises(Exception) as e:
            await set_budget('user1', -160.00, 'Monthly', conn=db)
        assert "CHECK constraint failed" in str(e)