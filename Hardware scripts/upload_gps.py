import mysql.connector
import time
import serial
import sys
from utilities import connect_to_mysql, getTrackerID
import sqlite3

# Local buffer for storing coordinates when the connection is lost
offline_data = []

# Function to save data locally when connection is lost
def save_offline_data(data):
    offline_data.append(data)
    print("Data saved locally due to lost connection.")

# Function to upload offline data when connection is restored
def upload_offline_data(conn):
    global offline_data
    if offline_data:
        cursor = conn.cursor()
        for data in offline_data:
            sql = "INSERT INTO TrackerData (TripID, classID, time, course_over_ground, latitude, longitude) VALUES (%s, %s, %s, %s, %s, %s)"
            cursor.execute(sql, data)
        conn.commit()
        offline_data = []  # Clear the offline data after uploading
        print("Offline data uploaded successfully.")

# Read GPS data from the serial port and parse the data if it starts with $GPRMC
def read_serial(port='/dev/ttyUSB1'):
    while True:
        try:
            with serial.Serial(port, 9600, timeout=1) as ser:
                while True:
                    data = ser.readline().decode().strip()
                    if data.startswith('$GPRMC'):
                        course, latitude, longitude = split_gprmc(data)
                        if latitude is None and longitude is None:
                            print('Coords None')
                            continue
                        else:
                            print("Data found")
                            time.sleep(3)
                            return course, latitude, longitude
                    else:
                        print('No data found')
        except:
            print("Couldn't connect to port")
            pass

# Extract the longitude, latitude and course over ground from the $GPRMC data
def split_gprmc(sentence):
    fields = sentence.split(',')
    if len(fields) < 12:
        return None, None, None
    if fields[2] != 'A':
        return None, None, None
    latitude = convert_lat_lon(fields[3], fields[4])
    longitude = convert_lat_lon(fields[5], fields[6])
    course = (fields[8]) 
    return course, latitude, longitude

# Convert coordinates from degrees and decimal minutes format to decimal degree format
def convert_lat_lon(coord, hemisphere):
    degrees = float(coord[:2])
    minutes = float(coord[2:])
    decimal_degrees = degrees + minutes / 60.0
    if hemisphere == 'S' or hemisphere == 'W':
        decimal_degrees = -decimal_degrees
    return decimal_degrees

# Write the value to a local CSV file to be used by the LED HAT script
def write_values(lat,long,course):
    connection = sqlite3.connect("/home/daybroken/Desktop/NEA/myDatabase.db")
    cursor = connection.cursor()
    cursor.execute("""UPDATE data SET LAT = ?, LONG = ?, COG = ? WHERE id = ?""", (lat, long, course, 1))
    connection.commit()
    connection.close()

def main():
    # Fetch the TripID and ClassID from the stops table
    conn = None
    while not conn:
        try:
            conn = connect_to_mysql()  # Attempt to connect to the MySQL database
        except mysql.connector.Error as e:
            print(f"Connection error: {e}")
            time.sleep(5)  # Wait before retrying
    
    with conn.cursor() as cursor:
        cursor.execute(""" 
        SELECT Stops.TripID, Stops.ClassID
        FROM Stops
        JOIN ActiveExpeditions ON Stops.TripID = ActiveExpeditions.TripID
        WHERE Stops.TrackerID = %s
        AND ActiveExpeditions.ActiveTrip = TRUE;
        """,(getTrackerID(),))
        result = cursor.fetchall()
    
    try:
        # Assign the TripID and classID to variables
        classID = result[0][1]
        TripID = result[0][0]
    except:
        # If there are no stops in the table it will quit
        print('Stops not defined')
        sys.exit()

    while True:
        current_time = time.strftime("%H:%M:%S", time.localtime())
        course, lat, long = read_serial()
        
        if conn:
            try:
                cursor = conn.cursor()
                sql = "INSERT INTO TrackerData (TripID, classID, time, course_over_ground, latitude, longitude) VALUES (%s, %s, %s, %s, %s, %s)"
                val = (TripID, classID, current_time, course, lat, long)
                cursor.execute(sql, val)
                conn.commit()
                cursor.close()
                write_values(lat, long, course)
            except mysql.connector.Error:
                print("Connection lost, saving data locally.")
                save_offline_data((TripID, classID, current_time, course, lat, long))
                conn = None  # Set connection to None to trigger reconnection logic
        else:
            print("Attempting to reconnect...")
            try:
                conn = connect_to_mysql()
                upload_offline_data(conn)  # Upload saved data if connection is restored
            except mysql.connector.Error as e:
                print(f"Error reconnecting: {e}")
                time.sleep(5)  # Wait before retrying

if __name__ == "__main__":
    main()
