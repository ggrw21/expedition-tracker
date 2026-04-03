from flask import Flask, request, render_template, redirect, url_for, session, Blueprint
from config import DBconnect

studentDashboard = Blueprint('studentDashboard', __name__)

@studentDashboard.route("/student-dashboard", methods=['GET', 'POST'])
def dashboard():
    print(session)
    #If the form has been posted call update stats function
    if request.method == "POST":
        updateStats()
    return render_template('Student Features/studentDashboard.html', activity = fetchStats(session['user']))

#Clear the users session
@studentDashboard.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('user', None)
    return redirect('/login')

def updateStats():
    conn = DBconnect()
    #Insert form values into DB to the logged in users record
    with conn.cursor() as cursor:
        #Turn each integer into a float before inserting
        cursor.execute('''UPDATE StudentData SET Volunteering = %s, Physical = %s, Skills = %s WHERE UserID = %s''', 
                       (float(request.form.get('volunteering'))/100, float(request.form.get('physical'))/100, 
                        float(request.form.get('skills'))/100, session['user']),)
    conn.commit()

def fetchStats(userID):
    #Select the activity floats for the logged in user
    conn = DBconnect()
    with conn.cursor() as cursor:
        cursor.execute('''SELECT Volunteering, Physical, Skills FROM StudentData WHERE userID = %s ''', (userID,))
        StudentData = cursor.fetchone()
    conn.commit()
    StudentData = [student * 100 for student in StudentData]
    return StudentData


if __name__ == '__main__':
    studentDashboard.run(debug=True)