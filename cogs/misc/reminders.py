import datetime
import uuid
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands, tasks
from pydantic import BaseModel, Field, field_validator
from dateparser import parse
from dateutil.relativedelta import relativedelta

from assistant import AssistantBot
from config import DATABASE_NAME, MONGO_URI


def get_time_string(trigger_time: datetime.datetime, now: datetime.datetime) -> str:
    """Formats the time until a reminder triggers into a human-readable string."""
    delta = trigger_time - now
    if delta.total_seconds() < 60:
        return "in less than a minute"
    elif delta.total_seconds() < 3600:
        return f"in {int(delta.total_seconds() / 60)} minutes"
    elif delta.total_seconds() < 86400:
        return f"in {int(delta.total_seconds() / 3600)} hours"
    else:
        return f"in {int(delta.total_seconds() / 86400)} days"


class Reminder(BaseModel):
    user_id: int
    target_user_id: Optional[int] = None
    channel_id: int
    guild_id: int
    message: str
    trigger_time: datetime.datetime
    creation_time: datetime.datetime
    reminder_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    is_dm: bool = True
    title: Optional[str] = None
    recurrence: Optional[str] = None  # "daily", "weekly", "monthly", None
    last_triggered: Optional[datetime.datetime] = None
    is_active: bool = True  # For pausing/activating reminders

    @field_validator("trigger_time", "creation_time", mode="before")
    def ensure_utc(self, v: datetime.datetime) -> datetime.datetime:
        if v.tzinfo is None:  # Assume naive times are in UTC
            return v.replace(tzinfo=datetime.timezone.utc)
        return v.astimezone(datetime.timezone.utc)


