import datetime
from io import BytesIO
from typing import Optional

import asyncpg
import disnake
from disnake.ext import commands

from assistant import Client, long_date


class Notes(commands.Cog):
    def __init__(self, client: Client):
        self.client = client
        self.conn: Optional[asyncpg.Connection] = None

    async def _connect_to_db(self):
        # connect to the database
        if self.conn is None:
            self.client.logger.info("Connecting to database...")
            self.conn = await asyncpg.connect(user="postgres", password="root")

    async def _add_note_to_db(self, tag: str, content: str,
                              user_id: int, guild_id: int,
                              attachments: list[disnake.Attachment]):
        await self._connect_to_db()
        if self.conn is None:
            self.client.logger.error("Could not connect to database.")
            return
        timestamp = int(datetime.datetime.now().timestamp())
        attachment_list = [await attachment.read() for attachment in attachments] if attachments else []
        attach_names = [attachment.filename for attachment in attachments] if attachments else []
        already_exists = await self.conn.fetch("SELECT * FROM notes WHERE tag = $1 AND guild_id = $2",
                                               tag.lower(), guild_id)
        if already_exists:
            await self.conn.execute(
                """
                UPDATE notes SET content = $1, created_on = $2, attachment = $3, attach_names = $4
                WHERE tag = $5 AND guild_id = $6""",
                content, timestamp, attachment_list, attach_names, tag.lower(), guild_id
            )
        else:
            await self.conn.execute(
                """
                INSERT INTO notes (tag, content, user_id, guild_id, created_on, attachment, attach_names)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                tag.lower(), content, user_id, guild_id, timestamp, attachment_list, attach_names
            )

    async def _get_notes_from_db(self, tag: str, guild_id: int):
        await self._connect_to_db()
        if self.conn is None:
            return None
        notes = await self.conn.fetch("SELECT * FROM notes WHERE tag = $1 AND guild_id = $2", tag.lower(), guild_id)
        return notes[0] if notes else None

    @commands.slash_command(description="Add notes for later reference.")
    async def add_note(self, inter: disnake.ApplicationCommandInteraction,
                       tag: str = commands.Param(description="The tag for the note."),
                       content: str = commands.Param(description="The content of the note."),
                       attachment: disnake.Attachment = commands.Param(description="Add Files", default=None)
                       ) -> None:
        """
        Add notes for later reference.
        """
        await inter.response.defer()
        await inter.edit_original_message(content="Note Added",
                                          embed=disnake.Embed(title=f"{tag.title()}", description=content, ),
                                          files=[await attachment.to_file()] if attachment else [])
        attach = [attachment] if attachment else []
        await self._add_note_to_db(tag, content, inter.user.id, inter.guild.id, attach)
        self.client.logger.info(f"{inter.user.display_name} added note {tag}")

    @commands.command(aliases=['add_note'])
    async def command_add_notes(self, ctx: commands.Context, *, tag: str) -> None:
        if ctx.message.reference is None:
            await ctx.send("You must use this command as a reply.")
            return
        msg = ctx.message.reference.resolved
        await self._add_note_to_db(tag, msg.content, msg.author.id, ctx.guild.id, msg.attachments)
        await msg.reply("Note Added")
        self.client.logger.info(f"{ctx.author.display_name} added note {tag}")

    @commands.command(aliases=['delete_note', 'del_note', 'remove_note'])
    @commands.has_permissions(manage_guild=True)
    async def commands_remove_notes(self, ctx: commands.Context, tag: str) -> None:
        # check if note exists
        if not await self._get_notes_from_db(tag, ctx.guild.id):
            await ctx.send("Note does not exist")
            return
        await self.conn.execute("DELETE FROM notes WHERE tag = $1 AND guild_id = $2", tag.lower(), ctx.guild.id)
        await ctx.send("Note Removed")
        self.client.logger.info(f"{ctx.author.display_name} removed note {tag}")

    @commands.slash_command(description="Fetch saved notes.")
    async def notes(self, inter: disnake.ApplicationCommandInteraction,
                    tag: str = commands.Param(description="Tag to search for")):
        """
        Fetch saved notes.
        """
        notes = await self._get_notes_from_db(tag, inter.guild.id)
        if not notes:
            await inter.response.send_message("No notes found.")
            return
        await inter.response.defer()
        attachments = notes["attachment"]
        names = notes["attach_names"]

        files = [disnake.File(BytesIO(attachment), filename=name)
                 for attachment, name in zip(attachments, names)] if attachments else []
        embed = disnake.Embed(title=f"{notes['tag'].title()}", description=notes['content'])
        embed.add_field(name="Author", value=f"<@{notes['user_id']}>")
        embed.add_field(name="Added on", value=long_date(notes['created_on']))
        await inter.edit_original_message(embed=embed, files=files)
        self.client.logger.info(f"{inter.user.display_name} fetched notes for {tag}")

    @notes.autocomplete('tag')
    async def notes_autocomplete(self, inter: disnake.ApplicationCommandInteraction,
                                 query: str) -> list[str]:
        """
        Autocomplete for tags.
        """
        await self._connect_to_db()
        if self.conn is None:
            return []
        records = await self.conn.fetch("SELECT tag FROM notes WHERE guild_id = $1", inter.guild.id)
        return [record['tag'] for record in records if query.lower() in record['tag']]


def setup(client):
    client.add_cog(Notes(client))
