from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta, timezone
from discord.ext import commands
import discord
import database
import asyncio
import config

# --- Bot setup ---
# Intents are permissions that tell Discord what events your bot wants to receive.
# The default set covers most things; we add members so we can see who's in the server.
intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!",
                   intents=intents)

# # --- Register command groups ---
# bot.tree.add_command(LogCommands())
# bot.tree.add_command(BudgetCommands())
# bot.tree.add_command(SummaryCommands())

# --- Events ---

@bot.event
async def on_ready():
    """ Fires once when the bot successfully connects to Discord.
    """
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")

    # Set up database tables on startup
    # await database.init_db()

    start_scheduler(bot) 
    
    # Sync slash commands to your test server.
    # This tells Discord "here are the commands this bot has".
    guild = discord.Object(id=config.GUILD_ID)
    
    # guild= makes it sync instantly to just your test server.
    # Without guild=, it syncs globally but takes up to an hour to propagate.
    bot.tree.copy_global_to(guild=guild) 
    print("About to sync...")
    await bot.tree.sync(guild=guild)
    print(f"Slash commands synced to guild {config.GUILD_ID}.")

async def send_scheduled_summaries(budget_period: str):
    print(f"[Scheduler] Function called for period: {budget_period}")

def start_scheduler(bot):
    """Creates the scheduler and registers all periodic jobs.
    Called once from bot.py after the bot connects.

    Args:
        bot (_type_): _description_
    """

    global bot_instance
    bot_instance = bot

    # Pass the running event loop explicitly so APScheduler
    # shares the same loop as discord.py
    curr_loop = asyncio.get_running_loop()
    print(f"--- loop is: {curr_loop}")
    scheduler = AsyncIOScheduler(loop=curr_loop)

    test_time = datetime.now(timezone.utc) + timedelta(minutes=2)
    print(f"--- current time: {datetime.now(timezone.utc)}\n--- job will fire at {test_time}")

    # test summary, fires 2 minutes after the bot is started up
    scheduler.add_job(
        send_scheduled_summaries,
        CronTrigger(hour=test_time.hour, minute=test_time.minute, timezone="UTC"),
        args=["daily"]
    )

    # Daily summaries - fire at 8pm UTC everyday
    # scheduler.add_job(
    #     send_scheduled_summaries,
    #     CronTrigger(hour=20, minute=0), # 8pm
    #     args=["daily"]
    # )

    # Weekly summaries - fire at 8pm UTC every Sunday
    scheduler.add_job(
        send_scheduled_summaries,
        CronTrigger(day_of_week="sun", hour=20, minute=0), # 8pm sunday
        args=["weekly"]
    )

    # Monthly summaries - fire at 8pm UTC on the last day of each month
    scheduler.add_job(
        send_scheduled_summaries,
        CronTrigger(day="last", hour=20, minute=0),
        args=["monthly"]
    )

    scheduler.start()
    print("[Scheduler] Started. Jobs scheduled for daily, weekly, and monthly summaries.")
    return scheduler

# --- Entry point ---
async def main():
    async with bot:
        print("--- starting up the bot")
        await bot.start(config.TOKEN)
        # print("--- bot started up. start scheduling")
        # start_scheduler(bot)

# Standard Python entry point pattern
# asyncio.run() starts the async event loop and runs main()
asyncio.run(main())