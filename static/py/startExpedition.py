from flask import Flask, request, render_template, redirect, url_for, session, Blueprint
from static.py.utilities import fetchClasses, populateClass
from config import DBconnect
import random

startExpedition = Blueprint('startExpedition', __name__)

@startExpedition.route("/start-expedition", methods=['GET', 'POST'])
def start_expedition():
    message = ''
    error_message = ''
    conn = DBconnect()
    #Selects any existing trips with the selected classID
    with conn.cursor() as cursor:
        cursor.execute('''SELECT TripID FROM ActiveExpeditions WHERE ActiveTrip = 1 
                       AND TripID IN (
                       SELECT TripID 
                       FROM Stops
                       WHERE classID = %s)''', (session.get('selectedClassID'),))
        activeExpo = cursor.fetchone()
    if activeExpo:
        error_message = 'Already active expedition'
    #If the form has been posted
    if request.method == 'POST' and not activeExpo:
        # Generate a unique TripID
        while True:
            conn = DBconnect()
            with conn.cursor() as cursor:
                trip_id = random.randint(100000, 999999)
                cursor.execute("SELECT EXISTS (SELECT 1 FROM Stops WHERE TripID = %s)", (trip_id,))
                exists = cursor.fetchone()[0]
                
                if not exists:
                    break
        conn = DBconnect()
        with conn.cursor() as cursor:
            #Check for tracker pair
            cursor.execute('''SELECT TrackerID FROM Classes WHERE ClassID = %s''', (session.get('selectedClassID'),))
            trackerID = cursor.fetchone()[0]
            if trackerID is None:
                error_message = 'No tracker paired to class'
            else:
                #Inserting co-ordinates
                cursor.execute('''INSERT INTO Stops (TripID, ClassID, latDes, longDes, TrackerID) VALUES (%s, %s, %s, %s, %s)''', (trip_id, session.get('selectedClassID'), request.form.get('start-lat'), request.form.get('start-lon'), trackerID))
                #If additional stops
                if request.form.getlist('stop-lat[]') and request.form.getlist('stop-lon[]'):
                    for lat, long in zip(request.form.getlist('stop-lat[]'), request.form.getlist('stop-lon[]')):
                        cursor.execute('''INSERT INTO Stops (TripID, ClassID, latDes, longDes, TrackerID) VALUES (%s, %s, %s, %s, %s)''', (trip_id, session.get('selectedClassID'), lat, long, trackerID))
                cursor.execute('''INSERT INTO Stops (TripID, ClassID, latDes, longDes, TrackerID) VALUES (%s, %s, %s, %s, %s)''', (trip_id, session.get('selectedClassID'), request.form.get('end-lat'), request.form.get('end-lon'), trackerID))
                cursor.execute('''INSERT INTO ActiveExpeditions VALUES (%s, %s)''',(trip_id, 1))
                message = 'Trip successfully started'
        conn.commit()
        conn.close()

    return render_template("Teacher Features/startExpedition.html", username=session['user'], classes=fetchClasses(), message=message, error_message=error_message, selectedClass=session.get('selectedClass') or None)



if __name__ == '__main__':
    startExpedition.run(debug=True)