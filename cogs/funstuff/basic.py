import discord
from discord.ext import commands

class CommandBasic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def self(self, interaction: discord.Interaction, message: str):
        await interaction.response.send_message(message)

async def setup(bot: commands.Bot):
    await bot.add_cog(CommandBasic(bot))