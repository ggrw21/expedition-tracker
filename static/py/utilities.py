from flask import Flask, request, render_template, redirect, url_for, session, Blueprint
from config import DBconnect
import random
import sys

utilities = Blueprint('utilities', __name__)

# Clear the user's entire session
@utilities.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()  # Removes all items from the session
    return redirect('/login')

@utilities.route('/select-class', methods=['POST'])
def select_class():
    #Add the seleceted class as session variables
    session['selectedClass'] = request.form.get('selected_class')
    session['selectedClassID'] = request.form.get('selected_ID')
    return redirect(request.referrer)

def populateClass():
    #If teacher has no classes redirect to create class
    if not fetchClasses():
        return redirect('/create-class')
    if session.get('selectedClassID') == None:
        selectedClass, selectedClassID = fetchClasses()[0][0], fetchClasses()[0][1]
        session['selectedClass'] = selectedClass
        session['selectedClassID'] = selectedClassID

def fetchClasses():
    #Fetch all classes where teacher is the UserID
    conn = DBconnect()
    with conn.cursor() as cursor:
        cursor.execute('''SELECT ClassName, ClassID FROM Classes WHERE TeacherID = %s''', (session['user'],))
        classes = cursor.fetchall()
    return classes

if __name__ == '__main__':
    utilities.run(debug=True)