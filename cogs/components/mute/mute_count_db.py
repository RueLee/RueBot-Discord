from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from ..sql_connect import get_db_connection

def add_mute_count(guild_id: int, member_id: int, days: int, hours: int, minutes: int, seconds: int):
    conn = get_db_connection()

    with conn.cursor() as cursor:
        scheduled_decrement = datetime.now() + relativedelta(months=3) + timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
        cursor.execute(
            """
            INSERT INTO user_mute (guild_id, user_id, mute_count, scheduled_decrement)
            VALUES (%s, %s, 1, %s)
            ON DUPLICATE KEY UPDATE
            mute_count = mute_count + 1,
            prev_scheduled_decrement = scheduled_decrement,
            scheduled_decrement = %s
            """,
            (guild_id, member_id, scheduled_decrement, scheduled_decrement))
        conn.commit()

def subtract_mute_count(guild_id: int, member_id: int):
    conn = get_db_connection()

    with conn.cursor() as cursor:
        cursor.execute(
            """
            UPDATE user_mute
            SET mute_count = mute_count - 1
            WHERE guild_id = %s AND user_id = %s
            """,
            (guild_id, member_id))
        conn.commit()

def delete_user_mute(guild_id: int, member_id: int):
    conn = get_db_connection()

    with conn.cursor() as cursor:
        cursor.execute(
            """
            DELETE FROM user_mute
            WHERE guild_id = %s AND user_id = %s
            """,
            (guild_id, member_id))
        conn.commit()

def update_user_mute(guild_id: int, member_id: int, date_rollback: bool):
    conn = get_db_connection()

    with conn.cursor() as cursor:
        mute_count = get_mute_count(guild_id, member_id)
        if mute_count is None:
            return

        target = 0
        if mute_count[0] <= target:
            delete_user_mute(guild_id, member_id)
        elif not date_rollback:
            cursor.execute(
                """
                UPDATE user_mute
                SET prev_scheduled_decrement = scheduled_decrement, scheduled_decrement = DATE_ADD(scheduled_decrement, INTERVAL 3 MONTH)
                WHERE guild_id = %s AND user_id = %s
                """,
                (guild_id, member_id))
            conn.commit()
        else:
            cursor.execute(
                """
                UPDATE user_mute
                SET scheduled_decrement = prev_scheduled_decrement, prev_scheduled_decrement = NULL
                WHERE guild_id = %s AND user_id = %s
                """,
                (guild_id, member_id))
            conn.commit()

def get_all_muted_user():
    conn = get_db_connection()

    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT *
            FROM user_mute
            """)
        result = cursor.fetchall()
        return result

def get_mute_count(guild_id: int, member_id: int):
    conn = get_db_connection()

    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT mute_count
            FROM user_mute
            WHERE guild_id = %s AND user_id = %s
            """,
            (guild_id, member_id))
        result = cursor.fetchone()
        return result

def get_decrement_date(guild_id: int, member_id: int):
    conn = get_db_connection()

    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT scheduled_decrement, prev_scheduled_decrement
            FROM user_mute
            WHERE guild_id = %s AND user_id = %s
            """,
            (guild_id, member_id))
        result = cursor.fetchone()
        return result
