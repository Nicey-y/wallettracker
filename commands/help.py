import discord
from discord import app_commands


class HelpCommands(app_commands.Group):

    def __init__(self):
        super().__init__(name="help", description="Get started with Wallet Tracker")

    @app_commands.command(name="show", description="Show all available commands")
    async def show(self, interaction: discord.Interaction):

        embed = discord.Embed(
            title="⸜(｡˃ ᵕ ˂ )⸝♡ Wallet Tracker - Command Reference",
            description="Here's everything you can do with Wallet Tracker.",
            colour=discord.Colour.blurple()
        )

        embed.set_author(
            name="🖊️ See full documentation here!!!",
            url="https://dent-apple-062.notion.site/wallet-tracker-documentation-33cec5b29929801d81dcf5b5bf6b71e4?source=copy_link"
        )

        embed.add_field(
            name="🚀 Getting Started",
            value=(
                "`/quicksetup start`: Set up your budget, summary channel, and timezone in one go\n"
            ),
            inline=False
        )

        embed.add_field(
            name="💸 Logging Spending",
            value=(
                "`/log spend`: Log a new spending entry\n"
                "`/log list`: View your recent entries with their IDs\n"
                "`/log edit`: Edit an existing entry by ID\n"
                "`/log delete`: Delete an entry by ID (with confirmation)\n"
            ),
            inline=False
        )

        embed.add_field(
            name="💰 Budget",
            value=(
                "`/budget set`: Set your budget amount and period\n"
                "`/budget setchannel`: Set the channel for automatic summaries\n"
            ),
            inline=False
        )

        embed.add_field(
            name="📊 Summary",
            value=(
                "`/summary show`: View your spending summary for the current period\n"
                "`/summary settimezone`: Set your local timezone for scheduled summaries\n"
            ),
            inline=False
        )

        embed.add_field(
            name="🕐 Automatic Summaries",
            value=(
                "Wallet Tracker automatically posts a summary at **8pm your local time** "
                "at the end of each budget period:\n"
                "— **Daily** budget → every evening\n"
                "— **Weekly** budget → every Sunday\n"
                "— **Monthly** budget → last day of the month\n"
            ),
            inline=False
        )

        embed.set_footer(text="Wallet Tracker · Use /quicksetup start to get started")

        await interaction.response.send_message(embed=embed, ephemeral=False)