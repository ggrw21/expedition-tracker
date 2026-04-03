from flask import Flask, request, render_template, redirect, url_for, session, Blueprint
from config import DBconnect
from static.py.utilities import fetchClasses, populateClass
import random
import sys

pairTracker = Blueprint('pairTracker', __name__)

@pairTracker.route('/pair-tracker', methods=['GET', 'POST'])
def dashboard():
    message, error_message = None, None
    populateClass()
    if checkClass():
        message = 'This class already has a paired tracker. Pairing a new tracker will automatically unpair the existing one.'
    #If the user submits a code it gets checked
    if request.method == 'POST':
        trackerID = checkCode()
        #If tracker code is valid
        if trackerID != None:
            conn = DBconnect()
            #See if a record with this pairing code already exists
            with conn.cursor() as cursor:
                cursor.execute('''SELECT * FROM Classes WHERE TrackerID = %s''', (trackerID))
                fetchone = cursor.fetchone()
            #If its unique then set the trackerID to current class and paired to True
            if fetchone == None:
                with conn.cursor() as cursor:
                    cursor.execute('''UPDATE Classes SET TrackerID = %s WHERE classID = %s''', (trackerID[0], session.get('selectedClassID')))
                    cursor.execute('''UPDATE TrackerPair SET Paired = 1 WHERE TrackerID = %s''', (trackerID[0],))
                    conn.commit()
                    message = 'Successfully Paired Tracker!'
            else:
                error_message = 'Error'
        else:
            error_message = 'Error'

    return render_template('Teacher Features/pairTracker.html', classes=fetchClasses(), selectedClass=session.get('selectedClass') or None, message=message, error_message=error_message)

def checkCode():
    conn = DBconnect()
    code = request.form.get('trackerCode')
    #Select the trackerID of the code inputted
    with conn.cursor() as cursor:
        cursor.execute('''SELECT TrackerID FROM TrackerPair WHERE TrackerCode = %s''', (code,))
        trackerID = cursor.fetchone()
    return trackerID

def checkClass():
    conn = DBconnect()
    #Check if class has a tracker paired
    with conn.cursor() as cursor:
        cursor.execute('''SELECT TrackerID FROM Classes WHERE classID = %s''', (session.get('selectedClassID'),))
        trackerID = cursor.fetchone()
    if trackerID[0] == None:
        return False
    return True

if __name__ == '__main__':
    pairTracker.run(debug=True)