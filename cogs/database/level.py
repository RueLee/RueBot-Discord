import discord
import nltk
from discord.ext import commands

from ..components.sql_connect import get_db_connection
from ..components.mute.mute_count_db import *

GUILD_WHITELIST_ID = [799809645585498142, 762191678240325662]
ROLE_HIERARCHY_WHITELIST_GUILD_ID = [799809645585498142]
ROLE_HIERARCHY = {}

class Level(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        nltk.download("punkt_tab")

    def compute_points(self, message: str, point_deduction: int) -> float:
        """
        Computes a point based on how many words a user sent in a single message.
        :param message: The message sent to discord. This will tokenize the string and return the length of the tokenized
        result. More sentences does not necessarily mean more points.
        :param point_deduction: The point scale deduction. Players who gets muted (or banned) by staff, their value will add to 1.
        The higher the value, the less point it has to give to the player.
        However, to give players opportunity to compensate deduction, whether to learn from their mistakes (without being stubborn),
        users are given a warning without any penalties. If he/she ends up scoring more than 1, the deduction takes effect.
        :return:
        """
        formula = (4 * len(nltk.word_tokenize(message)) ** 0.5) / (max(1, point_deduction))
        return formula

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.guild.id not in GUILD_WHITELIST_ID:
            return

        conn = get_db_connection()

        with conn.cursor() as cursor:
            guild_id = message.guild.id
            guild_name = message.guild.name
            guild_created = message.guild.created_at.date()

            # FIXME: Redundant call on guild
            cursor.execute(
                """
                INSERT INTO guild (guild_id, guild_name, date_created)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE guild_name = %s
                """,
                (guild_id, guild_name, guild_created, guild_name))

            user_id = message.author.id
            user_name = message.author.name
            user_join_date = message.author.created_at
            cursor.execute(
                """
                INSERT INTO guild_user (user_id, user_name, join_date)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE user_name = %s
                """,
                (user_id, user_name, user_join_date, user_name))

            conn.commit()
            update_user_mute(guild_id, user_id, date_rollback=False)

            cursor.execute(
                """
                SELECT * FROM level
                WHERE guild_id = %s AND user_id = %s
                """,
                (guild_id, user_id))
            result = cursor.fetchone()
            if result is None:
                curr_lvl = 0
                curr_role = None
                exp = 0
                exp_level_up = 100
                cursor.execute(
                    """
                    INSERT INTO level (guild_id, user_id, level, exp, exp_level_up)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (guild_id, user_id, curr_lvl, exp, exp_level_up))
            else:
                curr_lvl = result[2]
                curr_role = result[3]
                exp = result[4]
                exp_level_up = result[5]

                mute_score = get_mute_count(message.guild.id, message.author.id)
                if mute_score is None:
                    mute_score = 0

                exp += self.compute_points(message.content, mute_score[0])

            cursor.execute(
                """
                UPDATE level SET exp = %s
                WHERE guild_id = %s AND user_id = %s
                """,
                (exp, guild_id, user_id))
            if exp < exp_level_up:
                conn.commit()
                return

            curr_lvl += 1
            new_exp_level_up = 50 * curr_lvl ** 2 + 100 * curr_lvl + 50

            exp -= exp_level_up

            if curr_lvl in ROLE_HIERARCHY.keys() and guild_id in ROLE_HIERARCHY_WHITELIST_GUILD_ID:
                if curr_role is not None:
                    await message.author.remove_roles(curr_role)
                curr_role = discord.utils.get(message.guild.roles, name=ROLE_HIERARCHY[curr_lvl])
                await message.author.add_roles(curr_role)

            cursor.execute(
                """
                UPDATE level SET level = %s, role = IF(role IS NOT NULL, %s, NULL), exp = %s, exp_level_up = %s
                WHERE guild_id = %s AND user_id = %s
                """,
                (curr_lvl, curr_role, exp, new_exp_level_up, guild_id, user_id))

            await message.channel.send(f"{message.author.mention} has leveled up to {curr_lvl}!")

            conn.commit()

    @commands.command()
    async def level(self, interaction: discord.Interaction):
        conn = get_db_connection()

        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(
                """
                SELECT level FROM level
                WHERE user_id = %s
                """,
                (interaction.user.id))
            result = cursor.fetchone()
            await interaction.response.send_message(f"{interaction.user.mention}: Level {result[0]}")

async def setup(bot: commands.Bot):
    await bot.add_cog(Level(bot))