import discord
from discord import app_commands
from discord.ext import commands

class DiscordBan(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command()
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str="-"):
        await member.ban(reason=reason)

        embed = discord.Embed(
            title="Ban Notice",
            description=f"{member.mention} has been banned by {interaction.user.mention}!"
        )
        embed.add_field(
            name="Reason",
            value=reason
        )
        await interaction.response.send_message(embed=embed)
        await member.send(embed=embed)

    @app_commands.command()
    @app_commands.checks.has_permissions(ban_members=True)
    async def unban(self, interaction: discord.Interaction, member: discord.Member, reason: str="No reasons given!"):
        await member.unban(reason=reason)

        embed = discord.Embed(
            title="Unban Notice",
            description=f"{member.mention} has been unbanned by {interaction.user.mention}!"
        )
        embed.add_field(
            name="Reason",
            value=reason
        )
        await interaction.response.send_message(embed=embed)
        await member.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(DiscordBan(bot))