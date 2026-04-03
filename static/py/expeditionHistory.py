from flask import Flask, request, render_template, redirect, url_for, session, Blueprint, jsonify
import mysql.connector
from config import DBconnect
from static.py.utilities import fetchClasses, populateClass

expoHistory = Blueprint('expoHistory', __name__)

@expoHistory.route('/expedition-history', methods=['GET', 'POST'])
def expedition_history():
    populateClass()
    conn = DBconnect()
    with conn.cursor() as cursor:
        # Select the inactive trips for the selected class
        cursor.execute('''SELECT TripID FROM ActiveExpeditions WHERE ActiveTrip = 0 
                       AND TripID IN (
                       SELECT TripID 
                       FROM TrackerData
                       WHERE classID = %s)''', (session.get('selectedClassID'),))
        expoHistory = cursor.fetchall()

        # Create a list to store the results
        expeditionData = []

        # Loop through each trip and check for corresponding date in ExpeditionStats
        for tripid in expoHistory:
            cursor.execute('''SELECT Date FROM ExpeditionStats WHERE TripID = %s''', (tripid[0],))
            date_result = cursor.fetchone()

            # If a date is found, pair it with the TripID, otherwise set it to None
            if date_result:
                expeditionData.append((date_result[0], tripid[0]))
            else:
                expeditionData.append((None, tripid[0]))

    return render_template('Teacher Features/expeditionHistory.html',
                           username=session['user'], 
                           classes=fetchClasses(),
                           selectedClass=session.get('selectedClass'),
                           expeditionData = expeditionData)

@expoHistory.route('/expedition-history/<int:trip_id>')
def expedition_historyPage(trip_id):
    conn = DBconnect()
    with conn.cursor(dictionary=True) as cursor:
        # Fetch coordinates from database
        cursor.execute('''SELECT latitude, longitude FROM TrackerData WHERE latitude IS NOT NULL AND longitude IS NOT NULL AND TripID = %s''', (trip_id,))
        tracker_data = [{'lat': row['latitude'], 'lng': row['longitude'], 'type': 'TrackerData'} for row in cursor.fetchall()]

        cursor.execute('''SELECT latDes AS latitude, longDes AS longitude FROM Stops WHERE latDes IS NOT NULL AND longDes IS NOT NULL AND TripID = %s''', (trip_id,))
        stops_data = [{'lat': row['latitude'], 'lng': row['longitude'], 'type': 'Stops'} for row in cursor.fetchall()]

        cursor.execute('''SELECT latitude, longitude FROM TrackerData WHERE ID = (SELECT MAX(ID) FROM TrackerData WHERE latitude IS NOT NULL AND longitude IS NOT NULL AND TripID = %s) AND TripID = %s''', (trip_id, trip_id))
        recent = cursor.fetchone()

        user_location = [{'lat': recent['latitude'], 'lng': recent['longitude'], 'type': 'userLocation'}] if recent else []

        global all_coordinates
        all_coordinates = tracker_data + stops_data + user_location

    return render_template('Teacher Features/HistoryMap.html', username=session['user'], selectedClass=session.get('selectedClass'))

@expoHistory.route('/get_array')
def get_array():
    return jsonify(all_coordinates)

if __name__ == '__main__':
    expoHistory.run(debug=True)
