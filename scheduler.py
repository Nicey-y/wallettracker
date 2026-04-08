from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta, timezone
import discord
import database
import pytz
import asyncio

SUMMARY_HOUR_INT_CODE = 20 # 8pm
SUNDAY_INT_CODE = 6
FIRST_DAY_OF_MONTH = 1

# We'll set this when the scheduler is started from bot.py
bot_instance = None

def get_period_start(budget_period: str) -> str:
    """Works out when the current budget period started in UTC."""
    now = datetime.now(timezone.utc)
    if budget_period == "daily":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif budget_period == "weekly":
        days_since_monday = now.weekday()
        start = (now - timedelta(days=days_since_monday)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
    elif budget_period == "monthly":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return start.strftime("%Y-%m-%d %H:%M:%S")

# ###########################################
# ----------- FOR TESTING PURPOSE -----------
# ###########################################
# def is_summary_due(budget_period: str, user_tz: str) -> bool:
#     return True  # temporary — remove after testing

def is_summary_due(budget_period: str, user_tz: str) -> bool:
    """Checks whether a summary should be fired right now for a given user.

    Fire at 8pm in the user's local timezone, on the last day of their budget period.

    Args:
        budget_period (str): 'daily', 'weekly', or 'monthly'
        user_tz (str): a valid pytz timezone string e.g. 'Australia/Melbourne'

    Returns:
        bool: _description_
    """

    try:
        tz = pytz.timezone(user_tz)
    except pytz.UnknownTimeZoneError:
        tz = pytz.utc
    
    local_now = datetime.now(tz)
    hour = local_now.hour
    weekday = local_now.weekday() # Monday=0, Sunday=6

    # The hourly job runs at the top of each hour, so this window is reliable
    if budget_period == "daily":
        return hour == SUMMARY_HOUR_INT_CODE
    
    elif budget_period == "weekly":
        # Check for Sunday as well
        return weekday == SUNDAY_INT_CODE and hour == SUMMARY_HOUR_INT_CODE
    
    elif budget_period == "monthly":
        # Last day of the month
        tomorrow = local_now + timedelta(days=1)
        is_last_day = tomorrow.day == FIRST_DAY_OF_MONTH
        return is_last_day and hour == SUMMARY_HOUR_INT_CODE

    return False

async def send_scheduled_summaries():
    """Runs every hour. Checks every user's budget period and timezone,
    and sends a summary if one is due.

    This function is called by the scheduler at the end of each period.
    Current period and call time:
    daily   - Evening if the day
    weekly  - Sunday
    monthly - End of the month

    Args:
        budget_period (str): _description_
    """

    print(f"[Scheduler] Hourly check running at {datetime.now(timezone.utc).strftime('%H:%M UTC')}...")

    try:
        all_budgets = await database.get_all_budgets()
        # row indices: 0=user_id, 1=guild_id, 2=budget_amount, 3=budget_period, 4=opted_in
        relevant = [row for row in all_budgets if row[3] == budget_period and row[4] == 1]

        for user_id, guild_id, budget_amount, budget_period, _ in relevant:

            # Get user's timezone
            user_tz = await database.get_user_timezone(user_id)

            # Check if a summary is due for this user right now
            if not is_summary_due(budget_period, user_tz):
                continue

            print(f"[Scheduler] Summary due for user {user_id} ({budget_period}, {user_tz})")

            # Get the channel to post in
            channel_id = await database.get_summary_channel(guild_id)
            if not channel_id:
                print(f"[Scheduler] No summary channel for guild {guild_id}, skipping.")
                continue

            channel = bot_instance.get_channel(int(channel_id))
            if not channel:
                print(f"[Scheduler] Could not find channel {channel_id}, skipping.")
                continue

            # Fetch entries for this period
            period_start = get_period_start(budget_period)
            entries      = await database.get_entries(user_id, guild_id, period_start)

            total_spent = sum(row[0] for row in entries)
            remaining   = budget_amount - total_spent
            over_budget = total_spent > budget_amount

            # Category breakdown
            category_totals = {}
            for row in entries:
                amount, category, note, timestamp = row
                category = category or "uncategorised"
                category_totals[category] = category_totals.get(category, 0) + amount

            # Build embed
            colour = discord.Colour.red() if over_budget else discord.Colour.green()
            embed  = discord.Embed(
                title=f"📊 {budget_period.capitalize()} Summary",
                description=f"Automatic summary for <@{user_id}>",
                colour=colour
            )
            embed.add_field(name="💰 Budget", value=f"${budget_amount:.2f}", inline=True)
            embed.add_field(name="💸 Spent",  value=f"${total_spent:.2f}",   inline=True)

            if over_budget:
                embed.add_field(name="🔴 Over by",   value=f"${abs(remaining):.2f}", inline=True)
            else:
                embed.add_field(name="🟢 Remaining", value=f"${remaining:.2f}",      inline=True)

            if category_totals:
                lines = [
                    f"`{cat}` — ${total:.2f}"
                    for cat, total in sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
                ]
                embed.add_field(name="📂 By Category", value="\n".join(lines), inline=False)

            embed.set_footer(text=f"Wallet Tracker · {len(entries)} entries this period")

            await channel.send(embed=embed)
            print(f"[Scheduler] Sent summary for user {user_id} in guild {guild_id}.")

    except Exception as e:
        import traceback
        print(f"[Scheduler] ERROR: {e}")
        traceback.print_exc()

    except Exception as e:
        import traceback
        print(f"[Scheduler] ERROR: {e}")
        traceback.print_exc()

def start_scheduler(bot):
    """Starts the scheduler with a single hourly job.
    Called once from bot.py after the bot connects.

    Args:
        bot (_type_): _description_
    """

    global bot_instance
    bot_instance = bot

    # Pass the running event loop explicitly so APScheduler
    # shares the same loop as discord.py
    loop = asyncio.get_running_loop()
    scheduler = AsyncIOScheduler(event_loop=loop)

    # test summary
    # test_time = datetime.now(timezone.utc) + timedelta(minutes=2)
    # scheduler.add_job(
    #     send_scheduled_summaries,
    #     CronTrigger(hour=test_time.hour, minute=test_time.minute, timezone="UTC")
    # )

    # Runs at the top of every hour
    scheduler.add_job(
        send_scheduled_summaries,
        CronTrigger(minute=0, timezone="UTC")
    )

    scheduler.start()
    print("[Scheduler] Started. Hourly check scheduled.")
    return scheduler

