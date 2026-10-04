import discord
from discord import app_commands
import database

async def period_autocomplete(
    interaction: discord.Interaction,
    current: str
) -> list[app_commands.Choice[str]]:
    """Autocomplete to show a dropdown of only the budget periods the user has registered.
    """
    periods = await database.get_periods_for_user(str(interaction.user.id))

    return [
        app_commands.Choice(name=period.capitalize(), value=period)
        for period in periods
        if current.lower() in period.lower()
    ]