import discord
from discord import app_commands
from discord.ext import commands

class AdminBasic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command()
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clear(self, interaction: discord.Interaction, amount: int):
        if amount < 1:
            await interaction.response.send_message(f"Enter a value greater than 0!", ephemeral=True)
            return

        await interaction.response.defer()
        await interaction.channel.purge(limit=amount + 1)
        await interaction.channel.send(f"{amount} message(s) have been deleted!", delete_after=5)

    # @clear.error
    # async def clear_error(self, interaction: discord.Interaction, error):
    #     if isinstance(error, commands.BadArgument):
    #         await interaction.response.send_message("`Correct Usage: /clear <amount (>0)>`")

async def setup(bot: commands.Bot):
    await bot.add_cog(AdminBasic(bot))