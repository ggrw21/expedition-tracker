from flask import Flask, request, render_template, redirect, url_for, session, Blueprint
from static.py.utilities import fetchClasses, populateClass
from config import DBconnect
import random

createClass = Blueprint('createClass', __name__)

@createClass.route("/create-class", methods=['GET', 'POST'])
def create_class():
    #If the form has been posted
    if request.method == 'POST':
        #Insert a new record into Classes
        className, awardType = request.form.get('className'), request.form.get('awardType')
        #Prevent non-expected values
        if awardType in ['Bronze', 'Silver', 'Gold']:
            conn = DBconnect()
            with conn.cursor() as cursor:
                #Loop until a unique code is found
                while True:
                    code = random.randint(100000,999999)
                    cursor.execute('''SELECT * FROM Classes WHERE JoinID = %s''', (code,))
                    if cursor.fetchone() == None:
                        break
                cursor.execute('''INSERT INTO Classes (AwardType, ClassName, TeacherID, JoinID, TrackerID)
                            VALUES (%s, %s, %s, %s, %s)''', (awardType, className, session['user'], code, None )) 
                conn.commit()
            #Redirect with success message
            return redirect(url_for('createClass.create_class', message='Successfully Created Class'))
        else:
            return redirect(url_for('createClass.create_class', error_message='Error Creating Class'))
    return render_template("Teacher Features/createClass.html", username=session['user'], classes=fetchClasses(), 
                           message=request.args.get('message'), selectedClass=session.get('selectedClass') or None)



if __name__ == '__main__':
    createClass.run(debug=True)