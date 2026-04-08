import discord
from discord import app_commands
import database

DELETE_VIEW_TIMEOUT = 30 # time out after 30 seconds

class DeleteConfirmView(discord.ui.View):
    """Two-button confirmation view for deleting an entry.
    Times out after 30 seconds if user doesn't respond.

    Args:
        discord (_type_): _description_
    """
    def __init__(self, *, entry_id: int, user_id: str, guild_id: str):
        super().__init__(timeout=DELETE_VIEW_TIMEOUT)
        self.entry_id = entry_id
        self.user_id  = user_id
        self.guild_id = guild_id

    async def interaction_check(self, 
                                interaction: discord.Interaction
                                ) -> bool:
        """Makes sure only the user who ran the command can press the buttons.
        If someone else tries to click, they get a silent rejection.
        """
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message(
                "❌ These buttons aren't for you.",
                ephemeral=False
            )
            return False
        return True
    
    # Delete button
    @discord.ui.button(label="yes wipe it off",
                       style=discord.ButtonStyle.danger)
    async def confirm(self,
                      interaction: discord.Interaction,
                      button: discord.ui.Button):
        try:
            deleted = await database.delete_entry(
                entry_id=self.entry_id,
                user_id=self.user_id,
                guild_id=self.guild_id
            )

            for item in self.children:
                item.disabled = True
                
            if deleted:
                await interaction.response.edit_message(
                    content="✅ Entry deleted successfully.",
                    embed=None,
                    view=self
                )
            else:
                await interaction.response.edit_message(
                    content="❌ Entry could not be found. It may have already been deleted.",
                    embed=None,
                    view=self
                )

            self.stop()

        except Exception as e:
            import traceback
            traceback.print_exc()

    # Cancel button
    @discord.ui.button(label="WAIT i changed my mind",
                       style=discord.ButtonStyle.secondary)
    async def cancel(self,
                     interaction: discord.Interaction,
                     button: discord.ui.Button):
        # Disable all buttons after clicking
        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(
            content="Cancelled. Entry was not deleted.",
            embed=None,
            view=self
        )
        self.stop()

    async def on_timeout(self):
        """Fires if the user doesn't click anything within 30 seconds.
        Disables the buttons so they can't be clicked after the timeout.
        """
        for item in self.children:
            item.disabled = True
        # We can't send a new message on timeout since we don't have an
        # interaction object here, but disabling the buttons makes it
        # clear the window has expired.

