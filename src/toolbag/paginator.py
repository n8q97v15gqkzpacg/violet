import discord
from discord import Message

class Paginator(discord.ui.View):
    def __init__(self, ctx, pages: list[discord.Embed], current: int = 0, timeout: float = None):
        super().__init__(timeout=10)
        self.ctx = ctx
        self.pages = pages
        self.current = current
        self.message: Message

        buttons = [
            ("previous", "<:previous:1308182040407052338>", discord.ButtonStyle.blurple),
            ("next", "<:next:1308182038150647888>", discord.ButtonStyle.blurple),
            ("pages", "<:navigate:1308182035788988436>", discord.ButtonStyle.grey),
            ("cancel", "<:cancel:1308182042554400778>", discord.ButtonStyle.danger),
        ]
        for cid, emoji, style in buttons:
            self.add_item(PaginatorButton(style, emoji, cid))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.warn("You're not the **author** of this embed!")
            return False
        return True

class PaginatorButton(discord.ui.Button):
    def __init__(self, style, emoji, custom_id=None):
        super().__init__(style=style, emoji=emoji, custom_id=custom_id)

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        if self.custom_id == "previous":
            view.current = (view.current - 1) % len(view.pages)
        elif self.custom_id == "next":
            view.current = (view.current + 1) % len(view.pages)
        elif self.custom_id == "pages":
            return await interaction.response.send_modal(PagesModal(view))
        elif self.custom_id == "cancel":
            view.stop()
            return await interaction.message.delete()
        await interaction.response.edit_message(embed=view.pages[view.current])

class PagesModal(discord.ui.Modal, title="Select Page"):
    def __init__(self, view: Paginator):
        super().__init__()
        self.view = view
        self.add_item(discord.ui.TextInput(
            label="Page",
            placeholder="5",
            custom_id="PAGINATOR:PAGES",
            style=discord.TextStyle.short,
            min_length=1,
            max_length=3,
            required=True
        ))

    async def on_submit(self, interaction: discord.Interaction):
        try:
            page = int(self.children[0].value)
        except ValueError:
            return await interaction.warn("Please provide a valid page number.")
        if not (1 <= page <= len(self.view.pages)):
            return await interaction.warn("Please provide a valid page number.")
        self.view.current = page - 1
        await interaction.response.edit_message(embed=self.view.pages[self.view.current])