class Reminders(commands.Cog):
    def __init__(self, bot: AssistantBot):
        self.bot = bot
        self.check_reminders.start()

    def cog_unload(self):
        self.check_reminders.cancel()

    @tasks.loop(seconds=60)  # Check every 60 seconds.
    async def check_reminders(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        db = self.bot.database[DATABASE_NAME]
        collection = db["reminders"]

        # Find reminders to trigger
        async for reminder_doc in collection.find({"trigger_time": {"$lte": now}, "is_active": True}):
            reminder = Reminder(**reminder_doc)
            try:
                if reminder.is_dm:
                    user = self.bot.get_user(reminder.target_user_id or reminder.user_id)
                    if user:
                        embed = discord.Embed(title=reminder.title or "Reminder", description=reminder.message, color=discord.Color.blue())
                        embed.add_field(name="Reminder Set At", value=f"<t:{int(reminder.creation_time.timestamp())}:f>", inline=False)
                        await user.send(embed=embed)
                    else:
                        self.bot.logger.warning(f"Could not find user {reminder.target_user_id or reminder.user_id} for reminder {reminder.reminder_id}")

                else:
                    channel = self.bot.get_channel(reminder.channel_id)
                    if channel:
                        embed = discord.Embed(title=reminder.title or "Reminder", description=reminder.message, color=discord.Color.blue())
                        embed.add_field(name="Reminder Set At", value=f"<t:{int(reminder.creation_time.timestamp())}:f>", inline=False)
                        await channel.send(f"<@{reminder.target_user_id or reminder.user_id}>", embed=embed)

            except discord.Forbidden:
                channel = self.bot.get_channel(reminder.channel_id)
                if channel:
                    await channel.send(f"Hey <@{reminder.user_id}>, I couldn't DM you! Here's your reminder:\n"
                                       f"> {reminder.message}")
            except Exception as e:
                self.bot.logger.error(f"Error sending reminder: {e}", exc_info=True)
            finally:
                if reminder.recurrence is None:
                    # Delete one-time reminders.
                    await collection.delete_one({"reminder_id": reminder.reminder_id})
                else:
                    # Update recurring reminders.
                    reminder.last_triggered = now
                    reminder.trigger_time = self.calculate_next_trigger_time(reminder)
                    await collection.update_one({"reminder_id": reminder.reminder_id}, {"$set": reminder.model_dump()})

    def calculate_next_trigger_time(self, reminder: Reminder) -> datetime.datetime:
        """Calculates the next trigger time based on recurrence."""
        if reminder.last_triggered is None:  # Should not happen, but handle for safety
            return reminder.trigger_time

        last_triggered = reminder.last_triggered
        recurrence = reminder.recurrence

        if recurrence == "daily":
            return last_triggered + datetime.timedelta(days=1)
        elif recurrence == "weekly":
            return last_triggered + datetime.timedelta(weeks=1)
        elif recurrence == "monthly":
            return last_triggered + relativedelta(months=1)  # Use relativedelta for months
        elif recurrence == "yearly":
            return last_triggered + relativedelta(years=1)
        elif recurrence == "hourly":
            return last_triggered + datetime.timedelta(hours=1)
        elif recurrence == "minutely":
            return last_triggered + datetime.timedelta(minutes=1)
        elif recurrence and recurrence.startswith("every"):  # "every 2 days"
            parts = recurrence.split()
            try:
                count = int(parts[1])
                unit = parts[2]
                if unit.startswith("day"):
                    return last_triggered + datetime.timedelta(days=count)
                elif unit.startswith("week"):
                    return last_triggered + datetime.timedelta(weeks=count)
                elif unit.startswith("month"):
                    return last_triggered + relativedelta(months=count)
                elif unit.startswith("year"):
                    return last_triggered + relativedelta(years=count)
                elif unit.startswith("hour"):
                    return last_triggered + datetime.timedelta(hours=count)
                elif unit.startswith("minute"):
                    return last_triggered + datetime.timedelta(minutes=count)
                else:
                    self.bot.logger.error(f"Invalid recurrence unit: {unit}")  # error logging.
                    return last_triggered + datetime.timedelta(days=1)  # default
            except ValueError:
                self.bot.logger.error(f"Invalid recurrence format: {recurrence}")
                return last_triggered + datetime.timedelta(days=1)

        else:
            #  Shouldn't reach here, but handle for safety.
            return last_triggered + datetime.timedelta(days=1)

    @check_reminders.before_loop
    async def before_check_reminders(self):
        await self.bot.wait_until_ready()

    @commands.hybrid_group(name="remind", invoke_without_command=True, aliases=["reminder"])
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def remind(self, ctx: commands.Context, time: str, *, message: str):
        await self._create_reminder(ctx, time, message=message)

    @remind.command(name="me")
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def remind_me(self, ctx: commands.Context, time: str, *, message: str):
        """Sets a reminder.  Time can be relative (e.g., 'in 5 minutes') or absolute (e.g., 'at 3:30 PM')."""
        await self._create_reminder(ctx, time, message=message)

    @remind.command(name="channel", aliases=["here"])
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def remind_channel(self, ctx: commands.Context, time: str, *, message: str):
        await self._create_reminder(ctx, time, message=message, is_dm=False)

    @remind.command(name="someone", aliases=["other"])
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)  # Require "Manage Messages"
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def remind_other(self, ctx: commands.Context, member: discord.Member, time: str, *, message: str):
        if member.bot:
            await ctx.reply('Oh no! Please do not do that!')
            return
        await self._create_reminder(ctx, time, message=message, target_user=member)

    async def _create_reminder(self, ctx: commands.Context, time_str: str, message: str, is_dm: bool = True, target_user: Optional[discord.User | discord.Member] = None,
                               recurrence: Optional[str] = None, title: Optional[str] = None):
        parsed_time = parse(time_str, settings={'PREFER_DATES_FROM': 'future', 'RETURN_AS_TIMEZONE_AWARE': True, 'DEFAULT_LANGUAGES': ["en"]})

        if parsed_time is None:
            await ctx.send("Invalid time format. Please use a recognizable format (e.g., 'in 5 minutes', 'at 2:30 PM').")
            return

        if parsed_time.tzinfo is None:
            parsed_time = parsed_time.replace(tzinfo=datetime.timezone.utc)

        now = datetime.datetime.now(datetime.timezone.utc)
        if parsed_time <= now:
            await ctx.send("Reminder time must be in the future.")
            return

        if len(message) > 2000:
            await ctx.send("Reminder message is too long (max 2000 characters).")
            return

        if recurrence and recurrence not in ("daily", "weekly", "monthly", "yearly", "hourly", "minutely") and not recurrence.startswith("every"):
            await ctx.send("Invalid recurrence interval.")
            return

        reminder = Reminder(user_id=ctx.author.id, target_user_id=(target_user.id if target_user else ctx.author.id), channel_id=ctx.channel.id, guild_id=ctx.guild.id,
                            message=message, trigger_time=parsed_time, creation_time=now, is_dm=is_dm, recurrence=recurrence, title=title)
        db = self.bot.database[DATABASE_NAME]
        collection = db["reminders"]
        await collection.insert_one(reminder.model_dump())
        await ctx.send(f"Okay, I'll remind {'you' if reminder.is_dm else 'here'} {get_time_string(reminder.trigger_time, now)}: {reminder.message}", suppress_embeds=True)

    @remind.command(name="list")
    @commands.guild_only()
    async def list_reminders(self, ctx: commands.Context):
        """Lists your pending reminders."""
        db = self.bot.database[DATABASE_NAME]
        collection = db["reminders"]

        reminders = []
        async for doc in collection.find({"user_id": ctx.author.id, "trigger_time": {"$gt": datetime.datetime.now(datetime.timezone.utc)}, "is_active": True}):
            reminders.append(Reminder(**doc))

        if not reminders:
            await ctx.send("You have no pending reminders.")
            return

        embed = discord.Embed(title="Your Pending Reminders")
        for reminder in reminders:
            recurrence_str = f" (Repeats {reminder.recurrence})" if reminder.recurrence else ""
            embed.add_field(name=f"ID: {reminder.reminder_id}{reminder.title if reminder.title else ''}",
                            value=f"Time: <t:{int(reminder.trigger_time.timestamp())}:f>{recurrence_str}\nMessage: {reminder.message[:100]}...",  # Truncate message
                            inline=False)
        await ctx.send(embed=embed)

    @remind.command(name="cancel")
    @commands.guild_only()
    @app_commands.describe(reminder_id="The ID of the reminder to cancel (use /remind list to get IDs).",
                           delete="Permanently delete the reminder (True) or just deactivate it (False).")
    async def cancel_reminder(self, ctx: commands.Context, reminder_id: str, delete: Optional[bool] = False):
        """Cancels a reminder by its ID."""
        db = self.bot.database[DATABASE_NAME]
        collection = db["reminders"]

        if delete:
            result = await collection.delete_one({"user_id": ctx.author.id, "reminder_id": reminder_id})
            if result.deleted_count == 0:
                await ctx.send("Could not find a reminder with that ID, or it doesn't belong to you.")
            else:
                await ctx.send("Reminder deleted.")
        else:
            result = await collection.update_one({"user_id": ctx.author.id, "reminder_id": reminder_id}, {"$set": {"is_active": False}})
            if result.modified_count == 0:
                await ctx.send("Could not find a reminder with that ID, or it doesn't belong to you.")
            else:
                await ctx.send("Reminder deactivated.  Use `/remind cancel <id> --delete` to delete it permanently.")

    @remind.command(name="edit")
    @commands.guild_only()
    @app_commands.describe(reminder_id="The ID of the reminder to edit.", new_message="The new message for the reminder.", new_time="The new time for the reminder.",
                           new_recurrence="The new recurrence interval (e.g., daily, weekly).", new_title="The title of the reminder")
    async def edit_reminder(self, ctx: commands.Context, reminder_id: str, new_message: Optional[str] = None, new_time: Optional[str] = None, new_recurrence: Optional[str] = None,
                            new_title: Optional[str] = None):
        """Edits an existing reminder."""
        db = self.bot.database[DATABASE_NAME]
        collection = db["reminders"]

        reminder_doc = await collection.find_one({"user_id": ctx.author.id, "reminder_id": reminder_id, "is_active": True})
        if not reminder_doc:
            await ctx.send("Could not find an active reminder with that ID, or it doesn't belong to you.")
            return

        reminder = Reminder(**reminder_doc)
        update_data = {}

        if new_message:
            if len(new_message) > 2000:
                await ctx.send("Reminder message is too long (max 2000 characters).")
                return
            update_data["message"] = new_message

        if new_time:
            parsed_time = parse(new_time, settings={'PREFER_DATES_FROM': 'future', 'RETURN_AS_TIMEZONE_AWARE': True})
            if parsed_time is None:
                await ctx.send("Invalid time format.")
                return
            if parsed_time.tzinfo is None:
                parsed_time = parsed_time.replace(tzinfo=datetime.timezone.utc)
            if parsed_time <= datetime.datetime.now(datetime.timezone.utc):
                await ctx.send("Reminder time must be in the future.")
                return
            update_data["trigger_time"] = parsed_time
            update_data["last_triggered"] = None  # Reset last_triggered

        if new_recurrence:
            if new_recurrence not in ("daily", "weekly", "monthly", "yearly", "hourly", "minutely", "none",) and not new_recurrence.startswith("every"):
                await ctx.send("Invalid recurrence interval.")
                return
            if new_recurrence == "none":
                update_data["recurrence"] = None
            else:
                update_data["recurrence"] = new_recurrence

            update_data["last_triggered"] = None

        if new_title:
            update_data["title"] = new_title

        if update_data:  # Only update if there are changes
            await collection.update_one({"reminder_id": reminder_id}, {"$set": update_data})
            await ctx.send("Reminder updated.")
        else:
            embed = discord.Embed(title=f"Edit Reminder: {reminder.reminder_id}", color=discord.Color.blurple())
            embed.add_field(name="Message", value=reminder.message, inline=False)
            embed.add_field(name="Trigger Time", value=str(reminder.trigger_time), inline=False)
            if reminder.recurrence:
                embed.add_field(name="Recurrence", value=reminder.recurrence, inline=False)
            await ctx.send(embed=embed)

    @remind.command(name="help")
    async def remind_help(self, ctx: commands.Context):
        embed = discord.Embed(title="Remind Help", description="Available commands for /remind", color=discord.Color.blue())
        embed.add_field(name="/remind me <time> <message>", value="Set a reminder", inline=False)
        embed.add_field(name="/remind channel <time> <message>", value="Set a reminder in this channel", inline=False)
        embed.add_field(name="/remind other <user> <time> <message>", value="Set a reminder for user (Requires `Manage Messages` permission)", inline=False)
        embed.add_field(name="/remind list", value="Lists your pending reminders.", inline=False)
        embed.add_field(name="/remind cancel <reminder_id> [--delete]", value="Cancels a reminder by its ID. Use `--delete` to permanently remove.", inline=False)
        embed.add_field(name="/remind edit <reminder_id> [options]", value="Edits an existing reminder.", inline=False)
        embed.add_field(name="Options for /remind edit", value="--message <new_message>\n--time <new_time>\n--repeat <new_recurrence>\n--title", inline=False)
        await ctx.send(embed=embed)

    @remind_me.autocomplete("time")
    @remind_channel.autocomplete("time")
    @remind_other.autocomplete("time")
    async def remind_time_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        return [
            app_commands.Choice(name="In 5 minutes", value="in 5 minutes"), app_commands.Choice(name="In 15 minutes", value="in 15 minutes"),
            app_commands.Choice(name="In 30 minutes", value="in 30 minutes"), app_commands.Choice(name="In 1 hour", value="in 1 hour"),
            app_commands.Choice(name="In 2 hours", value="in 2 hours"), app_commands.Choice(name="In 5 hours", value="in 5 hours"),
            app_commands.Choice(name="In 12 hours", value="in 12 hours"), app_commands.Choice(name="In 1 day", value="in 1 day"),
            app_commands.Choice(name="In 2 days", value="in 2 days"), app_commands.Choice(name="In 1 week", value="in 1 week"), app_commands.Choice(name="At 9am", value="at 9am"),
            app_commands.Choice(name="At 12pm", value="at 12pm"), app_commands.Choice(name="At 6pm", value="at 6pm"), app_commands.Choice(name="At 12am", value="at 12am"),
        ]

    @edit_reminder.autocomplete("new_recurrence")
    async def recurrence_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        return [
            app_commands.Choice(name="None", value="none"), app_commands.Choice(name="Daily", value="daily"), app_commands.Choice(name="Weekly", value="weekly"),
            app_commands.Choice(name="Monthly", value="monthly"), app_commands.Choice(name="Yearly", value="yearly"), app_commands.Choice(name="Hourly", value="hourly"),
            app_commands.Choice(name="Minutely", value="minutely"), app_commands.Choice(name="Every 2 days", value="every 2 days"),
            app_commands.Choice(name="Every 3 weeks", value="every 3 weeks"),
        ]


async def setup(bot: AssistantBot):
    if MONGO_URI:
        await bot.add_cog(Reminders(bot))
    else:
        bot.logger.warning("[FAILED] reminders.py cog not loaded. MONGO_URI not set.")
