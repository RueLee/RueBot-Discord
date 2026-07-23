import json

import discord
from discord import app_commands
from discord.ext import commands

VERIFICATION_CHANNEL_ID = 1524508477802676244
DATA_FILE = "verification-message.json"

class VerificationButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Verify", style=discord.ButtonStyle.green)
    async def verify(self, interaction: discord.Interaction, button: discord.Button):
        role = discord.utils.get(interaction.guild.roles, name="Verified")
        if role in interaction.user.roles:
            await interaction.response.send_message("You have already been verified!", ephemeral=True)
            return

        muted_role = discord.utils.get(interaction.guild.roles, name="Muted")
        if muted_role in interaction.user.roles:
            await interaction.response.send_message("You have an active mute! Try verifying again after your mute lifts!", ephemeral=True)
            return

        await interaction.user.add_roles(role)
        await interaction.user.send(f"You have been verified at server, {interaction.guild.name}!")

class Verification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        message_id = self.load_verification_message()
        if not message_id:
            return

        channel = self.bot.get_channel(VERIFICATION_CHANNEL_ID)
        if not channel:
            return

        try:
            message = await channel.fetch_message(message_id)
            view = VerificationButton()
            await message.edit(view=view)
            print("Reconnected to existing verification message.")
        except discord.NotFound:
            print("Verification message not found, please run /setup_verify again.")

    def load_verification_message(self):
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                f.close()
                return data.get("message_id", None)
        except FileNotFoundError:
            pass

    def save_verification_message(self, message_id):
        with open(DATA_FILE, "w") as f:
            json.dump({"message_id": message_id}, f)
            f.close()

    @app_commands.command()
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_verify(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Welcome to RueLee's Discord Server",
            description="By joining the server, you agree to behave! Players who violate any of these may constitute a warning, kick, or ban!",
            color=0x33ffbd,
        )
        embed.set_author(
            name=interaction.user.name,
            icon_url=interaction.user.avatar,
        )
        message = await interaction.response.send_message(embed=embed, view=VerificationButton())
        self.save_verification_message(message.id)

async def setup(bot: commands.Bot):
    await bot.add_cog(Verification(bot))