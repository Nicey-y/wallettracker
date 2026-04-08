import discord
from discord import app_commands
from datetime import datetime, timedelta, timezone
import database
import pytz

def get_period_start(budget_period: str) -> str:
    """ Work out the datetime when the current budget period started.

    Args:
        budget_period (str): _description_

    Returns:
        str: a string that SQLite can compare against.
        For example, if today is Wednesday and the period is 'weekly',
        this returns last Monday's date at midnight.
    """

    now = datetime.now(timezone.utc)

    if budget_period == 'daily':
        # Start of today
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    elif budget_period == 'weekly':
        # Monday of the current week
        days_since_monday = now.weekday() # Monday = 0, Sunday = 6
        start = (now - timedelta(days=days_since_monday)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
    
    elif budget_period == 'monthly':
        # First day of the current month
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    else: 
        # Fallback to start of today if period is unrecognised
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    return start.strftime("%Y-%m-%d %H:%M:%S")

class SummaryCommands(app_commands.Group):
    """ Group of commands related to spending summaries.

    Args:
        app_commands (_type_): _description_
    """

    def __init__(self):
        super().__init__(name="summary",
                         description="View your spending summary")
    
    @app_commands.command(name="show",
                          description="Show your spending summary for the current period.")
    async def show(self, interaction: discord.Interaction):

        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild.id)

        # Fetch user's budget
        budget_row = await database.get_budget(user_id, guild_id)

        if budget_row is None:
            await interaction.response.send_message(
                "❌ You haven't set a budget yet. Run `/budget set` first.",
                ephemeral=True
            )
            return
        
        budget_amount, budget_period = budget_row

        # Work out when the current period started
        period_start = get_period_start(budget_period)

        # Fetch all entries since the beginning of the period
        entries = await database.get_entries(user_id, guild_id, period_start)

        # Add up total spent
        total_spent = sum(row[0] for row in entries)
        # row[0] is the amount column — the first column in our SELECT

        remaining   = budget_amount - total_spent
        over_budget = total_spent > budget_amount

        # Build a breakdown by category
        category_totals = {}
        for row in entries:
            amount, category, note, timestamp = row
            category = category or "uncategorised"
            category_totals[category] = category_totals.get(category, 0) + amount
        
        # --- Build the response embed ---
        # Embeds are Discord's way of sending richly formatted messages with
        # colours, fields, and footers — much nicer than plain text.
        colour = discord.Colour.red() if over_budget else discord.Colour.green()

        embed = discord.Embed(
            title=f"📊 Wallet Tracker Summary",
            description=f"**{budget_period.capitalize()}** budget period · since {period_start[:10]}",
            colour=colour
        )

        embed.add_field(
            name="💰 Budget",
            value=f"${budget_amount:.2f}",
            inline=True
        )
        embed.add_field(
            name="💸 Spent",
            value=f"${total_spent:.2f}",
            inline=True
        )

        if over_budget:
            embed.add_field(
                name="🔴 Over budget by",
                value=f"${abs(remaining):.2f}",
                inline=True
            )
        else:
            embed.add_field(
                name="🟢 Remaining",
                value=f"${remaining:.2f}",
                inline=True
            )
        
        # Category breakdown
        if category_totals:
            breakdown_lines = []
            for cat, total in sorted(category_totals.items(), key=lambda x: x[1], reverse=True):
                pct = (total / budget_amount) * 100
                breakdown_lines.append(f"`{cat}` — ${total:.2f} ({pct:.0f}%)")
            embed.add_field(
                name="📂 By Category",
                value="\n".join(breakdown_lines),
                inline=False
            )
        else:
            embed.add_field(
                name="📂 By Category",
                value="No entries yet this period.",
                inline=False
            )

        # embed is a structured card with a coloured sidebar, fields, and a footer. 
        # The colour is green if you're under budget and red if you're over
        embed.set_footer(text=f"Wallet Tracker · {len(entries)} entries this period")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="settimezone",
                          description="Set your local timezone for scheduled summaries")
    @app_commands.describe(tz="Your timezone e.g. Australia/Melbourne, Europe/London, America/New_York")
    async def set_timezone(self,
                          interaction: discord.Interaction,
                          tz: str):
        # Validate that the timezone string is real
        if tz not in pytz.all_timezones:
            await interaction.response.send_message(
                f"❌ `{tz}` is not a valid timezone.\n"
                f"Use the format `Region/City` e.g. `Australia/Melbourne`, `Europe/London`, `America/New_York`.\n"
                f"Full list: <https://en.wikipedia.org/wiki/List_of_tz_database_time_zones>",
                ephemeral=True
            )
            return
        
        await database.set_user_timezone(str(interaction.user.id), tz)

        # Show the user their current local time as confirmation
        local_time = datetime.now(pytz.timezone(tz)).strftime("%H:%M, %A %d %B %Y")

        await interaction.response.send_message(
            f"✅ Timezone set to `{tz}`.\n"
            f"Your current local time is **{local_time}**.",
            ephemeral=True
        )