from flask import Flask
from flask_socketio import SocketIO
import os
from static.py.login import login
from static.py.createClass import createClass
from static.py.viewClass import viewClass
from static.py.studentDashboard import studentDashboard
from static.py.pairTracker import pairTracker
from static.py.utilities import utilities
from static.py.map import map, handle_new_coordinate
from static.py.expeditionHistory import expoHistory
from static.py.startExpedition import startExpedition


# Initialize the Flask app
app = Flask(__name__)

# Configure session and secret key
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')

if not app.config['SECRET_KEY']:
    raise RuntimeError("Missing required environment variable: FLASK_SECRET_KEY")

# Initialize SocketIO
socketio = SocketIO(app)

# Register blueprints
app.register_blueprint(login)
app.register_blueprint(createClass)
app.register_blueprint(viewClass)
app.register_blueprint(studentDashboard)
app.register_blueprint(pairTracker)
app.register_blueprint(utilities)
app.register_blueprint(map, url_prefix='/live-expedition')
app.register_blueprint(expoHistory)
app.register_blueprint(startExpedition)

# Register SocketIO event handlers
socketio.on_event('new_coordinate', handle_new_coordinate)

if __name__ == '__main__':
    socketio.run(app, debug=True)
