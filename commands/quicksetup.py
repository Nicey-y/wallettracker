import discord
from discord import app_commands
import pytz
import aiosqlite
import database
from utils.validate import *

class PeriodSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Daily",   value="daily"),
            discord.SelectOption(label="Weekly",  value="weekly"),
            discord.SelectOption(label="Monthly", value="monthly"),
        ]
        super().__init__(
            placeholder='Select your budget period',
            min_values=1,
            max_values=1,   # only one can be selected at a time
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        # defer() because we don't want to send a new message
        # just record the selection and wait for user to the Continue button
        self.view.selected_period = self.values[0]
        await interaction.response.defer()

class ChannelSelect(discord.ui.ChannelSelect):
    def __init__(self):
        super().__init__(
            placeholder='Select a channel to send your summaries to',
            min_values=1,
            max_values=1,
            channel_types=[discord.ChannelType.text]  # text channels only
        )

    async def callback(self, interaction: discord.Interaction):
        self.view.selected_channel = str(self.values[0].id)
        await interaction.response.defer()

class TimezoneSelect(discord.ui.Select):
    def __init__(self):
        options = [
            # Americas
            discord.SelectOption(label="Pacific/Honolulu",    value="Pacific/Honolulu"),
            discord.SelectOption(label="America/Anchorage",   value="America/Anchorage"),
            discord.SelectOption(label="America/Los_Angeles", value="America/Los_Angeles"),
            discord.SelectOption(label="America/Denver",      value="America/Denver"),
            discord.SelectOption(label="America/Chicago",     value="America/Chicago"),
            discord.SelectOption(label="America/New_York",    value="America/New_York"),
            discord.SelectOption(label="America/Sao_Paulo",   value="America/Sao_Paulo"),

            # Europe & Africa
            discord.SelectOption(label="Europe/London",       value="Europe/London"),
            discord.SelectOption(label="Europe/Paris",        value="Europe/Paris"),
            discord.SelectOption(label="Europe/Helsinki",     value="Europe/Helsinki"),
            discord.SelectOption(label="Europe/Moscow",       value="Europe/Moscow"),
            discord.SelectOption(label="Asia/Dubai",          value="Asia/Dubai"),

            # Asia
            discord.SelectOption(label="Asia/Karachi",        value="Asia/Karachi"),
            discord.SelectOption(label="Asia/Kolkata",        value="Asia/Kolkata"),
            discord.SelectOption(label="Asia/Dhaka",          value="Asia/Dhaka"),
            discord.SelectOption(label="Asia/Bangkok",        value="Asia/Bangkok"),
            discord.SelectOption(label="Asia/Shanghai",       value="Asia/Shanghai"),
            discord.SelectOption(label="Asia/Tokyo",          value="Asia/Tokyo"),

            # Oceania
            discord.SelectOption(label="Australia/Sydney",    value="Australia/Sydney"),
            discord.SelectOption(label="Pacific/Auckland",    value="Pacific/Auckland"),
        ]
        super().__init__(
            placeholder='Select your timezone',
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        self.view.selected_timezone = self.values[0]
        await interaction.response.defer()

class QuickSetupView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)  # timeout after 2min
        self.selected_period   = None
        self.selected_channel  = None
        self.selected_timezone = None

        # Add the 3 dropdowns to the view
        self.add_item(PeriodSelect())
        self.add_item(ChannelSelect())
        self.add_item(TimezoneSelect())

    @discord.ui.button(label="Continue", style=discord.ButtonStyle.primary, row=4)
    async def continue_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check that all 3 dropdowns have been selected before opening the modal
        if not all([self.selected_period, self.selected_channel, self.selected_timezone]):
            await interaction.response.send_message(
                "Please select all three options before continuing.",
                ephemeral=True
            )
            return

        # Pass selections through modal
        modal = BudgetAmountModal(
            period=self.selected_period,
            channel_id=self.selected_channel,
            tz=self.selected_timezone
        )
        await interaction.response.send_modal(modal)

# discord.ui.Modal is Discord's built-in pop-up form system
class BudgetAmountModal(discord.ui.Modal,
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

    def __init__(self, 
                 period: str,
                 channel_id: str,
                 tz: str):
        super().__init__()
        self.period = period
        self.channel_id = channel_id
        self.tz = tz
    
    async def on_submit(self, 
                        interaction: discord.Interaction):
        # --- Validate budget amount ---
        amount = float(self.budget_amount.value)
        msg = validate_amount(amount)
        if msg:
            await interaction.response.send_message(
                msg,
                ephemeral=False
            )
            return
        
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild.id)

        await database.set_budget(user_id, amount, self.period)
        await database.set_summary_channel_for_budget(
            guild_id, 
            str(self.channel_id),
            user_id,
            self.period)
        await database.set_user_timezone(user_id, self.tz)

        # Confirm back to the user with a summary of what was set
        local_time = __import__('datetime').datetime.now(
            pytz.timezone(self.tz)
        ).strftime("%H:%M, %A %d %B %Y")

        await interaction.response.send_message(
            f"✅ **Wallet Tracker is all set up!**\n\n"
            f"💰 **Budget:** ${amount:.2f} per {self.period}\n"
            f"📢 **Summary channel:** <#{self.channel_id}>\n"
            f"🌏 **Timezone:** `{self.tz}` (your local time: {local_time})\n\n"
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
        
    @app_commands.command(name="start", description="Set up WalletTracker in one go")
    async def start(self, interaction: discord.Interaction):
        view = QuickSetupView()
        await interaction.response.send_message(
            "**WalletTracker Setup**\nSelect your preferences, then click Continue.\n‼️By selecting timezone, you will be overwriting your previously set timezone.",
            view=view,
            ephemeral=True
        )