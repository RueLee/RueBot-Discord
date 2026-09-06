import os

import mysql.connector

rates_db = None
cursor = None

def get_db_connection():
    if not rates_db.is_connected():
        rates_db.reconnect(attempts=3, delay=1)
    return rates_db

try:
    rates_db = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        autocommit=True
    )

    cursor = rates_db.cursor()
    print("Connection to Database Successful!")
except mysql.connector.Error as err:
    print(err)
finally:
    if rates_db:
        rates_db.close()
    if cursor:
        cursor.close()