import discord, jishaku, os, asyncpg, dotenv, aiohttp, discord_ios
from discord.ext import commands
from src.toolbag.context import CustomContext
from src.toolbag.context import VioletHelp

os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True"
os.environ["JISHAKU_HIDE"] = "True"

token = os.getenv("TOKEN")


class violet(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=",",
            intents=discord.Intents.all(),
            owner_ids={1475139269365469244, 1460003194771083296, 713128996287807600},
            allowed_mentions=discord.AllowedMentions(
                everyone=False,
                users=True,
                roles=False
            ),
            help_command=VioletHelp()
        )

        self.color = 0xFFFFFF
        self.warn = 0xEFB700
        self.error = 0xFF0000
        self.success = 0x00FF00
        self.neutral = 0xFFFFFF
        self.cooldown = commands.CooldownMapping.from_cooldown(
            3,
            4,
            commands.BucketType.user
        )

        self.add_check(self.global_cooldown)

    async def global_cooldown(self, ctx):
        bucket = self.cooldown.get_bucket(ctx.message)
        retry_after = bucket.update_rate_limit()

        if retry_after:
            raise commands.CommandOnCooldown(
                bucket,
                retry_after,
                commands.BucketType.user
            )

        return True

    async def setup_hook(self):
        await self.load_extension("jishaku")
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                await self.load_extension(f"cogs.{filename[:-3]}")

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")

    async def get_context(self, message, *, cls=None):
        return await super().get_context(message, cls=cls or CustomContext)

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.warn("Missing required argument.")

        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.warn(
                f"You're on cooldown. Try again in {round(error.retry_after)}s."
            )

        elif isinstance(error, commands.MissingPermissions):
            await ctx.warn(
                f"You're **missing** permission: **{', '.join(p for p in error.missing_permissions)}**"
            )

        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.warn("I do not have the required permissions.")

        elif isinstance(error, commands.BadArgument):
            await ctx.warn("Bad argument.")

        else:
            await ctx.warn(f"An error occurred while processing the command.\n**{error}**")
            raise error

    async def on_message(self, message):
        if message.author.bot:
            return
        await self.process_commands(message)


if __name__ == "__main__":
    bot = violet()
    bot.run(token)