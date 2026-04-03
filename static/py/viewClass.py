from flask import Flask, request, render_template, redirect, url_for, session, Blueprint
from config import DBconnect
from static.py.utilities import fetchClasses, populateClass
import random
import sys

viewClass = Blueprint('viewClass', __name__)

@viewClass.route("/view-class", methods=['GET', 'POST'])
def view_class():
    removeStudents()
    populateClass()
    StudentData = fetchStudentData(session.get('selectedClassID'), request.form.get('dropdown'))
    #Change the floats and integers into a more user friendly format
    ProcessedStudentData = [
            (user, "Complete" if status == 1 else "Incomplete", 
            f"{score1 * 100:.0f}%", f"{score2 * 100:.0f}%", f"{score3 * 100:.0f}%")
            for user, status, score1, score2, score3 in StudentData
        ]
    return render_template("Teacher Features/viewClass.html",
                           username=session['user'], 
                           classes=fetchClasses(), 
                           message=request.args.get('message'), 
                           selectedClass=session.get('selectedClass'),
                            StudentData=ProcessedStudentData,
                            selected_filter = request.form.get('dropdown'))


def removeStudents(): 
    #Check if there is a POST request
    if request.method == "POST":
        if request.form.get('action') == "removeStudent":
            selected_users = request.form.getlist('selected_users')
            #Iterate through the selected users
            for user in selected_users:
                conn = DBconnect()
                #Remove each user's record from the table
                with conn.cursor() as cursor:
                    cursor.execute('''DELETE FROM StudentData WHERE userID = %s''', (user,))
                conn.commit()


def fetchStudentData(classID, filter):
    #Fetch all studentdata where class is the ClassID
    conn = DBconnect()
    with conn.cursor() as cursor:
        if filter == 'A-Z':
            cursor.execute('''SELECT userID, Expedition, Volunteering, Physical, Skills FROM StudentData WHERE ClassID = %s ORDER BY userID ASC''', (classID,))
        elif filter == 'Expedition Complete':
            cursor.execute('''SELECT userID, Expedition, Volunteering, Physical, Skills FROM StudentData WHERE ClassID = %s ORDER BY Expedition DESC''', (classID,))
        elif filter == 'Volunteering':
            cursor.execute('''SELECT userID, Expedition, Volunteering, Physical, Skills FROM StudentData WHERE ClassID = %s ORDER BY Volunteering DESC''', (classID,))
        elif filter == 'Physical':
            cursor.execute('''SELECT userID, Expedition, Volunteering, Physical, Skills FROM StudentData WHERE ClassID = %s ORDER BY Physical DESC''', (classID,))
        elif filter == 'Skills':
            cursor.execute('''SELECT userID, Expedition, Volunteering, Physical, Skills FROM StudentData WHERE ClassID = %s ORDER BY Skills DESC''', (classID,))
        else:
            cursor.execute('''SELECT userID, Expedition, Volunteering, Physical, Skills FROM StudentData WHERE ClassID = %s''', (classID,))
        StudentData = cursor.fetchall()
    return StudentData


    
if __name__ == '__main__':
    viewClass.run(debug=True)