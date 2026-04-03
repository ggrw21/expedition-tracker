from flask import Flask, request, render_template, redirect, url_for, session, Blueprint
import mysql.connector
import os
import hashlib
import random
import subprocess
from config import DBconnect
import time

login = Blueprint('loginsystem', __name__)

@login.route('/')
#If user is logged in, redirect to home page else sign up page
def index():
    if check_if_logged_in():
        return redirect('view-class')
    return render_template('Login System/index.html')

@login.route('/submit', methods=['POST'])
def sign_up():
    #Validates the user submitted the form
    if request.form['action'] == "Submit":
        return signing_up()
    else:
        return "Invalid action"

@login.route('/login', methods=['GET', 'POST'])
def login_page():
    #If the user is logged in already redirect to home
    if check_if_logged_in():
        return redirect('view-class')
    #If they submit the login form call logging_in()
    if request.method == 'POST':
        if request.form.get('action') == "Submit":
            return logging_in()
        else:
            return "Invalid action"
    return render_template('Login System/login.html')


@login.route('/forgot', methods=['GET', 'POST'])
def reset_page():
    #If the user is logged in already redirect to home
    if check_if_logged_in():
        return redirect('view-class')
    if request.method == 'POST':
    #If the user requested a password link call the reset_pw() function
        if request.form.get('action') == "Send Link":
            return reset_pw(request.form['email'].lower())
        else:
            return "Invalid action"
    return render_template('Login System/forgotPW.html', reset_message="", show_form=False)


#If user clicks on an email-confirm link store their code as a session variable
@login.route('/email-confirm/<int:code>')
def email_confirm(code):
    session['inpResetCode'] = code
    return render_template('Login System/resetPW.html')
    
@login.route('/newPW', methods=['GET','POST'])
def reset_password():
    try:
        #Check if the users reset code matches the generated one
        if time.time() - session['send_code_time'] > 900:
            return render_template('Login System/resetPW.html', red_reset_message="Code Expired", show_form=False)
        if session['inpResetCode'] == int(session['reset_code']):
            conn = DBconnect()
            #If it does then update the database with the new password
            with conn.cursor() as cursor:
                cursor.execute('''UPDATE LoginTable SET HashPW = (%s) WHERE email = %s''', (hash(request.form.get('newPW')),session['reset_email'],))
            conn.commit()
            session.clear()
            return render_template('Login System/resetPW.html', reset_message="Successfully Reset", show_form=False)
        return render_template('Login System/resetPW.html', red_reset_message="Invalid Code", show_form=False)
    #If the users link doesnt contain a reset code then redirect to home.
    except:
        return render_template('Login System/index.html')

def logging_in():
    conn = DBconnect()
    with conn.cursor() as cursor:
        #Fetches the HashPW of the users inputted email
        cursor.execute('''SELECT hashPW FROM LoginTable WHERE email = %s''', (request.form['email'].lower(),))
        fetched_pw = cursor.fetchone()
    #If users Hashed PW matches the fetched one
    if fetched_pw and hash(request.form['password']) == fetched_pw[0]:
        #Change the user session to the users email so they stay logged in
        clear_session()
        session['user'] = request.form['email'].lower()
        return redirect('/view-class')
    else:
        return render_template('Login System/login.html', red_error_message='Password Incorrect or Account does not exist.', show_form=False)

def reset_pw(email):
    #If the users email exists in the database
    if check_if_account(email):
        #Store the reset email and a random reset code as session variables
        session['reset_email'] = email
        session['reset_code'] = str(random.randint(100000, 999999))
        session['send_code_time'] = time.time()
        #Send the user an email
        subprocess.run(["python3",'/Users/daybroken/Documents/Year12/CS/NEA/Iterations/Prototype2/static/py/email_link.py'] + [session['reset_email'], session['reset_code']])
        return render_template('Login System/forgotPW.html', reset_message="Code has been sent", submitted_email=email, show_form=False)
    else:
        return render_template('Login System/forgotPW.html', red_reset_message="Account not found", show_form=False)


def signing_up():
    #Check if the account already exists in the database
    created_check = check_if_account(request.form['email'].lower())
    if not created_check:
        conn = DBconnect()
        #If its not created already insert the users form values as a new record
        with conn.cursor() as cursor:
            cursor.execute('''INSERT INTO LoginTable (email, hashPW, AccountType) VALUES (%s, %s, %s)''', (request.form['email'].lower(), hash(request.form['password']), request.form['account_type']))
            conn.commit()
        clear_session()
        session['user'] = request.form['email'].lower()
        return redirect('/view-class')
    else:
        return redirect('/login')

def hash(string):
    return hashlib.sha256(string.encode()).hexdigest()

def check_if_account(email):
    conn = DBconnect()    
    #Selects the number of entreis with the same email as the parameter, if its greater than 0 return True
    with conn.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM LoginTable WHERE email = %s", (email,))
        result = cursor.fetchone()
        return result[0] > 0

def check_if_logged_in():
    user = session.get('user')
    if user is None:
        return False
    else:
        return True

def clear_session():
    for key in list(session.keys()):
        print(key)
        session.pop(key)

if __name__ == '__main__':
    login.run(debug=True)

    