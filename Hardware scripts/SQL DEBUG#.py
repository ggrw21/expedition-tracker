import sqlite3
import mysql
from utilities import connect_to_mysql
import mysql.connector

#conn = sqlite3.connect("/home/daybroken/Desktop/NEA/myDatabase.db")
#cursor = conn.cursor()
#cursor.execute("""INSERT INTO data (id, latitude, longitude, cog) VALUES (1, 0, 0, 0)""")
#cursor.execute("""SELECT * FROM data""")
conn = connect_to_mysql()
with conn.cursor() as cursor:
    cursor.execute("""
            SELECT Stops.TripID
            FROM Stops
            JOIN ActiveExpeditions ON Stops.TripID = ActiveExpeditions.TripID
            WHERE Stops.TrackerID = %s
            AND ActiveExpeditions.ActiveTrip = TRUE
            """, (123456,))
    tripid = cursor.fetchone()[0]
    cursor.execute('''UPDATE ActiveExpeditions SET ActiveTrip = 0 WHERE TripID = %s'''(int(tripid),))
cursor.close()
conn.commit()
