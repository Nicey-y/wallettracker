import discord
from discord.ext import commands
from discord import app_commands
import asyncio

import config
import database
from commands.log import LogCommands
from commands.budget import BudgetCommands
from commands.summary import SummaryCommands
from commands.quicksetup import QuickSetupCommands
from commands.help import HelpCommands
from scheduler import start_scheduler

# --- Bot setup ---
# Intents are permissions that tell Discord what events your bot wants to receive.
# The default set covers most things; we add members so we can see who's in the server.
intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!",
                   intents=intents)

# --- Register command groups ---
bot.tree.add_command(LogCommands())
bot.tree.add_command(BudgetCommands())
bot.tree.add_command(SummaryCommands())
bot.tree.add_command(QuickSetupCommands())
bot.tree.add_command(HelpCommands())

# --- Events ---

@bot.event
async def on_ready():
    """ Fires once when the bot successfully connects to Discord.
    """
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")

    # Set up database tables on startup
    await database.init_db()

    start_scheduler(bot) 
    
    print("About to sync...")

    try:
        for guild_id in config.GUILD_IDS:
            print(f"Syncing to guild {guild_id}...")
            guild = discord.Object(id=guild_id)
            bot.tree.copy_global_to(guild=guild)
            await bot.tree.sync(guild=guild)
            print(f"Synced to guild {guild_id}.")
        print("All guilds synced.")
    except Exception as e:
        import traceback
        print(f"Sync error: {e}")
        traceback.print_exc()

@bot.event
async def on_guild_join(guild):
    """ Fires when the bot is added to a new server.

    Args:
        guild (_type_): _description_
    """
    print(f"Joined new guild: {guild.name} (ID: {guild.id})")

# --- Slash Commands ---

@bot.tree.command(name="ping",
                  description="Check if Wallet Tracker is online")
async def ping(interaction: discord.Interaction):
    """ A simple test command. If this works, everything is wired up correctly.

    Args:
        interaction (discord.Interaction): _description_
    """
    await interaction.response.send_message(
        f"Pong! Wallet Tracker is online. Latency: {round(bot.latency * 1000)}ms",
        ephemeral=True # ephemeral=True means only the person who ran the command can see the reply
    )

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    """Catches any unhandled errors in slash commands and prints them."""
    
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message(
            "❌ You don't have permission to use this command.",
            ephemeral=True
        )
        return
    
    print(f"Error in command '{interaction.command.name}': {error}")
    import traceback
    traceback.print_exc()
    
    # Try to respond to the user if we haven't already
    try:
        await interaction.response.send_message(
            "❌ Something went wrong. Check the bot console for details.",
            ephemeral=True
        )
    except discord.InteractionResponded:
        pass  # interaction was already responded to, that's fine

# --- Entry point ---
async def main():
    async with bot:
        await bot.start(config.TOKEN)

# Standard Python entry point pattern
# asyncio.run() starts the async event loop and runs main()
asyncio.run(main())