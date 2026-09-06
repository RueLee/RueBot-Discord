import asyncio
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from ..components.mute.mute_count_db import *

def convert_minutes(minutes_input: float) -> int:
    total_seconds = int(minutes_input * 60)

    days = total_seconds // 86400
    remaining_seconds = total_seconds % 86400
    hours = total_seconds // 3600
    remaining_seconds = total_seconds % 3600
    minutes = remaining_seconds // 60
    seconds = remaining_seconds % 60

    return days, hours, minutes, seconds

class DiscordMute(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mute_tasks = {}
    
    # In the event of an outage, check if certain users have passed the date to decrement mute count
    @commands.Cog.listener()
    async def on_ready(self):
        all_muted_user = get_all_muted_user()
        if all_muted_user == []:
            return
        
        today_date = datetime.now()

        for user in all_muted_user:
            scheduled_decrement = user[3]
            if scheduled_decrement <= today_date:
                subtract_mute_count(user[0], user[1])
                update_user_mute(user[0], user[1], date_rollback=False)

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

        days, hours, minutes, seconds = convert_minutes(duration)
        embed = discord.Embed(
            title="Mute Notice",
            description=f"{member.mention} has been muted by {interaction.user.mention} for `{days:.2f}d {hours:.2f}hr {minutes:.2f}min {seconds:.2f}sec`!"
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

        add_mute_count(interaction.guild.id, member.id, days, hours, minutes, seconds)

    async def unmute_after(self, interaction: discord.Interaction, member: discord.Member, duration: float, muted_role: discord.Role):
        try:
            await asyncio.sleep(int(duration * 60))
            await member.remove_roles(muted_role)
            await member.send("You have been unmuted!")
        except asyncio.CancelledError:
            print(f"NOTICE: {member} was manually unmuted!")
            subtract_mute_count(interaction.guild.id, member.id)
            update_user_mute(interaction.guild.id, member.id, date_rollback=True)
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