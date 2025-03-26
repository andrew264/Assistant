import random
import re
from typing import List, Optional

import discord
import wavelink
from discord import app_commands
from discord.ext import commands

from assistant import AssistantBot
from config import DATABASE_NAME, LAVA_CONFIG
from models.playlist_models import PlaylistModel, Song
from utils import clickable_song
from utils.checks import check_vc_interaction
from utils.tracks import url_rx


class PlaylistCog(commands.Cog):
    def __init__(self, bot: AssistantBot):
        self.bot = bot

    async def get_voice_client(self, ctx: discord.Interaction) -> wavelink.Player:
        vc = ctx.guild.voice_client
        if not vc:
            self.bot.logger.debug("[MUSIC] Creating a new voice client.")
            vc = await ctx.user.voice.channel.connect(cls=wavelink.Player, self_deaf=True)
        return vc

    playlist_group = app_commands.Group(name="playlist", description="Manage your playlists.")

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
        await interaction.edit_original_response(content=f"An error occurred while executing this command.\n```py\n{error}\n```")
        self.bot.logger.error(f'Error in playlist command: {error}', exc_info=True)

    @playlist_group.command(name="create", description="Create a new playlist.")
    @app_commands.describe(name="The name of your new playlist.")
    @app_commands.guild_only()
    async def create_playlist(self, ctx: discord.Interaction, name: str):
        await ctx.response.defer()
        user_id = ctx.user.id
        guild_id = ctx.guild.id

        try:
            new_playlist = PlaylistModel(user_id=user_id, guild_id=guild_id, name=name)
        except Exception as e:
            self.bot.logger.error(f"[PLAYLIST] - Error creating playlist: {e}")
            return await ctx.edit_original_response(content=f'An unknown error occurred: {e}')

        collection = self.bot.database[DATABASE_NAME]['playlists']
        if await collection.count_documents({"user_id": user_id, "guild_id": guild_id, "name": name}) > 0:
            return await ctx.edit_original_response(content="You already have a playlist with that name.")
        if await collection.count_documents({"user_id": user_id, "guild_id": guild_id}) > 10:
            return await ctx.edit_original_response(content="Max playlists reached!")

        await collection.insert_one(new_playlist.model_dump())
        await ctx.edit_original_response(content=f"Playlist '{name}' created successfully!")

    @playlist_group.command(name="delete", description="Delete a playlist.")
    @app_commands.describe(name="The name of the playlist to delete.")
    @app_commands.guild_only()
    async def delete_playlist(self, ctx: discord.Interaction, name: str):
        await ctx.response.defer()
        user_id = ctx.user.id
        guild_id = ctx.guild.id

        collection = self.bot.database[DATABASE_NAME]['playlists']
        playlist = await collection.find_one({"user_id": user_id, "guild_id": guild_id, "name": name})
        if not playlist:
            return await ctx.edit_original_response(content="Playlist not found.")

        # Confirmation with buttons
        view = discord.ui.View()
        btn_yes = discord.ui.Button(label="Yes", style=discord.ButtonStyle.danger)
        btn_no = discord.ui.Button(label="No", style=discord.ButtonStyle.secondary)

        async def on_yes_click(interaction: discord.Interaction):
            await collection.delete_one({"_id": playlist["_id"]})
            await interaction.response.edit_message(content=f"Playlist '{name}' deleted.", view=None)
            view.stop()

        async def on_no_click(interaction: discord.Interaction):
            await interaction.response.edit_message(content="Playlist deletion cancelled.", view=None)
            view.stop()

        btn_yes.callback = on_yes_click
        btn_no.callback = on_no_click
        view.add_item(btn_yes)
        view.add_item(btn_no)

        await ctx.edit_original_response(content=f"Are you sure you want to delete playlist '{name}'?", view=view)

    @playlist_group.command(name="add", description="Add a song or an entire playlist to a playlist.")
    @app_commands.describe(playlist_name="The name of the playlist.", song_query="The song to add (or a playlist URL/query).")
    @app_commands.guild_only()
    @check_vc_interaction()
    async def add_to_playlist(self, ctx: discord.Interaction, playlist_name: str, song_query: Optional[str] = None):
        await ctx.response.defer()
        user_id = ctx.user.id
        guild_id = ctx.guild.id
        vc = await self.get_voice_client(ctx)
        collection = self.bot.database[DATABASE_NAME]['playlists']
        playlist = await collection.find_one({"user_id": user_id, "guild_id": guild_id, "name": playlist_name})
        if not playlist:
            return await ctx.edit_original_response(content="Playlist not found.")

        if len(playlist['songs']) >= 200:
            return await ctx.edit_original_response(content="This playlist is full!")

        # Determine which track(s) to add
        if song_query:
            if not re.match(url_rx, song_query):
                song_query = f"ytsearch:{song_query}"
            try:
                tracks = await wavelink.Pool.fetch_tracks(song_query)
                if not tracks:
                    return await ctx.edit_original_response(content="Could not find that song or playlist!")
            except Exception as e:
                self.bot.logger.error(f'Error fetching track(s): {e}', exc_info=True)
                return await ctx.edit_original_response(content=f"An error occurred: {e}")
        elif vc.current:
            tracks = [vc.current]
        else:
            return await ctx.edit_original_response(content="Please provide a song query or URL, or play a song to add the current song.")

        # Check if we got a playlist from wavelink
        if isinstance(tracks, wavelink.Playlist):
            new_songs = []
            for track in tracks.tracks:
                # Respect the 200 songs limit
                if len(playlist['songs']) + len(new_songs) >= 200:
                    break
                try:
                    song = Song(title=track.title, artist=track.author, uri=track.uri, duration=track.length, thumbnail=track.artwork,
                                source='youtube' if 'youtube' in track.uri else 'other')
                    new_songs.append(song.model_dump())
                except Exception as e:
                    self.bot.logger.error(f"Song data error: {e}")
                    continue
            if not new_songs:
                return await ctx.edit_original_response(content="No songs could be added (playlist might be full).")
            result = await collection.update_one({"_id": playlist["_id"]}, {"$push": {"songs": {"$each": new_songs}}, "$set": {"updated_at": discord.utils.utcnow()}})
            await ctx.edit_original_response(content=f"Added {len(new_songs)} songs from the playlist to '{playlist_name}'.")
        else:
            # Assume a single track (if a list is returned, take the first)
            track = tracks[0] if isinstance(tracks, list) else tracks
            try:
                new_song = Song(title=track.title, artist=track.author, uri=track.uri, duration=track.length, thumbnail=track.artwork,
                                source='youtube' if 'youtube' in track.uri else 'other')
            except Exception as e:
                self.bot.logger.error(f"Song data error: {e}")
                return await ctx.edit_original_response(content="Error processing song data.")

            result = await collection.update_one({"_id": playlist["_id"]}, {"$push": {"songs": new_song.model_dump()}, "$set": {"updated_at": discord.utils.utcnow()}})
            if result.modified_count:
                await ctx.edit_original_response(content=f"Added {clickable_song(track)} to playlist '{playlist_name}'.")
            else:
                await ctx.edit_original_response(content="An error occurred while adding the song.")

    @playlist_group.command(name="remove", description="Remove a song from a playlist.")
    @app_commands.describe(playlist_name="The name of the playlist.", index="The index of the song to remove.")
    @app_commands.guild_only()
    async def remove_from_playlist(self, ctx: discord.Interaction, playlist_name: str, index: int):
        await ctx.response.defer()
        user_id = ctx.user.id
        guild_id = ctx.guild.id
        collection = self.bot.database[DATABASE_NAME]['playlists']
        playlist = await collection.find_one({"user_id": user_id, "guild_id": guild_id, "name": playlist_name})
        if not playlist:
            return await ctx.edit_original_response(content="Playlist not found.")

        if not 1 <= index <= len(playlist["songs"]):
            return await ctx.edit_original_response(content="Invalid song index.")

        removed_song = playlist["songs"][index - 1]
        await collection.update_one({"_id": playlist["_id"]}, {"$pull": {"songs": removed_song}, "$set": {"updated_at": discord.utils.utcnow()}})
        await ctx.edit_original_response(content=f"Removed '{removed_song['title']}' from playlist '{playlist_name}'.")

    @playlist_group.command(name="list", description="Show your playlists")
    @app_commands.guild_only()
    async def list_playlists(self, ctx: discord.Interaction):
        await ctx.response.defer()
        user_id = ctx.user.id
        guild_id = ctx.guild.id
        collection = self.bot.database[DATABASE_NAME]['playlists']

        playlists = await collection.find({"user_id": user_id, "guild_id": guild_id}).to_list(length=None)
        if not playlists:
            return await ctx.edit_original_response(content="You don't have any playlists.")

        embed = discord.Embed(title=f"{ctx.user.display_name}'s Playlists", color=discord.Color.blue())
        description = ""
        for i, playlist in enumerate(playlists):
            description += f"{i + 1}. {playlist['name']} ({len(playlist['songs'])} songs)\n"
        embed.description = description
        await ctx.edit_original_response(embed=embed)

    @playlist_group.command(name="show", description="Show the contents of a playlist.")
    @app_commands.describe(playlist_name="The name of the playlist.", page_number="The page number to display.")
    @app_commands.guild_only()
    async def show_playlist(self, ctx: discord.Interaction, playlist_name: str, page_number: Optional[int] = 1):
        await ctx.response.defer()
        user_id = ctx.user.id
        guild_id = ctx.guild.id

        collection = self.bot.database[DATABASE_NAME]['playlists']
        playlist = await collection.find_one({"user_id": user_id, "guild_id": guild_id, "name": playlist_name})
        if not playlist:
            return await ctx.edit_original_response(content="Playlist not found.")

        songs = playlist["songs"]
        if not songs:
            return await ctx.edit_original_response(content="This playlist is empty")

        class PlaylistPages(discord.ui.View):
            def __init__(self, songs: List[dict], start_page: int = 1):
                super().__init__(timeout=180)
                self.songs = songs
                self.page_number = start_page
                self.per_page = 10
                self.total_pages = (len(songs) + self.per_page - 1) // self.per_page

            async def on_timeout(self) -> None:
                for item in self.children:
                    item.disabled = True
                await self.message.edit(view=self)
                self.stop()

            def page_embed(self, page_number: int) -> discord.Embed:
                start = (page_number - 1) * self.per_page
                end = start + self.per_page
                page_content = self.songs[start:end]
                embed = discord.Embed(title=f"Playlist: {playlist_name}", color=discord.Color.green())
                embed.description = ""
                for i, song in enumerate(page_content):
                    index = start + i + 1
                    embed.description += f"{index}. [{song['title']}]({song['uri']})\n"
                embed.set_footer(text=f"Page {page_number}/{self.total_pages} | Total Songs: {len(self.songs)}")
                return embed

            @discord.ui.button(emoji="◀", style=discord.ButtonStyle.secondary)
            async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
                if self.page_number > 1:
                    self.page_number -= 1
                else:
                    self.page_number = self.total_pages
                embed = self.page_embed(self.page_number)
                await interaction.response.edit_message(embed=embed, view=self)

            @discord.ui.button(emoji="▶", style=discord.ButtonStyle.secondary)
            async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
                if self.page_number < self.total_pages:
                    self.page_number += 1
                else:
                    self.page_number = 1
                embed = self.page_embed(self.page_number)
                await interaction.response.edit_message(embed=embed, view=self)

        view = PlaylistPages(songs, start_page=page_number)
        msg = await ctx.edit_original_response(embed=view.page_embed(view.page_number), view=view)
        view.message = msg

    @playlist_group.command(name="play", description="Play a playlist.")
    @app_commands.describe(playlist_name="The name of the playlist to play.")
    @app_commands.guild_only()
    @check_vc_interaction()
    async def play_playlist(self, ctx: discord.Interaction, playlist_name: str):
        await ctx.response.defer()
        user_id = ctx.user.id
        guild_id = ctx.guild.id
        vc = await self.get_voice_client(ctx)
        collection = self.bot.database[DATABASE_NAME]['playlists']
        playlist = await collection.find_one({"user_id": user_id, "guild_id": guild_id, "name": playlist_name})
        if not playlist:
            return await ctx.edit_original_response(content="Playlist not found.")
        if not playlist["songs"]:
            return await ctx.edit_original_response(content="This playlist is empty.")

        vc.queue.clear()
        for song_data in playlist["songs"]:
            try:
                track_res = await wavelink.Pool.fetch_tracks(song_data["uri"])
                # If a playlist or list is returned, take the first track.
                if isinstance(track_res, (list, wavelink.Playlist)):
                    track = track_res[0]
                else:
                    track = track_res

                if isinstance(track, wavelink.Playable):
                    vc.queue.put(track)
            except Exception as e:
                self.bot.logger.error(f"Failed to fetch track {song_data['uri']}: {e}")
                await ctx.edit_original_response(content=f"Skipping {song_data['title']} due to an error.")
                continue

        if not vc.current:
            await vc.play(vc.queue.get())

        await ctx.edit_original_response(content=f"Playing playlist '{playlist_name}'.")

    @playlist_group.command(name="rename", description="Rename a playlist.")
    @app_commands.describe(old_name='The old name of the playlist', new_name="The new name of the playlist")
    @app_commands.guild_only()
    async def rename_playlist(self, ctx: discord.Interaction, old_name: str, new_name: str):
        await ctx.response.defer()
        user_id = ctx.user.id
        guild_id = ctx.guild.id

        try:
            # Validate new name using Pydantic
            PlaylistModel(user_id=user_id, guild_id=guild_id, name=new_name)
        except Exception as e:
            return await ctx.edit_original_response(content=str(e))

        collection = self.bot.database[DATABASE_NAME]['playlists']
        if await collection.count_documents({"user_id": user_id, "guild_id": guild_id, "name": new_name}) > 0:
            return await ctx.edit_original_response(content="You already have a playlist with that name.")

        result = await collection.update_one({"user_id": user_id, "guild_id": guild_id, "name": old_name}, {"$set": {"name": new_name, "updated_at": discord.utils.utcnow()}})
        if result.modified_count:
            await ctx.edit_original_response(content=f"Renamed '{old_name}' to '{new_name}'.")
        else:
            await ctx.edit_original_response(content="Could not find a playlist with that name.")

    @playlist_group.command(name='shuffle', description='Shuffle the songs within a playlist')
    @app_commands.describe(playlist_name="The name of the playlist to shuffle.")
    @app_commands.guild_only()
    async def shuffle_playlist(self, ctx: discord.Interaction, playlist_name: str):
        await ctx.response.defer()
        user_id = ctx.user.id
        guild_id = ctx.guild.id
        collection = self.bot.database[DATABASE_NAME]['playlists']
        playlist = await collection.find_one({"user_id": user_id, "guild_id": guild_id, "name": playlist_name})
        if not playlist:
            return await ctx.edit_original_response(content="Playlist not found.")
        if not playlist["songs"]:
            return await ctx.edit_original_response(content="This playlist is empty.")

        random.shuffle(playlist["songs"])
        await collection.update_one({"_id": playlist["_id"]}, {"$set": {"songs": playlist["songs"], "updated_at": discord.utils.utcnow()}})
        await ctx.edit_original_response(content=f"Shuffled playlist '{playlist_name}'.")

    @playlist_group.command(name="share", description="Share one of your playlists with another user.")
    @app_commands.describe(playlist_name="The name of the playlist to share", user="The user to share the playlist with.")
    @app_commands.guild_only()
    async def share_playlist(self, ctx: discord.Interaction, playlist_name: str, user: discord.User):
        await ctx.response.defer(ephemeral=True)
        sender_id = ctx.user.id
        guild_id = ctx.guild.id
        collection = self.bot.database[DATABASE_NAME]['playlists']

        # Fetch the sender's playlist
        original = await collection.find_one({"user_id": sender_id, "guild_id": guild_id, "name": playlist_name})
        if not original:
            return await ctx.edit_original_response(content="Playlist not found.")

        # Check if the recipient already has a playlist with the same name
        if await collection.count_documents({"user_id": user.id, "guild_id": guild_id, "name": playlist_name}) > 0:
            return await ctx.edit_original_response(content=f"{user.mention} already has a playlist named '{playlist_name}'.")

        # Check recipient's total playlists (limit to 10)
        if await collection.count_documents({"user_id": user.id, "guild_id": guild_id}) >= 10:
            return await ctx.edit_original_response(content=f"{user.mention} has reached the maximum number of playlists.")

        # Prepare a copy of the playlist for sharing. We update user_id and timestamps.
        shared_playlist = original.copy()
        shared_playlist["_id"] = None  # Remove the original document ID
        shared_playlist["user_id"] = user.id
        shared_playlist["created_at"] = discord.utils.utcnow()
        shared_playlist["updated_at"] = discord.utils.utcnow()

        result = await collection.insert_one(shared_playlist)
        if result.inserted_id:
            await ctx.edit_original_response(content=f"Playlist '{playlist_name}' has been shared with {user.mention}.")
        else:
            await ctx.edit_original_response(content="An error occurred while sharing the playlist.")

    # -------------------- Autocomplete --------------------
    @create_playlist.autocomplete('name')
    @delete_playlist.autocomplete('name')
    @add_to_playlist.autocomplete('playlist_name')
    @remove_from_playlist.autocomplete('playlist_name')
    @show_playlist.autocomplete('playlist_name')
    @play_playlist.autocomplete('playlist_name')
    @rename_playlist.autocomplete('old_name')
    @shuffle_playlist.autocomplete('playlist_name')
    async def playlist_autocomplete(self, ctx: discord.Interaction, current: str):
        assert ctx.guild_id is not None
        collection = self.bot.database[DATABASE_NAME]['playlists']
        cursor = collection.find({"user_id": ctx.user.id, "guild_id": ctx.guild_id}, projection={"name": 1, "_id": 0})
        playlists = await cursor.to_list(length=25)
        return [app_commands.Choice(name=playlist['name'], value=playlist['name']) for playlist in playlists if current.lower() in playlist['name'].lower()]


async def setup(bot: AssistantBot):
    if LAVA_CONFIG:
        await bot.add_cog(PlaylistCog(bot))
