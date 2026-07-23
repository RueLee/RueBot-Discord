import discord
from discord import app_commands
from discord.ext import commands
import random

class Gambling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(description="Generates 5 normal and 1 mega numbers inspired from CA Lottery")
    @app_commands.describe(
        nums="Pick 5 numbers from 1-70. Separate with space to split numbers",
        mega="Pick a number from 1-26",
    )
    async def six_lottery(self, interaction: discord.Interaction, nums: str, mega: int):
        msg_error = "Correct Usage: `/six_lottery 5x<1-70> <1-26>`"
        nums = list(map(int, nums.split(" ")))
        nums.sort()

        if len(nums) != 5:
            await interaction.response.send_message(msg_error)
            return

        if mega > 26 or mega < 1:
            await interaction.response.send_message(msg_error)
            return

        standard_num = set(nums)

        if len(standard_num) != 5:
            await interaction.response.send_message(msg_error)
            return

        for num in standard_num:
            if num > 70 or num < 1:
                await interaction.response.send_message(msg_error)
                return

        rand_set = set()
        while len(rand_set) != 5:
            rand_set.add(random.randint(1, 70))

        rand_mega = random.randint(1, 26)
        rand_list = sorted(rand_set)

        matched = {}
        for i in range(len(nums)):
            matched[nums[i]] = nums[i]

        matched_counter = 0
        for i in range(len(nums)):
            if rand_list[i] in matched:
                matched_counter += 1

        is_mega_matched = False
        if mega == rand_mega:
            is_mega_matched = True

        await interaction.response.send_message(f"```"
                                                f"Your numbers: {nums}; Mega: {mega}\n"
                                                f"Resulting: {rand_list}; Mega: {rand_mega}\n\n"
                                                f"Matching numbers: {matched_counter}\n"
                                                f"Matched mega?: {is_mega_matched}"
                                                f"```")

    @app_commands.command(description="Randomizes number between 0-100%")
    async def howsmartis(self, interaction: discord.Interaction, message: str):
        percent_randomizer = round(random.random() * 100, 2)
        await interaction.response.send_message(f"{message} is {percent_randomizer}% smart!")

async def setup(bot: commands.Bot):
    await bot.add_cog(Gambling(bot))