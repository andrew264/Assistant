import datetime
from typing import Optional

import asyncpg
import disnake
from disnake.ext import commands

from EnvVariables import HOMIES
from assistant import Client


class Notes(commands.Cog):
    def __init__(self, client: Client):
        self.client = client
        self.conn = None

    async def _connect_to_db(self):
        # connect to the database
        if self.conn is None:
            self.conn = await asyncpg.connect(user="postgres", password="root")

    async def _add_note_to_db(self, tag: str, content: str,
                              user_id: int, guild_id: int,
                              attachments: Optional[list[disnake.Attachment]] = None):
        await self._connect_to_db()
        if self.conn is None:
            print("Could not connect to database.")
            return
        timestamp = int(datetime.datetime.now().timestamp())
        attachment_list = [await attachment.read() for attachment in attachments] if attachments else []
        already_exists = await self.conn.fetch("SELECT * FROM notes WHERE tag = $1", tag.lower())
        if already_exists:
            await self.conn.execute(
                "UPDATE notes SET content = $1, attachment = $2, created_on = $3 WHERE tag = $4",
                content, attachment_list, timestamp, tag.lower())
        else:
            await self.conn.execute(
                """
                INSERT INTO notes (tag, content, user_id, guild_id, created_on, attachment)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                tag.lower(), content, user_id, guild_id, timestamp, attachment_list
            )

    async def _get_notes_from_db(self, tag: str, guild_id: int):
        await self._connect_to_db()
        if self.conn is None:
            return None
        notes = await self.conn.fetch("""
            SELECT * FROM notes
            WHERE tag = $1 AND guild_id = $2
            """, tag.lower(), guild_id)
        return notes[0] if notes else None

    @commands.slash_command(description="Add notes for later reference.", guild_ids=[HOMIES])
    async def add_note(self, inter: disnake.ApplicationCommandInteraction,
                       tag: str, content: str,
                       attachment: disnake.Attachment = commands.Param(description="Add Files", default=None)
                       ) -> None:
        """
        Add notes for later reference.
        """
        await inter.response.send_message("Note Added",
                                          embed=disnake.Embed(
                                              title=f"{tag.title()}",
                                              description=content, ),
                                          files=[await attachment.to_file()] if attachment else [])
        attach = [attachment] if attachment else None
        await self._add_note_to_db(tag, content, inter.user.id, inter.guild.id, attach)

    @commands.slash_command(description="Fetch saved notes.", guild_ids=[HOMIES])
    async def notes(self, inter: disnake.ApplicationCommandInteraction,
                    tag: str = commands.Param(description="Tag to search for")):
        """
        Fetch saved notes.
        """
        notes = await self._get_notes_from_db(tag, inter.guild.id)
        if not notes:
            await inter.response.send_message("No notes found.")
            return
        # attachments: list[bytes] = notes["attachment"]
        # files = [disnake.File(bytes(attachment)) for attachment in attachments]
        await inter.response.send_message(
            embed=disnake.Embed(
                title=f"{notes['tag'].title()}",
                description=notes["content"],
            ),
            # files=files if files else None
        )

    @notes.autocomplete('tag')
    async def notes_autocomplete(self, inter: disnake.ApplicationCommandInteraction,
                                 query: str) -> list[str]:
        """
        Autocomplete for tags.
        """
        await self._connect_to_db()
        if self.conn is None:
            return []
        records = await self.conn.fetch(
            "SELECT tag FROM notes WHERE guild_id = $1", inter.guild.id)
        return [record['tag'] for record in records if query.lower() in record['tag']]


def setup(client):
    client.add_cog(Notes(client))
