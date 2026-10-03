import database
import pytz
import discord

def validate_amount(amount) -> str | None:
    """Return error message as string if amount is invalid, None otherwise

    Args:
        amount (float): amount of money

    Returns:
        str | None: _description_
    """
    try:
        amount_float = float(amount)
    except ValueError:
        return "❌ Budget amount must be a number (e.g. 500 or 99.99)."
    
    if amount_float is None or amount_float <= 0:
        return "❌ Amount must be greater than zero."
    else:
        return None

def validate_edit(amount: float | None,
                category: str | None,
                note: str | None) -> str | None:
    """Return error message as string if user doesn't provide at least one field to change

    Args:
        amount (float | None): _description_
        category (str | None): _description_
        note (str | None): _description_

    Returns:
        str | None: _description_
    """
    if amount is None and category is None and note is None:
        return "❌ Please provide at least one field to update (amount, category, or note)."
    else:
        return None

def validate_entry_query_limit(limit: int) -> str | None:
    """Keep the amount of entry queried between 1 and 10

    Args:
        limit (int): _description_

    Returns:
        str | None: _description_
    """
    if limit < 1 or limit > database.RECENT_ENTRY_EDIT_LIMIT:
        return "❌ Limit must be between 1 and 10."
    else:
        return None

def validate_period(period: str) -> str | None:
    if period not in ("daily", "weekly", "monthly"):
        return "❌ Budget period must be `daily`, `weekly`, or `monthly`."
    else:
        return None

def validate_timezone(tz: str) -> str | None:
    if tz not in pytz.all_timezones:
        return f"❌ `{tz}` is not a valid timezone.\nUse the format `Region/City` e.g. `Australia/Melbourne`.\nFull list: <https://en.wikipedia.org/wiki/List_of_tz_database_time_zones>"
    else:
        return None

def validate_channel(channel_name) -> str | None:
    if channel_name is None:
        return f"❌ Could not find a text channel named `#{channel_name}` in this server.\nMake sure the name is spelled exactly right."
    else:
        return None