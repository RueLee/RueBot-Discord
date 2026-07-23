import asyncio

import discord
from discord import app_commands
from discord.ext import commands

from ..components.mute.mute_count_db import *

def convert_minutes(minutes_input: float) -> str:
    total_seconds = int(minutes_input * 60)

    hours = total_seconds // 3600
    remaining_seconds = total_seconds % 3600
    minutes = remaining_seconds // 60
    seconds = remaining_seconds % 60

    formatted_time = f"{hours:02d}hr {minutes:02d}min {seconds:02d}sec"
    return formatted_time

class DiscordMute(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mute_tasks = {}

    @app_commands.command()
    @app_commands.checks.has_permissions(mute_members=True)
    async def mute(self, interaction: discord.Interaction, member: discord.Member, duration: float, message: str="-"):
        muted_role = discord.utils.get(interaction.guild.roles, name="Muted")
        if muted_role in member.roles:
            await interaction.response.send_message("This user is already muted!", ephemeral=True)
            return

        if duration <= 0:
            await interaction.response.send_message("Please enter a duration greater than 0!", ephemeral=True)
            return

        verified_role = discord.utils.get(interaction.guild.roles, name="Verified")
        await member.remove_roles(verified_role)
        await member.add_roles(muted_role)

        converted_duration_str = convert_minutes(duration)
        embed = discord.Embed(
            title="Mute Notice",
            description=f"{member.mention} has been muted by {interaction.user.mention} for `{converted_duration_str}`!"
        )
        embed.add_field(
            name="Reason",
            value=message,
            inline=False
        )
        await interaction.response.send_message(embed=embed)
        await member.send(embed=embed)

        task = asyncio.create_task(self.unmute_after(interaction, member, duration, muted_role))
        self.mute_tasks[member.id] = task

        add_mute_count_db(interaction.guild, member)

    async def unmute_after(self, interaction: discord.Interaction, member: discord.Member, duration: float, muted_role: discord.Role):
        try:
            await asyncio.sleep(int(duration * 60))
            await member.remove_roles(muted_role)
            await member.send("You have been unmuted!")
        except asyncio.CancelledError:
            print(f"NOTICE: {member} was manually unmuted!")
            subtract_mute_count_db(interaction.guild, member)
        finally:
            self.mute_tasks.pop(member.id, None)

    @app_commands.command()
    @app_commands.checks.has_permissions(mute_members=True)
    async def unmute(self, interaction: discord.Interaction, member: discord.Member):
        muted_role = discord.utils.get(interaction.guild.roles, name="Muted")
        if muted_role not in member.roles:
            await interaction.response.send_message(f"`{member}` does not have an active mute!", ephemeral=True)
            return

        task = self.mute_tasks.pop(member.id)
        task.cancel()

        verified_role = discord.utils.get(interaction.guild.roles, name="Verified")
        await member.add_roles(verified_role)
        await member.remove_roles(muted_role)
        embed = discord.Embed(
            title="Unmute Notice",
            description=f"{member.mention} has been unmuted by {interaction.user.mention}!"
        )
        await interaction.response.send_message(embed=embed)
        await member.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(DiscordMute(bot))