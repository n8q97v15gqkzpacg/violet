import discord
from discord.ext import commands
from discord.ext.commands import HelpCommand, Group
from discord.ui import Button, View
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Unpack, TypedDict, cast
from datetime import datetime
from discord import (
    AllowedMentions,
    ButtonStyle,
    Color,
    Message,
    MessageReference,
    Embed,
    Role,
    Member,
    ui,
)
from src.toolbag.paginator import Paginator
class FieldDict(TypedDict, total=False):
    name: str
    value: str
    inline: bool


class FooterDict(TypedDict, total=False):
    text: Optional[str]
    icon_url: Optional[str]


class AuthorDict(TypedDict, total=False):
    name: Optional[str]
    icon_url: Optional[str]


class ButtonDict(TypedDict, total=False):
    url: Optional[str]
    emoji: Optional[str]
    style: Optional[ButtonStyle]
    label: Optional[str]
class MessageKwargs(TypedDict, total=False):
    content: Optional[str]
    tts: Optional[bool]
    allowed_mentions: Optional[AllowedMentions]
    reference: Optional[MessageReference]
    mention_author: Optional[bool]
    delete_after: Optional[float]
    url: Optional[str]
    title: Optional[str]
    color: Optional[Color]
    image: Optional[str]
    description: Optional[str]
    thumbnail: Optional[str]
    footer: Optional[FooterDict]
    author: Optional[AuthorDict]
    fields: Optional[List[FieldDict]]
    timestamp: Optional[datetime]
    view: Optional[View]
    buttons: Optional[List[ButtonDict]]
class CustomContext(commands.Context):
    async def embed(self, **kwargs: Unpack[MessageKwargs]) -> Message:
        return await self.send(**self.create(**kwargs))
    def create(self, **kwargs: Unpack[MessageKwargs]) -> Dict[str, Any]:
        """Create a message with the given keword arguments.

        Returns:
            Dict[str, Any]: The message content, embed, view and delete_after.
        """
        view = View()

        for button in kwargs.get("buttons") or []:
            if not button or not button.get("label"):
                continue

            view.add_item(
                Button(
                    label=button.get("label"),
                    style=button.get("style") or ButtonStyle.secondary,
                    emoji=button.get("emoji"),
                    url=button.get("url"),
                )
            )

        embed = (
            Embed(
                url=kwargs.get("url"),
                description=kwargs.get("description"),
                title=kwargs.get("title"),
                color=kwargs.get("color") or self.bot.neutral,
                timestamp=kwargs.get("timestamp"),
            )
            .set_image(url=kwargs.get("image"))
            .set_thumbnail(url=kwargs.get("thumbnail"))
            .set_footer(
                text=cast(dict, kwargs.get("footer", {})).get("text"),
                icon_url=cast(dict, kwargs.get("footer", {})).get("icon_url"),
            )
            .set_author(
                name=cast(dict, kwargs.get("author", {})).get("name", ""),
                icon_url=cast(dict, kwargs.get("author", {})).get("icon_url", ""),
            )
        )

        for field in kwargs.get("fields") or []:
            if not field:
                continue

            embed.add_field(
                name=field.get("name"),
                value=field.get("value"),
                inline=field.get("inline", False),
            )

        return {
            "content": kwargs.get("content"),
            "embed": embed,
            "view": kwargs.get("view") or view,
            "delete_after": kwargs.get("delete_after"),
        }

    async def approve(self, message: str, **kwargs) -> discord.Message:
        embed = discord.Embed(
            description=f"<:approve:1477465120031637535> {self.author.mention}: {message}",
            color=self.bot.success,
            **kwargs
        )
        return await self.reply(embed=embed, mention_author=False)

    async def deny(self, message: str, **kwargs) -> discord.Message:
        embed = discord.Embed(
            description=f"<:deny:1477465080986603571> {self.author.mention}: {message}",
            color=self.bot.error,
            **kwargs
        )
        return await self.reply(embed=embed, mention_author=False)

    async def neutral(self, message: str, **kwargs) -> discord.Message:
        embed = discord.Embed(
            description=f"{self.author.mention}: {message}",
            color=self.bot.neutral,
            **kwargs
        )
        return await self.reply(embed=embed, mention_author=False)

    async def warn(self, message: str, **kwargs) -> discord.Message:
        embed = discord.Embed(
            description=f"<:warning:1477463685814423676> {self.author.mention}: {message}",
            color=self.bot.warn,
            **kwargs
        )
        return await self.reply(embed=embed, mention_author=False)

    async def paginate(self, embeds: list[discord.Embed], **kwargs): 
        if not embeds:
            return
        return await self.reply(embed=embeds[0], view=Paginator(self, embeds), mention_author=False, **kwargs)
