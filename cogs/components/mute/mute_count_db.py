import discord

from ..sql_connect import *

def add_mute_count_db(guild: discord.Guild, member: discord.Member):
    cursor.execute(f"SELECT mute_count FROM user_mute WHERE guild_id = {guild.id} AND user_id = {member.id}")
    result = cursor.fetchone()
    if result is None:
        cursor.execute(f"INSERT INTO user_mute VALUES ({guild.id}, {member.id}, 1)")
    else:
        cursor.execute(f"UPDATE user_mute SET mute_count = mute_count + 1 WHERE guild_id = {guild.id} AND user_id = {member.id}")
    rates_db.commit()

def subtract_mute_count_db(guild: discord.Guild, member: discord.Member):
    cursor.execute(f"UPDATE user_mute SET mute_count = mute_count - 1 WHERE guild_id = {guild.id} AND user_id = {member.id}")
    cursor.execute(f"SELECT mute_count FROM user_mute WHERE guild_id = {guild.id} AND user_id = {member.id}")
    result = cursor.fetchone()
    if result[0] <= 0:
        cursor.execute(f"DELETE FROM user_mute WHERE guild_id = {guild.id} AND user_id = {member.id}")

    rates_db.commit()

def get_mute_count_db(guild: discord.Guild, member: discord.Member):
    cursor.execute(f"SELECT mute_count FROM user_mute WHERE guild_id = {guild.id} AND user_id = {member.id}")
    result = cursor.fetchone()
    return result[0]
