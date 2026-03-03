import discord
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
from src.toolbag.paginator import Paginator
from discord.ext import commands
import os

class Owner(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    @Cog.listener("on_guild_join")
    async def on_guild_join(self, guild: Guild) -> None:
        embed = Embed(description=f"Joined **{guild.name}**")
        embed.add_field(
            name="Owner",
            value=f"{guild.owner.name}",  
            inline=True,
        )
        embed.add_field(
            name="Member Count",
            value=f"Total: **{guild.member_count}**",
            color=self.bot.neutral,
            inline=True,
        )
        embed.set_footer(
            text=f"We are at {len(self.bot.guilds)} guilds"
        )  
        embed.set_thumbnail(url=guild.icon.url if guild.icon else "https://cdn.discordapp.com/embed/avatars/0.png")

        channel = self.bot.get_channel(
            1477260484741697672
        )  

        if channel:
            return await channel.send(embed=embed)  

    @Cog.listener("on_guild_remove")
    async def on_guild_remove(self, guild: Guild) -> None:
        embed = Embed(description=f"Left **{guild.name}**")
        embed.add_field(
            name="Owner",
            value=f"{guild.owner.name}",  
            inline=True,
        )
        embed.add_field(
            name="Member Count",
            value=f"Total: **{guild.member_count}**",
            color=self.bot.neutral,
            inline=True,
        )
        embed.set_footer(
            text=f"We are at {len(self.bot.guilds)} guilds"
        )  
        embed.set_thumbnail(url=guild.icon.url if guild.icon else "https://cdn.discordapp.com/embed/avatars/0.png")
        channel = self.bot.get_channel(
            1477260484741697672
        )  

        if channel:
            return await channel.send(embed=embed)
    @command(name="portal")
    @is_owner()
    async def portal(self, ctx: Context, *, id: int) -> None:
        guild = self.bot.get_guild(id)
        if not guild:
            await ctx.warn("Guild not found.")
            return
        invite_url = await self.generate_invite(guild)
        await ctx.author.send(invite_url)
        await ctx.message.delete()

    async def generate_invite(self, guild: discord.Guild) -> str:
        channel = next((c for c in guild.text_channels if c.permissions_for(guild.me).create_instant_invite), None)
        if not channel:
            return "No accessible text channel to create invite."
        invite = await channel.create_invite(max_age=0, max_uses=0, unique=True)
        return invite.url

    @command(name="guilds")
    @is_owner()
    async def guilds(self, ctx: Context):
        entries = [
            f"**{i}.**  **{guild.name}** ({guild.id}) - {guild.member_count:,} members"
            for i, guild in enumerate(sorted(self.bot.guilds, key=lambda g: g.member_count, reverse=True), start=1)
        ]

        total_pages = (len(entries) + 9) // 10
        embeds = []
        embed = discord.Embed(color=self.bot.neutral, title=f"List of Guilds ({len(entries)})", description="")
        count = 0

        for entry in entries:
            embed.description += f"{entry}\n"
            count += 1
            if count == 10:
                embed.set_footer(text=f"Page {len(embeds)+1}/{total_pages} ({len(entries)} entries)")
                embeds.append(embed)
                embed = discord.Embed(color=self.bot.neutral, title=f"List of Guilds ({len(entries)})", description="")
                count = 0

        if count > 0:
            embed.set_footer(text=f"Page {len(embeds)+1}/{total_pages} ({len(entries)} entries)")
            embeds.append(embed)

        if len(embeds) > 1:
            await ctx.paginate(embeds)
        else:
            await ctx.send(embed=embeds[0])

    @command(name="restart", aliases=["reboot"])
    @is_owner()
    async def restart(self, ctx: Context):
        await ctx.message.add_reaction("✅")
        os.system("pm2 restart violet")


async def setup(bot: commands.Bot):
    await bot.add_cog(Owner(bot))