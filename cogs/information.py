import discord, psutil
from discord.ext import commands
from discord.ui import View, Button
from src.toolbag.context import CustomContext
from PIL import Image
from typing import Union
from discord.ext.commands import (
    command,
    cooldown,
    BucketType,
    Author,
    hybrid_command,
    group,
    Cog,
)
from colorthief import ColorThief
import requests
import io
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
    ButtonStyle,
    PartialEmoji,
    Emoji,
)
THUMBNAIL_URL = "https://images-ext-1.discordapp.net/external/aE5VAQixlI-i8rEjDviwX97aGONxhiLyf4yZVYaFMw8/%3Fsize%3D1024/https/cdn.discordapp.com/avatars/1476676961337212939/3b9d103e84e8875c2fcc48a27d4a47dd.png?format=webp&quality=lossless&width=190&height=190"


class Info(Cog):
    def __init__(self, bot):
        self.bot = bot

    @command(name="ping")
    async def ping(self, ctx):
        latency = round(self.bot.latency * 1000)
        await ctx.send(f"It took **{latency}ms** to reach **violet's shards**.")
    @command(
        name="hex",
        aliases=["dominant"],
        description="Get a hex code from an image."
    )
    async def hex(self, ctx, *, user: discord.User = None):
        user = user or ctx.author
        image_url = None

        if ctx.message.attachments:
            image_url = ctx.message.attachments[0].url
        elif user.display_avatar:
            image_url = user.display_avatar.url
        else:
            image_url = ctx.author.display_avatar.url

        async with ctx.typing():
            try:
                response = requests.get(image_url)
                image_bytes = io.BytesIO(response.content)
                image = Image.open(image_bytes)
                color_thief = ColorThief(image_bytes)
                dominant = color_thief.get_color(quality=1)

                hex_discord = int("0x{:02x}{:02x}{:02x}".format(*dominant), 16)
                hex_code = "#{:02x}{:02x}{:02x}".format(*dominant)

                return await ctx.embed(
                    title=f"Hex Code: {hex_code}",
                    description=f"RGB Value: {dominant}",
                    color=hex_discord
                )

            except Exception as e:
                return await ctx.warn(f"An error occurred: `{e}`")
    @command(name="avatar", aliases=["av"], description="Get a user's avatar.")
    async def avatar(
        self, ctx, *, user: Union[User, Member, str] = Author
    ) -> Message:
        if isinstance(user, (User, Member)):
            member = ctx.guild.get_member(user.id) if ctx.guild else None
        else:
            if user:
                members = ctx.guild.members 
                member_names = [m.display_name for m in members]
                match = get_close_matches(
                    user.lower(),
                    [name.lower() for name in member_names],
                    n=1,
                    cutoff=0.5,
                )
                if match:
                    member = next(
                        m for m in members if m.display_name.lower() == match[0]
                    )
                else:
                    return await ctx.warn(f"No matching user found for `{user}`.")
                user = member
            else:
                user = ctx.author
                member = ctx.guild.get_member(user.id) if ctx.guild else None

        if not user:
            return await ctx.warn("No user found or matched.")

        return await ctx.embed(
            title=f"{user}'s avatar",
            url=user.display_avatar.url,
            image=user.display_avatar.url,
        )
    @command(
        name="membercount",
        aliases=["mc"],
        description="Get the member count of the guild."
    )
    async def membercount(self, ctx):
        guild = ctx.guild
        total_members = guild.member_count
        bot_count = sum(1 for member in guild.members if member.bot)
        user_count = total_members - bot_count

        bot_percentage = (bot_count / total_members) * 100 if total_members > 0 else 0
        user_percentage = (user_count / total_members) * 100 if total_members > 0 else 0

        embed = discord.Embed(
            description=f"**{guild.name}'s Statistics**",
            color=self.bot.color
        )

        embed.add_field(
            name="Members",
            value=f"**{total_members}**",
            inline=True
        )
        embed.add_field(
            name="Users",
            value=f"**{user_count}** ({user_percentage:.2f}%)",
            inline=True
        )
        embed.add_field(
            name="Bots",
            value=f"**{bot_count}** ({bot_percentage:.2f}%)",
            inline=True
        )

        await ctx.send(embed=embed)
    @command(name="invite")
    async def invite(self, ctx):
        invite_link = discord.utils.oauth_url(self.bot.user.id, permissions=discord.Permissions(permissions=8))
        await ctx.send(f"{invite_link}")

    @command(name="source")
    async def source(self, ctx):
        await ctx.send("why?")

    @commands.command(aliases=["bi"])
    @commands.cooldown(1, 4, commands.BucketType.guild)
    async def botinfo(self, ctx):

        total_users = len(set(member.id for guild in self.bot.guilds for member in guild.members))
        total_guilds = len(self.bot.guilds)
        latency = round(self.bot.latency * 1000)
        ram_mib = psutil.Process().memory_info().rss / 1024 / 1024
        ram_display = f"{ram_mib / 1024:.2f}GiB" if ram_mib >= 1024 else f"{ram_mib:.2f}MiB"

        main_embed = discord.Embed(
            title="violet",
            description="> **violet** is developed and maintained by [**marian**](https://discord.com/users/1475139269365469244)",
            color=2428677
        )

        main_embed.add_field(
            name="Statistics:",
            value=(
                f"> **Users**: `{total_users:,}`\n"
                f"> **Guilds**: `{total_guilds}`\n"
                f"> **Commands**: `{len(self.bot.commands)}`"
            ),
            inline=True
        )

        main_embed.add_field(
            name="System:",
            value=(
                f"> **Latency**: {latency}ms\n"
                f"> **Discord.py**: {discord.__version__}\n"
                f"> **RAM**: `{ram_display}`"
            ),
            inline=True
        )

        main_embed.set_thumbnail(url=THUMBNAIL_URL)
        main_embed.set_footer(text="violet.rest • discord.gg/violetbot", icon_url=THUMBNAIL_URL)

        view = discord.ui.View()

        website_button = discord.ui.Button(
            label="Website",
            url="https://violet.rest/",
            style=discord.ButtonStyle.link
        )

        invite_button = discord.ui.Button(
            label="Invite",
            url="https://discord.com/oauth2/authorize?client_id=1476676961337212939&scope=bot+applications.commands&permissions=8",
            style=discord.ButtonStyle.link
        )

        support_button = discord.ui.Button(
            label="Support",
            url="https://discord.gg/violetbot",
            style=discord.ButtonStyle.link
        )

        bot_team_button = discord.ui.Button(
            label="Bot Team",
            style=discord.ButtonStyle.secondary
        )

        async def show_team(interaction: discord.Interaction):

            team_embed = discord.Embed(
                title="Violet's Team",
                description="Core team behind violet",
                color=2428677
            )

            team_embed.add_field(
                name="Developer",
                value="- idk",
                inline=False
            )

            team_embed.set_thumbnail(url=THUMBNAIL_URL)
            team_embed.set_footer(text="violet.rest • discord.gg/violetbot", icon_url=THUMBNAIL_URL)

            back_view = discord.ui.View()

            back_button = discord.ui.Button(
                label="Bot Info",
                style=discord.ButtonStyle.secondary
            )

            async def go_back(interaction2: discord.Interaction):
                await interaction2.response.edit_message(embed=main_embed, view=view)

            back_button.callback = go_back
            back_view.add_item(back_button)

            await interaction.response.edit_message(embed=team_embed, view=back_view)

        bot_team_button.callback = show_team

        view.add_item(website_button)
        view.add_item(invite_button)
        view.add_item(support_button)
        view.add_item(bot_team_button)

        await ctx.send(embed=main_embed, view=view)

async def setup(bot):
    await bot.add_cog(Info(bot))