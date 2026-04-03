from flask import Flask, request, render_template, redirect, url_for, session, Blueprint
from flask_socketio import emit
import mysql.connector
from config import DBconnect
from static.py.utilities import fetchClasses, populateClass
import time
import threading
from decimal import Decimal
from datetime import date, timedelta, datetime


# Define the blueprint
map = Blueprint('map', __name__)

# Serve the HTML page with the map
@map.route('/')
def index():
    populateClass()
    #Find an active expedition for the current class
    conn = DBconnect()
    with conn.cursor() as cursor:
        cursor.execute('''SELECT TripID FROM ActiveExpeditions WHERE ActiveTrip = 1 
                       AND TripID IN (
                       SELECT TripID 
                       FROM Stops
                       WHERE classID = %s)''', (session.get('selectedClassID'),))
        activeExpo = cursor.fetchone()
    session['activeExpedition'] = activeExpo
    #Assigns the message value
    if activeExpo != None:
        message = None
    else:
        message = (f"No active Expedition for {session.get('selectedClass')}")

    return render_template('Teacher Features/map.html',
                           username=session['user'], 
                           classes=fetchClasses(), 
                           selectedClass=session.get('selectedClass'),
                           message = message)

# Background thread to simulate real-time GPS data updates
def gps_data_update():
    while True:
        time.sleep(2)  # Adjust as needed

# Start the GPS update thread
thread = threading.Thread(target=gps_data_update, daemon=True)
thread.start()

# Define SocketIO event handler for new coordinates
def handle_new_coordinate(data):
    conn = DBconnect()
    try:
        if session.get('activeExpedition'):
            with conn.cursor(dictionary=True) as cursor:
                # Fetch coordinates from database
                cursor.execute('''SELECT latitude, longitude FROM TrackerData WHERE latitude IS NOT NULL AND longitude IS NOT NULL AND TripID = %s''', session.get('activeExpedition'))
                tracker_data = [{'lat': row['latitude'], 'lng': row['longitude'], 'type': 'TrackerData'} for row in cursor.fetchall()]

                cursor.execute('''SELECT latDes AS latitude, longDes AS longitude FROM Stops WHERE latDes IS NOT NULL AND longDes IS NOT NULL AND TripID = %s''', session.get('activeExpedition'))
                stops_data = [{'lat': row['latitude'], 'lng': row['longitude'], 'type': 'Stops'} for row in cursor.fetchall()]

                cursor.execute('''SELECT latitude, longitude FROM TrackerData WHERE ID = (SELECT MAX(ID) FROM TrackerData WHERE latitude IS NOT NULL AND longitude IS NOT NULL AND TripID = %s) AND TripID = %s''', (session.get('activeExpedition')[0], session.get('activeExpedition')[0]))
                recent = cursor.fetchone()
                
                user_location = [{'lat': recent['latitude'], 'lng': recent['longitude'], 'type': 'userLocation'}] if recent else []


                all_coordinates = tracker_data + stops_data + user_location

                #Fetch Expedition Stats
                cursor.execute('''SELECT * FROM ExpeditionStats WHERE TripID = %s''', session.get('activeExpedition'))
                expeditionStats = cursor.fetchall()
                
                expeditionStats = [
                    [
                        stat['TripID'],
                        stat['Date'].isoformat() if isinstance(stat['Date'], date) else stat['Date'],
                        int(stat['ElapsedTime']),
                        float(stat['DistanceWalked']) if isinstance(stat['DistanceWalked'], Decimal) else stat['DistanceWalked'],
                        float(stat['AveragePace']) if isinstance(stat['AveragePace'], Decimal) else stat['AveragePace']
                    ]
                    for stat in expeditionStats
                ]

                #Fetch last updated
                cursor.execute('''
                    SELECT time 
                    FROM TrackerData 
                    WHERE ID = (SELECT MAX(ID) FROM TrackerData) 
                    AND tripID = %s;
                ''', (session.get('activeExpedition')))

                lastUpdated = cursor.fetchone()
                
                if lastUpdated:
                    lastUpdatedTime = lastUpdated['time']
                    current_time = datetime.now().strftime("%H%M%S")

                    time1 = datetime.strptime(str(lastUpdatedTime), "%H:%M:%S")
                    time2 = datetime.strptime(current_time, "%H%M%S")

                    timeDifference = (time2 - time1).total_seconds()
                else:
                    timeDifference = None                    
                # Emit all coordinates at once
                emit('location_update', {'coordinates': all_coordinates,
                                         'expeditionStats' : expeditionStats,
                                         'timeDifference' : timeDifference}, broadcast=True)
    except mysql.connector.Error as e:
        print(f"Database query error: {e}")
    finally:
        conn.close()