class VioletHelp(HelpCommand):
    context: "Context"

    def __init__(self, **options):
        super().__init__(
            command_attrs={"aliases": ["h", "cmds"], "hidden": True},
            verify_checks=False,
            **options,
        )

    async def send_bot_help(self, mapping):
        ctx = self.context

        class HelpSelect(discord.ui.Select):
            def __init__(self, mapping):
                self.mapping = mapping
                options = []

                for cog, commands_list in mapping.items():
                    if cog and cog.qualified_name.lower() == "owner":
                        continue

                    filtered = [c for c in commands_list if not c.hidden]
                    if not filtered:
                        continue

                    label = cog.qualified_name if cog else "No Category"
                    options.append(
                        discord.SelectOption(
                            label=label,
                            description=f"{len(filtered)} command(s)"
                        )
                    )

                super().__init__(
                    placeholder="Select a category",
                    min_values=1,
                    max_values=1,
                    options=options
                )

            async def callback(self, interaction: discord.Interaction):
                selected = self.values[0]

                for cog, commands_list in self.mapping.items():
                    name = cog.qualified_name if cog else "No Category"

                    if name.lower() == "owner": 
                        continue

                    if name == selected:
                        filtered = [c for c in commands_list if not c.hidden]

                        embed = discord.Embed(
                            title=f"{name} Commands",
                            description=f"```\n{', '.join(c.name for c in filtered)}\n```",
                            color=ctx.bot.neutral
                        )
                        embed.set_footer(text=f"{len(filtered)} command(s)")
                        await interaction.response.edit_message(embed=embed)
                        return

        class HelpView(discord.ui.View):
            def __init__(self, mapping):
                super().__init__(timeout=60)
                self.add_item(HelpSelect(mapping))

        embed = Embed(
            title="Violet Menu",
            description="- Select a category to view commands.",
            color=ctx.bot.neutral
        )

        await ctx.reply(embed=embed, view=HelpView(mapping))

    async def send_command_help(self, command):
        aliases = command.aliases

        try:
            permissions = command.permissions
        except (AttributeError, TypeError):
            permissions = []

        embed = (
            Embed(
                color=self.context.bot.neutral,
                title=f"Command: {command.qualified_name}",
                description=command.help or "No description provided.",
            )
            .set_author(
                name=self.context.author.name,
                icon_url=self.context.author.display_avatar.url,
            )
            .add_field(
                name="Aliases",
                value=f"{', '.join(aliases)}" if aliases else "N/A",
                inline=True,
            )
            .add_field(
                name="Parameters",
                value=f"{', '.join(command.clean_params)}"
                if command.clean_params
                else "N/A",
                inline=True,
            )
            .add_field(
                name="Permissions",
                value=f"<:warning:1477463685814423676> "
                + (f"{', '.join(permissions)}" if permissions else "N/A"),
                inline=True,
            )
            .add_field(
                name="Usage",
                value=f"```Syntax: {self.context.clean_prefix}{command.qualified_name} {command.usage or ''}```",
                inline=False,
            )
            .set_footer(
                text=(
                    f"Module: {command.cog_name.lower()}"
                    if command.cog_name
                    else "Module: N/A"
                ),
            )
        )

        return await self.context.send(embed=embed)

    async def send_group_help(self, group: Group):
        embeds = []

        group_permissions = set()
        for cmd in group.commands:
            try:
                if hasattr(cmd, "permissions") and cmd.permissions:
                    group_permissions.update(cmd.permissions)
            except (AttributeError, TypeError):
                continue

        group_embed = (
            Embed(
                color=self.context.bot.neutral,
                title=f"Command Group: {group.name}",
                description=group.help or "No description provided.",
            )
            .set_author(
                name=self.context.author.name,
                icon_url=self.context.author.display_avatar.url,
            )
            .add_field(
                name="Aliases",
                value=", ".join(group.aliases) if group.aliases else "N/A",
                inline=True,
            )
            .add_field(
                name="Parameters",
                value=", ".join(group.clean_params) if group.clean_params else "N/A",
                inline=True,
            )
            .add_field(
                name="Permissions",
                value="<:warning:1477463685814423676> "
                + (", ".join(group_permissions) if group_permissions else "N/A"),
                inline=True,
            )
            .add_field(
                name="Usage",
                value=f"```Syntax: {self.context.clean_prefix}{group.qualified_name} {group.usage or ''}```",
                inline=False,
            )
            .set_footer(
                text=f"Page 1/{len(group.commands) + 1} • Module: {group.cog_name.lower() if group.cog_name else 'N/A'}"
            )
        )

        embeds.append(group_embed)

        for i, command in enumerate(group.commands):
            try:
                permissions = command.permissions
            except (AttributeError, TypeError):
                permissions = []

            command_embed = (
                Embed(
                    color=self.context.bot.neutral,
                    title=f"Command: {command.name}",
                    description=command.help or "No description provided.",
                )
                .add_field(
                    name="Aliases",
                    value=", ".join(command.aliases) if command.aliases else "N/A",
                    inline=True,
                )
                .add_field(
                    name="Parameters",
                    value=", ".join(command.clean_params) if command.clean_params else "N/A",
                    inline=True,
                )
                .add_field(
                    name="Permissions",
                    value="<:warning:1477463685814423676> "
                    + (", ".join(permissions) if permissions else "N/A"),
                    inline=True,
                )
                .add_field(
                    name="Usage",
                    value=f"```Syntax: {self.context.clean_prefix}{command.qualified_name} {command.usage or ''}```",
                    inline=False,
                )
                .set_footer(
                    text=f"Page {i + 2}/{len(group.commands) + 1} • Module: {command.cog_name.lower() if command.cog_name else 'N/A'}"
                )
            )

            embeds.append(command_embed)

        await self.context.paginate(embeds)