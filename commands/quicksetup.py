import discord
from discord import app_commands
import pytz
import database

# discord.ui.Modal is Discord's built-in pop-up form system
class QuickSetupModal(discord.ui.Modal,
                      title="FinanceTracker Quick Setup"):
    """A pop-up form that collects all setup info in one go.

    Args:
        discord (_type_): _description_
        title (str, optional): _description_. Defaults to "FinanceTracker Quick Setup".
    """

    budget_amount = discord.ui.TextInput(
        label="Budget Amount",
        placeholder="e.g. 500",
        required=True,
        max_length=10
    )

    budget_period = discord.ui.TextInput(
        label="Budget Period",
        placeholder="daily / weekly / monthly",
        required=True,
        max_length=10
    )

    summary_channel = discord.ui.TextInput(
        label="Summary Channel Name",
        placeholder="e.g. general (without the # symbol)",
        required=True,
        max_length=100
    )

    user_timezone = discord.ui.TextInput(
        label="timezone",
        placeholder="e.g. Australia/Melbourne, America/New_York",
        required=True,
        max_length=50
    )

    def __init__(self, guild: discord.Guild):
        super().__init__()

        # We need the guild to look up the channel by name later
        self.guild = guild
    
    async def on_submit(self, 
                        interaction: discord.Interaction):
        
        # Collect errors to raise at the end in order to not interrupt the
        # form filling process
        errors = []

        # --- Validate budget amount ---
        try:
            amount = float(self.budget_amount.value)
            if amount <= 0:
                errors.append("❌ Budget amount must be greater than zero.")
        except ValueError:
            errors.append("❌ Budget amount must be a number (e.g. 500 or 99.99).")
            amount = None

        # --- Validate budget period ---
        period = self.budget_period.value.strip().lower()
        if period not in ("daily", "weekly", "monthly"):
            errors.append("❌ Budget period must be `daily`, `weekly`, or `monthly`.")
        
        # --- Validate timezone ---
        tz = self.user_timezone.value.strip()
        if tz not in pytz.all_timezones:
            errors.append(
                f"❌ `{tz}` is not a valid timezone. "
                f"Use the format `Region/City` e.g. `Australia/Melbourne`.\n"
                f"Full list: <https://en.wikipedia.org/wiki/List_of_tz_database_time_zones>"
            )
        
        # --- Validate channel ---
        # The user types a channel name, so we look it up in the guild
        channel_name = self.summary_channel.value.strip().lstrip("#")

        # searches the server's channel list by name
        channel = discord.utils.get(self.guild.text_channels, name=channel_name)
        if channel is None:
            errors.append(
                f"❌ Could not find a text channel named `#{channel_name}` in this server. "
                f"Make sure the name is spelled exactly right."
            )
        
        # If any validation failed, show all errors at once ---
        if errors:
            await interaction.response.send_message(
                "\n\n".join(errors),
                ephemeral=True
            )
            return
        
        # All valid -> save everything
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild.id)

        await database.set_budget(user_id, guild_id, amount, period)
        await database.set_summary_channel(guild_id, str(channel.id))
        await database.set_user_timezone(user_id, tz)

        # Confirm back to the user with a summary of what was set
        local_time = __import__('datetime').datetime.now(
            pytz.timezone(tz)
        ).strftime("%H:%M, %A %d %B %Y")

        await interaction.response.send_message(
            f"✅ **FinanceTracker is all set up!**\n\n"
            f"💰 **Budget:** ${amount:.2f} per {period}\n"
            f"📢 **Summary channel:** {channel.mention}\n"
            f"🌏 **Timezone:** `{tz}` (your local time: {local_time})\n\n"
            f"You can start logging spending with `/log spend`.",
            ephemeral=True
        )
    
    async def on_error(self, 
                       interaction: discord.Interaction, 
                       error: Exception):
        """Catches any unexpected errors inside the modal."""
        
        import traceback
        traceback.print_exc()
        await interaction.response.send_message(
            "❌ Something went wrong during setup. Please try again.",
            ephemeral=True
        )

class QuickSetupCommands(app_commands.Group):

    def __init__(self):
        super().__init__(name="quicksetup", 
                         description="Set up FinanceTracker in one go")
        
    @app_commands.command(name="start",
                          description="Run the quick setup wizard to get started")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def start(self,
                    interaction: discord.Interaction):
        """Opens the quick setup modal.

        Args:
            interaction (discord.Interaction): _description_
        """
        modal = QuickSetupModal(guild=interaction.guild)
        await interaction.response.send_modal(modal)