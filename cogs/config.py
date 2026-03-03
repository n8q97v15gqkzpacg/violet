import discord
from discord.ext import commands
import os, aiohttp
import asyncpg

DB_HOST     = "localhost"
DB_PORT     = 5432
DB_NAME     = "discord_bot"
DB_USER     = "botuser"
DB_PASSWORD = "youshallnotpass12"

class Config(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    async def cog_load(self):
        self.pool = await asyncpg.create_pool(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        
        async with self.pool.acquire() as connection:
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS swear_words (
                    guild_id BIGINT,
                    word TEXT,
                    PRIMARY KEY (guild_id, word)
                )
            """)
            
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS swear_stats (
                    guild_id BIGINT PRIMARY KEY,
                    total_swears INTEGER DEFAULT 0
                )
            """)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        async with self.pool.acquire() as connection:
            swear_words = await connection.fetch(
                """
                SELECT word FROM swear_words
                WHERE guild_id = $1
                """,
                message.guild.id
            )
            swear_words = [row["word"] for row in swear_words]

            if any(swear in message.content.lower() for swear in swear_words):
                await connection.execute("""
                    INSERT INTO swear_stats (guild_id, total_swears)
                    VALUES ($1, 1)
                    ON CONFLICT (guild_id)
                    DO UPDATE SET total_swears = swear_stats.total_swears + 1
                """, message.guild.id)
                
                result = await connection.fetchrow("""
                    SELECT total_swears FROM swear_stats
                    WHERE guild_id = $1
                """, message.guild.id)
                
                total_swears = result['total_swears']
                
                await message.channel.send(
                    f"this server has {total_swears} swears now",
                    reference=message,
                    mention_author=False
                )

    @commands.group(name="swear")
    @commands.has_permissions(manage_guild=True)
    async def swear(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send_help("swear")

    @swear.command(name="add")
    @commands.has_permissions(manage_guild=True)
    async def swear_add(self, ctx, *, word: str):
        async with self.pool.acquire() as connection:
            await connection.execute(
                """
                INSERT INTO swear_words (guild_id, word)
                VALUES ($1, $2)
                ON CONFLICT DO NOTHING
                """,
                ctx.guild.id,
                word.lower()
            )
        await ctx.send(f"Added '{word}' to the swear word list.")

    @swear.command(name="remove")
    @commands.has_permissions(manage_guild=True)
    async def swear_remove(self, ctx, *, word: str):
        async with self.pool.acquire() as connection:
            await connection.execute(
                """
                DELETE FROM swear_words
                WHERE guild_id = $1 AND word = $2
                """,
                ctx.guild.id,
                word.lower()
            )
        await ctx.send(f"Removed '{word}' from the swear word list.")

    @swear.command(name="list")
    @commands.has_permissions(manage_guild=True)
    async def swear_list(self, ctx):
        async with self.pool.acquire() as connection:
            rows = await connection.fetch(
                """
                SELECT word FROM swear_words
                WHERE guild_id = $1
                """,
                ctx.guild.id
            )
        if rows:
            swear_words = [row["word"] for row in rows]
            await ctx.send(f"Swear words for this server: {', '.join(swear_words)}")
        else:
            await ctx.send("No swear words have been added for this server.")
    
    @swear.command(name="stats")
    @commands.has_permissions(manage_guild=True)
    async def swear_stats(self, ctx):
        async with self.pool.acquire() as connection:
            result = await connection.fetchrow("""
                SELECT total_swears FROM swear_stats
                WHERE guild_id = $1
            """, ctx.guild.id)
            
            total_swears = result['total_swears'] if result else 0
            
        await ctx.neutral(f"This server has a total of {total_swears} recorded swears.")

    @swear.command(name="reset")
    @commands.has_permissions(administrator=True)
    async def swear_reset(self, ctx):
        async with self.pool.acquire() as connection:
            await connection.execute("""
                INSERT INTO swear_stats (guild_id, total_swears)
                VALUES ($1, 0)
                ON CONFLICT (guild_id)
                DO UPDATE SET total_swears = 0
            """, ctx.guild.id)
        await ctx.approve("Swear counter has been reset to 0.")

    @commands.group(name="customize", aliases=["custom", "cu"], invoke_without_command=True)
    async def customize(self, ctx):
        """Base command for customizing the bot's appearance for the server."""
        await ctx.send_help("customize")

    @customize.command(name="icon")
    @commands.has_permissions(manage_guild=True)
    async def customize_icon(self, ctx, url: str):
        """Change the bot's icon for this server."""
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return await ctx.send("Failed to fetch the image. Please provide a valid URL.")
                data = await resp.read()
                try:
                    await ctx.guild.me.edit(avatar=data)
                    await ctx.send("Bot icon updated successfully!")
                except Exception as e:
                    await ctx.send(f"Failed to update bot icon: {e}")


    @customize.command("banner")
    @commands.has_permissions(manage_guild=True)
    async def customize_banner(self, ctx, url: str):
        """Change the bot's banner for this server."""
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return await ctx.send("Failed to fetch the image. Please provide a valid URL.")
                data = await resp.read()
                try:
                    await ctx.guild.me.edit(banner=data)
                    await ctx.send("Bot banner updated successfully!")
                except Exception as e:
                    await ctx.send(f"Failed to update bot banner: {e}")

    @customize.command("nickname")
    @commands.has_permissions(manage_guild=True)
    async def customize_nickname(self, ctx, *, nickname: str):
        """Change the bot's nickname for this server."""
        try:
            await ctx.guild.me.edit(nick=nickname)
            await ctx.send(f"Bot nickname updated to: {nickname}")
        except Exception as e:
            await ctx.send(f"Failed to update bot nickname: {e}")


    @customize.command("reset")
    @commands.has_permissions(manage_guild=True)
    async def customize_reset(self, ctx):
        """Reset the bot's appearance to default."""
        try:
            await ctx.guild.me.edit(
                avatar=None,
                banner=None
            )
            await ctx.send("Bot appearance reset to default!")
        except Exception as e:
            await ctx.send(f"Failed to reset bot appearance: {e}")


async def setup(bot):
    await bot.add_cog(Config(bot))