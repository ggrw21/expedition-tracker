import math
import time
import mysql.connector
import os
import sys
#from utilities import connect_to_mysql, getTrackerID
import sqlite3
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


def _require_env(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _get_ssl_ca_path():
    configured_path = os.getenv("MYSQL_SSL_CA")
    if configured_path:
        return configured_path

    repo_cert = BASE_DIR / "ca.pem"
    if repo_cert.exists():
        return str(repo_cert)

    if os.name == 'posix':
        return '/home/daybroken/Desktop/NEA/ca.pem'
    if os.name == 'nt':
        return r"G:\Other computers\Mac\Year12\CS\NEA\Iterations\Resources\ca.pem"
    return None

def connect_to_mysql():
    while True:
        try:
            ssl_ca = _get_ssl_ca_path()

            # Connect to the MySQL database and specify the database
            mydb = mysql.connector.connect(
                host=os.getenv("MYSQL_HOST", "tracker-db-nea-tracker.h.aivencloud.com"),
                user=_require_env("MYSQL_USER"),
                password=_require_env("MYSQL_PASSWORD"),
                port=int(os.getenv("MYSQL_PORT", "21950")),
                database=os.getenv("MYSQL_DATABASE", "defaultdb"),
                ssl_ca=ssl_ca
            )
            print("Connected to MySQL!")
            return mydb
        except mysql.connector.Error as e:
            print("Error Connecting, retrying...")
            print(f"Error: {e}")
            time.sleep(3)

def getTrackerID():
    return 123456



def haversine(latPos, longPos, latDes, longDes):
    latPos, longPos, latDes, longDes = map(math.radians, [latPos, longPos, latDes, longDes])
    dlat = latDes - latPos
    dlong = longDes - longPos
    a = math.sin(dlat/2)**2 + math.cos(latPos) * math.cos(latDes) * math.sin(dlong/2)**2
    c = 2* math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = 6371 * c * 1000
    return distance

while True:
    time.sleep(5)
    #Find active tripID
    conn = connect_to_mysql()
    with conn.cursor() as cursor:
        cursor.execute("""
        SELECT Stops.TripID
        FROM Stops
        JOIN ActiveExpeditions ON Stops.TripID = ActiveExpeditions.TripID
        WHERE Stops.TrackerID = %s
        AND ActiveExpeditions.ActiveTrip = TRUE
        LIMIT 1
        """, (getTrackerID(),))

        tripID = cursor.fetchall()[0][0]

    #Get todays date
    date = datetime.now().strftime("%Y-%m-%d")

    #Get the seconds between the first record time and time now
    with conn.cursor() as cursor:
        cursor.execute('SELECT time FROM TrackerData WHERE ID = (SELECT MIN(ID) FROM TrackerData WHERE TripID = %s) AND TripID = %s', (tripID, tripID))
        firsttime = cursor.fetchall()
    seconds_in_day = (datetime.now() - datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)).seconds
    ElapsedTime = seconds_in_day - firsttime[0][0].seconds

    with conn.cursor() as cursor:
        cursor.execute('SELECT latitude, longitude FROM TrackerData WHERE latitude IS NOT NULL AND longitude IS NOT NULL AND TripID = %s', (tripID,))
        coords = cursor.fetchall()

    #Iterate through all coordinates and get total distance
    DistanceWalked = 0
    for i in range(len(coords) - 1):
        lat1, lon1 = coords[i]
        lat2, lon2 = coords[i + 1]
        
        distance = haversine(lat1, lon1, lat2, lon2)
        #Only log distance if 
        if distance > 0.5:
            DistanceWalked += distance

    AveragePace = DistanceWalked/ElapsedTime

    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM ExpeditionStats WHERE TripID = %s',(tripID,))
        row = cursor.fetchall()
        if row == []:
            cursor.execute('INSERT INTO ExpeditionStats (TripID, Date, ElapsedTime, DistanceWalked, AveragePace) VALUES (%s, %s, %s, %s, %s)', (tripID, date, ElapsedTime, DistanceWalked, AveragePace))
        else:
            cursor.execute('UPDATE ExpeditionStats SET ElapsedTime = %s, DistanceWalked = %s, AveragePace = %s WHERE TripID = %s', (ElapsedTime, DistanceWalked, AveragePace, tripID))
        conn.commit()




        

