import discord
from discord import app_commands
import pytz
import database
from utils.validate import *

# discord.ui.Modal is Discord's built-in pop-up form system
class QuickSetupModal(discord.ui.Modal,
                      title="Wallet Tracker Quick Setup"):
    """A pop-up form that collects all setup info in one go.

    Args:
        discord (_type_): _description_
        title (str, optional): _description_. Defaults to "Wallet Tracker Quick Setup".
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
        amount = float(self.budget_amount.value)
        msg = validate_amount(amount)
        if msg:
            errors.append(msg)

        # --- Validate budget period ---
        # validate_period
        period = self.budget_period.value.strip().lower()
        msg = validate_period(period)
        if msg:
            errors.append(msg)
        
        # --- Validate timezone ---
        tz = self.user_timezone.value.strip()
        msg = validate_timezone(tz)
        if msg:
            errors.append(msg)
        
        # --- Validate channel ---
        # The user types a channel name, so we look it up in the guild
        channel_name = self.summary_channel.value.strip().lstrip("#")

        # searches the server's channel list by name
        # validate_channel
        channel = discord.utils.get(self.guild.text_channels, name=channel_name)
        msg = validate_channel(channel)
        if msg:
            errors.append(msg)
        
        # If any validation failed, show all errors at once ---
        if errors:
            await interaction.response.send_message(
                "\n\n".join(errors),
                ephemeral=False
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
            f"✅ **Wallet Tracker is all set up!**\n\n"
            f"💰 **Budget:** ${amount:.2f} per {period}\n"
            f"📢 **Summary channel:** {channel.mention}\n"
            f"🌏 **Timezone:** `{tz}` (your local time: {local_time})\n\n"
            f"You can start logging spending with `/log spend`.",
            ephemeral=False
        )
    
    async def on_error(self, 
                       interaction: discord.Interaction, 
                       error: Exception):
        """Catches any unexpected errors inside the modal."""
        
        import traceback
        traceback.print_exc()
        await interaction.response.send_message(
            "❌ Something went wrong during setup. Please try again.",
            ephemeral=False
        )

class QuickSetupCommands(app_commands.Group):

    def __init__(self):
        super().__init__(name="quicksetup", 
                         description="Set up Wallet Tracker in one go")
        
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