import os

import mysql.connector

rates_db = None
cursor = None

try:
    rates_db = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

    cursor = rates_db.cursor()
    print("Connection to Database Successful!")
except mysql.connector.Error as err:
    print(err)
finally:
    if rates_db:
        rates_db.close()