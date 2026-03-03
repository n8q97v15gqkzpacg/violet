import discord
import asyncpg
import asyncio
import os
import timezonefinder
from discord import (
    Embed,
    User,
    Member,
    Message,
    Spotify,
    ActivityType,
    Permissions,
    Status,
    Invite,
    Role,
    Button,
    ButtonStyle,
    Guild,
)
from discord.ext.commands import (
    command,
    cooldown,
    Context,
    BucketType,
    Author,
    hybrid_command,
    group,
    Cog,
    has_permissions,
    is_owner,
)
from discord.ext import commands
from datetime import datetime
import humanize
from src.toolbag.paginator import Paginator
from src.toolbag.context import CustomContext
from discord.utils import format_dt, get

#from uwuipy import uwuipy
from typing import Optional

DB_HOST     = "localhost"
DB_PORT     = 5432
DB_NAME     = "discord_bot"
DB_USER     = "botuser"
DB_PASSWORD = "youshallnotpass12"


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.Sniped = {}
        self.editSnipe = {}
        self.reactSnipe = {}
        self.pool: Optional[asyncpg.Pool] = None
       # try:
        #    self.uwu = uwuipy(None)
       # except TypeError:
          #  self.uwu = uwuipy()

    async def cog_load(self):
        self.pool = await asyncpg.create_pool(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        await self.pool.execute("""
            CREATE TABLE IF NOT EXISTS uwulock (
                guild_id BIGINT,
                user_id BIGINT,
                PRIMARY KEY (guild_id, user_id)
            )
        """)

    async def cog_unload(self):
        if self.pool:
            await self.pool.close()
    @Cog.listener("on_message_delete")
    async def snipe_listener(self, message: Message) -> None:
        if message.author.bot:
            return

        if message.channel.id not in self.Sniped:
            self.Sniped[message.channel.id] = []

        image_url = None
        if message.attachments:
            image_url = message.attachments[0].url

        self.Sniped[message.channel.id].append(
            {
                "author": str(message.author),
                "author_url": str(message.author.display_avatar.url),
                "content": message.content,
                "image_url": image_url,
                "timestamp": message.created_at,
                "deleted_at": datetime.utcnow(),
            }
        )

    @Cog.listener("on_raw_reaction_remove")
    async def reactionsnip_listener(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return

        channel = self.bot.get_channel(payload.channel_id)
        if not channel:
            return

        message_link = f"https://discord.com/channels/{payload.guild_id}/{payload.channel_id}/{payload.message_id}"
        emoji = str(payload.emoji)
        if payload.channel_id not in self.reactSnipe:
            self.reactSnipe[payload.channel_id] = []

        self.reactSnipe[payload.channel_id].append(
            {
                "author": str(payload.user_id),
                "emoji": emoji,
                "message_link": message_link,
                "message_id": payload.message_id,
                "timestamp": datetime.utcnow(),
            }
        )

    @Cog.listener("on_message_edit")
    async def editsnipe_listener(self, before: Message, after: Message) -> None:
        if before.guild and not before.author.bot:
            channel_id = before.channel.id

            if channel_id not in self.editSnipe:
                self.editSnipe[channel_id] = []

            self.editSnipe[channel_id].append(
                {
                    "before_content": before.content,
                    "after_content": after.content,
                    "author": str(before.author),
                    "author_url": str(before.author.display_avatar.url),
                    "timestamp": (before.edited_at),
                    "edited_at": datetime.utcnow(),
                }
            )

    

    @commands.group(name="uwulock", aliases=["uwu"], invoke_without_command=True)
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def uwulock(self, ctx, member: discord.Member):
        if self.pool is None:
            return await ctx.warn("Database unavailable.")

        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            return await ctx.warn("You can't uwulock someone with a higher or equal role!")

        if member.id == ctx.guild.owner_id:
            return await ctx.warn("You can't uwulock the server owner!")

        if member.bot:
            return await ctx.warn("You can't uwulock bots!")

        deleted = await self.pool.fetchval(
            "DELETE FROM uwulock WHERE guild_id = $1 AND user_id = $2 RETURNING user_id",
            ctx.guild.id, member.id
        )

        if deleted:
            return await ctx.approve(f"I've removed {member.mention} from **uwulock**.")

        await self.pool.execute(
            "INSERT INTO uwulock (guild_id, user_id) VALUES ($1, $2) ON CONFLICT DO NOTHING",
            ctx.guild.id, member.id
        )
        return await ctx.approve(f"I've added {member.mention} to **uwulock**.")

    @uwulock.command(name="list")
    @commands.guild_only()
    async def uwulock_list(self, ctx):
        if self.pool is None:
            return await ctx.warn("Database unavailable.")

        records = await self.pool.fetch(
            "SELECT user_id FROM uwulock WHERE guild_id = $1",
            ctx.guild.id
        )

        if not records:
            return await ctx.warn("No one in this server is uwulocked!")

        members = []
        for record in records:
            member = ctx.guild.get_member(record["user_id"])
            if member:
                members.append(f"{member.mention} - `{member.id}`")

        if not members:
            return await ctx.warn("No one in this server is uwulocked!")

        embeds = []
        members_per_page = 10

        for i in range(0, len(members), members_per_page):
            chunk = members[i:i + members_per_page]
            embed = discord.Embed(
                title="Uwulocked Members",
                description="\n".join(chunk),
                color=0x2b2d31
            )
            embed.set_footer(text=f"Page {len(embeds) + 1}/{(len(members) + members_per_page - 1) // members_per_page} ({len(members)} members)")
            embeds.append(embed)

        await ctx.send(embed=embeds[0])

    @uwulock.command(name="reset")
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def uwulock_reset(self, ctx):
        if self.pool is None:
            return await ctx.warn("Database unavailable.")

        count = await self.pool.fetchval(
            "SELECT COUNT(*) FROM uwulock WHERE guild_id = $1",
            ctx.guild.id
        )

        if not count:
            return await ctx.warn("No one in this server is uwulocked!")

        await self.pool.execute(
            "DELETE FROM uwulock WHERE guild_id = $1",
            ctx.guild.id
        )
        return await ctx.approve("I've reset the **uwulock** list.")

    @commands.Cog.listener("on_message")
    async def uwulock_listener(self, message: discord.Message):
        if message.author.bot or message.guild is None or self.pool is None:
            return

        record = await self.pool.fetchval(
            "SELECT 1 FROM uwulock WHERE guild_id = $1 AND user_id = $2",
            message.guild.id, message.author.id
        )

        if not record:
            return

        if not message.content:
            return

        await asyncio.sleep(0.5)

        uwuified = self.uwu.uwuify(message.content).strip()

        if not uwuified:
            return

        thread = discord.utils.MISSING
        channel = message.channel

        if isinstance(channel, discord.Thread):
            thread = channel
            channel = channel.parent

        if not hasattr(channel, "webhooks"):
            return

        try:
            webhooks = await channel.webhooks()
        except discord.Forbidden:
            return

        webhook = discord.utils.get(webhooks, name="Uwulock")

        if webhook is None:
            try:
                webhook = await channel.create_webhook(name="Uwulock")
            except discord.Forbidden:
                return

        try:
            await message.delete()
        except discord.Forbidden:
            pass

        try:
            await webhook.send(
                content=uwuified,
                username=message.author.display_name,
                avatar_url=message.author.display_avatar.url,
                allowed_mentions=discord.AllowedMentions.none(),
                thread=thread
            )
        except Exception:
            pass
    @command(
        name="reactionsnipe",
        description="See recently removed reactions.",
        aliases=["rs"],
    )
    async def reactionsnipe(self, ctx: Context, *, index: int = 1):
        snipes = self.reactSnipe.get(ctx.channel.id, [])
        if not snipes:
            return await ctx.embed(
                description=f"> 🔎 {ctx.author.mention}: No **reaction removal** found!",
            )

        index -= 1

        if index < 0 or index >= len(snipes):
            return await ctx.warn(f"Invalid index!")

        sniped = snipes[index]
        user_id = sniped.get("author", "N/A")
        emoji = sniped.get("emoji", "")
        timestamp = sniped.get("timestamp", datetime.utcnow())
        original_message_id = sniped.get("message_id")

        embed = Embed(
            description=f"> **{await ctx.guild.fetch_member(user_id)}** reacted with *{emoji}* {format_dt(timestamp, 'R')}",
            color=ctx.bot.neutral,
        )

        channel = self.bot.get_channel(ctx.channel.id)
        original_message = await channel.fetch_message(original_message_id)
        await original_message.reply(embed=embed)

    @command(name="editsnipe", aliases=["es"], description="See edited messages.")
    async def editsnipe(self, ctx: Context, *, index: int = 1):
        editsnipes = self.editSnipe.get(ctx.channel.id, [])
        if not editsnipes:
            return await ctx.embed(
                description=f"> 🔎 {ctx.author.mention}: No **edited messages** found!"
            )

        index -= 1

        if index < 0 or index >= len(editsnipes):
            return await ctx.warn(f"Invalid index!")

        editsniped = editsnipes[index]
        before = editsniped.get("before_content", "")
        after = editsniped.get("after_content", "")
        author = editsniped.get("author", "N/A")
        author_url = editsniped.get("author_url", "")
        edited = editsniped.get("edited_at", datetime.utcnow())

        time_after_edit = humanize.naturaltime(edited)

        embed = Embed(description=f"> **Before:** {before} \n> **After:** {after}")
        embed.set_footer(
            text=f"Edited {time_after_edit} ∙ {index + 1}/{len(editsnipes)}"
        )
        embed.set_author(name=author, icon_url=author_url)
        return await ctx.send(embed=embed)

    @command(name="snipe", aliases=["s"], description="See deleted messages.")
    async def snipe(self, ctx: Context, *, index: int = 1):
        sniped_messages = self.Sniped.get(ctx.channel.id, [])
        if not sniped_messages:
            return await ctx.embed(
                description=f"> 🔎 {ctx.author.mention}: No **deleted messages** found!"
            )

        index -= 1

        if index < 0 or index >= len(sniped_messages):
            return await ctx.warn("Invalid index!")

        sniped_message = sniped_messages[index]
        content = sniped_message.get("content", "")
        author = sniped_message.get("author", "N/A")
        author_icon = sniped_message.get("author_url")
        deleted_at = sniped_message.get("deleted_at", datetime.utcnow())
        image_url = sniped_message.get("image_url")

        time_since_deletion = humanize.naturaltime(deleted_at)

        embed = Embed(description=content)
        embed.set_footer(
            text=f"Deleted {time_since_deletion} ∙ {index + 1}/{len(sniped_messages)}"
        )
        embed.set_author(name=author, icon_url=author_icon)

        if image_url:
            embed.set_image(url=image_url)

        await ctx.send(embed=embed)

    @command(
        name="clearsnipes",
        aliases=["cs"],
        description="Clear all sniped messages in the guild.",
    )
    @has_permissions(manage_messages=True)
    async def clearsnipes(self, ctx: Context):
        cleared = False

        if ctx.message.channel.id in self.Sniped:
            del self.Sniped[ctx.message.channel.id]
            cleared = True

        if ctx.message.channel.id in self.editSnipe:
            del self.editSnipe[ctx.message.channel.id]
            cleared = True

        if ctx.message.channel.id in self.reactSnipe:
            del self.reactSnipe[ctx.message.channel.id]
            cleared = True

        if cleared:
            return await ctx.message.add_reaction("✅") 
        else:
            return await ctx.warn("> There are no **sniped** messages in this guild.")
async def setup(bot):
    await bot.add_cog(Utility(bot))