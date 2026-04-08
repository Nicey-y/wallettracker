import discord
from discord import app_commands
import database

# The valid period choices the user can pick from.
# Using a fixed list prevents users from entering arbitrary strings like
# "fortnightly" or "yearly" that the scheduler won't know how to handle.
VALID_PERIODS = ['daily', 'weekly', 'monthly']

class BudgetCommands(app_commands.Group):
    """ Group of commands related to budget management.

    Args:
        app_commands (_type_): _description_
    """

    def __init__(self):
        super().__init__(name="budget",
                         description="Manage your budget")
    
    # '/budget set' command
    @app_commands.command(name="set",
                          description="Set your spending budget")
    @app_commands.describe(
        amount="Your total budget for the period (e.g. 500)",
        period="How often your budget resets"
    )
    # show a dropdown menu for the period argument
    @app_commands.choices(period=[
        app_commands.Choice(name="Daily",   value="daily"),
        app_commands.Choice(name="Weekly",  value="weekly"),
        app_commands.Choice(name="Monthly",  value="monthly"),
    ])
    async def set_budget(
        self,
        interaction: discord.Interaction,
        amount: float,
        period: app_commands.Choice[str]
    ):
        # Validate amount
        if amount <= 0:
            await interaction.response.send_message(
                "❌ Budget must be greater than zero.",
                ephemeral=False
            )
            return
        
        await database.set_budget(
            user_id=str(interaction.user.id),
            guild_id=str(interaction.guild.id),
            amount=amount,
            period=period.value # period is a Choice object, .value gives us the string
        )

        await interaction.response.send_message(
            f"✅ Budget set to **${amount:.2f}** per **{period.name.lower()}**.\n"
            f"FinanceTracker will track your spending against this budget.",
            ephemeral=False
        )

    # '/budget setchannel' command
    @app_commands.command(name="setchannel",
                          description="Set the channel where automatic summaries are posted")
    @app_commands.describe(channel="The channel to post summaries in")
    # only users with the "Manage Server" permission can run this command
    @app_commands.checks.has_permissions(manage_guild=True)
    async def set_channel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel # show a channel picker in the slash command UI
                                     # user clicks a channel from a dropdown rather than typing a name
    ):
        await database.set_summary_channel(
            guild_id=str(interaction.guild.id),
            channel_id=str(channel.id)
        )

        await interaction.response.send_message(
            f"Automatic summaries will be posted in {channel.mention}.",
            ephemeral=False
        )