# app_commands.Group is discord.py's way of creating a group of related slash commands 
# that share a prefix. This means the command will be '/log spend' 
# rather than just '/log'
class LogCommands(app_commands.Group):
    """ Group of commands related to logging spending.

    Args:
        app_commands (_type_): _description_
    """

    def __init__(self):
        super().__init__(name="log",
                         description="Log a spending entry")
    
    # '/log spend' as a whole command
    @app_commands.command(name="spend",
                          description="Log a new spending entry")
    @app_commands.describe(
        amount="How much you spent (e.g. 12.50)",
        category="What you spent it on (e.g. coffee, transport, groceries)",
        note="Optional extra detail (e.g. 'spent at Aldi')"
    )
    # show a dropdown menu for the period argument
    @app_commands.choices(category=[
        app_commands.Choice(name="Eat out & Takeaway",   value="Eat out & Takeaway"),
        app_commands.Choice(name="Entertainment",  value="Entertainment"),
        app_commands.Choice(name="Grocery",  value="Grocery"),
        app_commands.Choice(name="Snack",  value="Snack"),
        app_commands.Choice(name="Utils & Bills",  value="Utils & Bills"),
        app_commands.Choice(name="Other",  value="Other"),
    ])
    async def spend(
        self,
        interaction: discord.Interaction,
        amount: float,
        category: app_commands.Choice[str],
        note: str = None
    ):
        # Basic validation — amount must be positive
        if amount <= 0:
            await interaction.response.send_message(
                "❌ Amount must be greater than zero.",
                ephemeral=False
            )
            return
        
        # Write to databse
        await database.add_entry(
            user_id=str(interaction.user.id),
            guild_id=str(interaction.guild.id),
            amount=amount,
            category=category.value, # category is a Choice object, .value gives us the string
            note=note
        )

        # Build a confirmation message
        note_line = f"\n📝 Note: {note}" if note else ""
        await interaction.response.send_message(
            f"✅ Logged **${amount:.2f}** for **{category.name}**{note_line}",
            ephemeral=False
        )

    # '/log list' command to get a list of recent entries
    @app_commands.command(name="list",
                          description="Show your recent spending entries")
    @app_commands.describe(limit="How many entries to show (default 10, max 25)")
    async def list_entries(self,
                           interaction: discord.Interaction,
                           limit: int = database.RECENT_ENTRY_EDIT_LIMIT):
        
        # Cap the limit so no one requests 1000 entries (or the entire databse)
        if limit < 1 or limit > database.HARD_ENTRY_EDIT_LIMIT:
            await interaction.response.send_message(
                "❌ Limit must be between 1 and 25.",
                ephemeral=False
            )
            return
        
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild.id)

        entries = await database.get_recent_entries(user_id, guild_id, limit)
        if not entries:
            await interaction.response.send_message(
                "You have no logged entries yet. Use `/log spend` to add one.",
                ephemeral=False
            )
            return
        
        # Build an embed with one line per entry
        embed = discord.Embed(
            title="Recent Entries",
            description=f"Your last {len(entries)} spending entries.",
            colour=discord.Colour.blurple()
        )

        lines = []
        for entry_id, amount, category, note, timestamp, in entries:
            # Trim timestamp to just the date and time, drop seconds
            ts = timestamp[:16]
            note_part = f" — {note}" if note else ""
            lines.append(f"`ID: {entry_id}` **${amount:.2f}** · {category}{note_part} · {ts}")

        embed.add_field(name="Entries", value="\n".join(lines), inline=False)
        embed.set_footer(text="Use /log edit or /log delete with the entry ID to modify an entry.")

        await interaction.response.send_message(embed=embed, ephemeral=False)

    # '/log edit' to edit an entry based on entry_id
    @app_commands.command(name="edit",
                          description="Edit a previously logged spending entry")
    @app_commands.describe(
        entry_id="The ID of the entry to edit (use /log list to find it)",
        amount="New amount (leave blank to keep current)",
        category="New category (leave blank to keep current)",
        note="New note (leave blank to keep current)"
    )
    async def edit(
        self,
        interaction: discord.Interaction,
        entry_id: int,
        amount: float = None,
        category: str = None,
        note: str = None
    ):
        # Make sure the user provided at least one field to change
        if amount is None and category is None and note is None:
            await interaction.response.send_message(
                "❌ Please provide at least one field to update "
                "(amount, category, or note).",
                ephemeral=False
            )
            return
        
        if amount is not None and amount <= 0:
            await interaction.response.send_message(
                "❌ Amount must be greater than zero.",
                ephemeral=False
            )
            return
        
        user_id  = str(interaction.user.id)
        guild_id = str(interaction.guild.id)

        updated = await database.edit_entry(
            entry_id=entry_id,
            user_id=user_id,
            guild_id=guild_id,
            amount=amount,
            category=category,
            note=note
        )

        if not updated:
            await interaction.response.send_message(
                f"❌ No entry found with ID `#{entry_id}`. "
                f"Use `/log list` to see your entries and their IDs.",
                ephemeral=False
            )
            return
        
        # Build a confirmation showing what changed
        changes = []
        if amount is not None:
            changes.append(f"Amount → **${amount:.2f}**")
        if category is not None:
            changes.append(f"Category → **{category}**")
        if note is not None:
            changes.append(f"Note → **{note}**")

        await interaction.response.send_message(
            f"✅ Entry `#{entry_id}` updated:\n" + "\n".join(changes),
            ephemeral=False
        )

    # '/log delete' command to delete an entry
    @app_commands.command(name="delete",
                          description="Delete a logged spending entry")
    @app_commands.describe(
        entry_id="The ID of the entry to delete (use /log list to find it)"
    )
    async def delete(
        self,
        interaction: discord.Interaction,
        entry_id: int
    ):
        user_id  = str(interaction.user.id)
        guild_id = str(interaction.guild.id)

        # Fetch the entry first so we can show it in the confirmation
        entry = await database.get_entry_by_id(entry_id, user_id, guild_id)

        if entry is None:
            await interaction.response.send_message(
                f"❌ No entry found with ID `#{entry_id}`. "
                f"Use `/log list` to see your entries and their IDs.",
                ephemeral=False
            )
            return
        
        # Unpack entry details
        _, amount, category, note, timestamp = entry
        ts = timestamp[:16]
        note_part = f" - {note}" if note else ""

        # Build a confirmation embed showing what's about to be deleted
        embed = discord.Embed(
            title="🗑️ Confirm Deletion",
            description="Are you sure you want to delete this entry? This cannot be undone.",
            colour=discord.Colour.orange()
        )
        embed.add_field(
            name="Entry to delete",
            value=f"`ID: {entry_id}` **${amount:.2f}** · {category}{note_part} · {ts}",
            inline=False
        )

        view = DeleteConfirmView(
            entry_id=entry_id,
            user_id=user_id,
            guild_id=guild_id
        )

        await interaction.response.send_message(
            embed=embed,
            view=view,
            ephemeral=False
        )