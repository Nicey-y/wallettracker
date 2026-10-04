import pytest
from datetime import datetime, timezone
from unittest.mock import patch

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from scheduler import is_summary_due, get_period_start

# pytest tests/test_03_scheduler.py -v

class TestGetPeriodStart:
    def test_daily_returns_midnight(self):
        """Daily period start is midnight of the given date.
        """
        mock_now = datetime(2024, 6, 15, 14, 30, 0, tzinfo=timezone.utc)
        with patch('scheduler.datetime') as mock_dt:
            mock_dt.now.return_value = mock_now
            result = get_period_start('daily')
        assert result == "2024-06-15 00:00:00"

    def test_weekly_returns_monday_midnight(self):
        """Weekly period start is midnight start of Monday of the week of 
        the current date.
        e.g. 2024-06-15 is a Saturday -> Monday was 2024-06-10.
        """
        mock_now = datetime(2024, 6, 15, 14, 30, 0, tzinfo=timezone.utc)
        with patch("scheduler.datetime") as mock_dt:
            mock_dt.now.return_value = mock_now
            result = get_period_start("weekly")
        assert result == "2024-06-10 00:00:00"

    def test_monthly_returns_first_of_month_midnight(self):
        """Monthly period start is the midnight start of the first day of the 
        current month.
        """
        mock_now = datetime(2024, 6, 15, 14, 30, 0, tzinfo=timezone.utc)
        with patch("scheduler.datetime") as mock_dt:
            mock_dt.now.return_value = mock_now
            result = get_period_start("monthly")
        assert result == "2024-06-01 00:00:00"

    def test_unknown_period_returns_midnight(self):
        """Unknown period falls back to start of today.
        """
        mock_now = datetime(2024, 6, 15, 14, 30, 0, tzinfo=timezone.utc)
        with patch("scheduler.datetime") as mock_dt:
            mock_dt.now.return_value = mock_now
            result = get_period_start("unknown")
        assert result == "2024-06-15 00:00:00"

class TestIsSummaryDue:
    # pytest tests/test_03_scheduler.py::TestIsSummaryDue::test_daily_due_at_8pm -v
    def test_daily_due_at_8pm(self):
        """Daily summary is due 8pm local time.
        """
        import pytz
        melb_tz = pytz.timezone("Australia/Melbourne")
        # 8pm Melbourne = 9am UTC (Melbourne is currently UTC+11)
        mock_now = melb_tz.localize(datetime(2024, 6, 15, 20, 0, 0))

        with patch("scheduler.datetime") as mock_dt:
            mock_dt.now.return_value = mock_now
            assert is_summary_due("daily", "Australia/Melbourne") is True

    def test_daily_not_due_at_other_hours(self):
        """Daily summary should not be due at hours that aren't 8pm local.
        """
        import pytz
        melb_tz = pytz.timezone("Australia/Melbourne")
        # 4pm Melbourne time
        mock_now = melb_tz.localize(datetime(2024, 6, 15, 16, 0, 0))

        with patch("scheduler.datetime") as mock_dt:
            mock_dt.now.return_value = mock_now
            assert is_summary_due("daily", "Australia/Melbourne") is False

    def test_weekly_due_sunday_8pm(self):
        """Weekly summary is due on Sunday 8pm local time.
        2024-06-16 is a Sunday.
        """
        import pytz
        melb_tz = pytz.timezone("Australia/Melbourne")
        mock_now = melb_tz.localize(datetime(2024, 6, 16, 20, 0, 0))  # Sunday 8pm

        with patch("scheduler.datetime") as mock_dt:
            mock_dt.now.return_value = mock_now
            assert is_summary_due("weekly", "Australia/Melbourne") is True

    def test_weekly_not_due_on_weekday(self):
        """Weekly summary should not be due on a day other than Sunday.
        2024-06-15 is a Saturday.
        """
        import pytz
        melb_tz = pytz.timezone("Australia/Melbourne")
        mock_now = melb_tz.localize(datetime(2024, 6, 15, 20, 0, 0))  # Saturday 8pm

        with patch("scheduler.datetime") as mock_dt:
            mock_dt.now.return_value = mock_now
            assert is_summary_due("weekly", "Australia/Melbourne") is False

    def test_monthly_due_on_last_day(self):
        """Monthly summary should be due on the last day of the month at 8pm.
        2024-06-30 is the last day of June.
        """
        import pytz
        melb_tz = pytz.timezone("Australia/Melbourne")
        mock_now = melb_tz.localize(datetime(2024, 6, 30, 20, 0, 0))  # June 30 8pm

        with patch("scheduler.datetime") as mock_dt:
            mock_dt.now.return_value = mock_now
            assert is_summary_due("monthly", "Australia/Melbourne") is True

    def test_monthly_not_due_mid_month(self):
        """Monthly summary should not be due mid month.
        """
        import pytz
        melb_tz = pytz.timezone("Australia/Melbourne")
        mock_now = melb_tz.localize(datetime(2024, 6, 15, 20, 0, 0))  # June 15 8pm

        with patch("scheduler.datetime") as mock_dt:
            mock_dt.now.return_value = mock_now
            assert is_summary_due("monthly", "Australia/Melbourne") is False

    def test_invalid_timezone_defaults_to_utc(self):
        """An invalid timezone should fall back to UTC without crashing.
        """
        import pytz
        melb_tz = pytz.timezone("Australia/Melbourne")
        mock_now = melb_tz.localize(datetime(2024, 6, 15, 20, 0, 0))
        with patch("scheduler.datetime") as mock_dt:
            mock_dt.now.return_value = mock_now

            # Default to UTC, no exception raised
            result = is_summary_due("daily", "Invalid/Timezone")
            assert isinstance(result, bool)