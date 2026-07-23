import os
import sys
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

GUILD_ID = discord.Object(os.getenv("GUILD_ID"))
OS_FILE_SLASH = "\\" if sys.platform == "win32" else "/"

class RueBot(commands.Bot):
    def __init__(self, intents: discord.Intents):
        super().__init__(command_prefix="/", intents=intents)
        # self.tree = app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        await self.load_cogs()
        self.tree.copy_global_to(guild=GUILD_ID)
        await self.tree.sync(guild=GUILD_ID)

    async def load_cogs(self, path_to_locate="cogs"):
        cog_path = Path(path_to_locate)
        dir_ignore = ["components"]

        for directory in cog_path.iterdir():
            if directory.name in dir_ignore:
                continue

            for cog in directory.iterdir():
                try:
                    cog_filename = cog.name
                    if cog_filename.endswith(".py") and not cog_filename.startswith("_"):
                        cog_str = str(cog).replace(".py", "").replace(OS_FILE_SLASH, ".")
                        await self.load_extension(cog_str)
                except:
                    print(f"Cannot load cog: {cog}")


def main():
    intents = discord.Intents.default()
    intents.message_content = True
    bot = RueBot(intents=intents)

    @bot.event
    async def on_ready():
        print(f"Logged in as {bot.user}")

    @bot.event
    async def on_app_command_error(interaction: discord.Interaction, error):
        if isinstance(error, commands.MissingPermissions):
            await interaction.response.send_message("Sorry! You do not have access to use this command!")

    @bot.tree.command()
    async def test(interaction: discord.Interaction):
        await interaction.response.send_message("TEST RUN")


    token_string = os.getenv("TOKEN")
    bot.run(token_string)

if __name__ == "__main__":
    main()