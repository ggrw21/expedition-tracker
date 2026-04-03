import math
from rpi_ws281x import PixelStrip, Color
import time
import mysql.connector
import os
import sys
from utilities import connect_to_mysql, getTrackerID, Matrixs
import sqlite3 

# LED strip configuration
LED_COUNT = 64      
LED_PIN = 18          
LED_FREQ_HZ = 800000    
LED_DMA = 10          
LED_BRIGHTNESS = 125
LED_INVERT = False
LED_CHANNEL = 0

#Get the strip ready for writing
strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip.begin()

def calculate_bearing(lat1, lon1, lat2, lon2):
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    delta_lon = lon2_rad - lon1_rad
    y = math.sin(delta_lon) * math.cos(lat2_rad)
    x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lon)
    bearing_rad = math.atan2(y, x)
    bearing_deg = math.degrees(bearing_rad)
    bearing = (bearing_deg + 360) % 360
    return bearing

def compass_directions(bearing, COG):
    difference = bearing - COG
    difference %= 360
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW",]
    compdir = round(difference/45) % 8
    return(directions[compdir])

def display_array(strip, array):
    # Set arrow color (red)
    arrow_color = Color(255, 0, 0)
    # Loop through the 2D array and set the pixel colors
    for y in range(len(array)):
        for x in range(len(array[y])):
            if array[y][x] == 1:
                index = x + y * 8
                strip.setPixelColor(index, arrow_color)
    strip.show()
    
def turn_off_all_leds(strip):
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, Color(0,0,0))
    strip.show()


def write_stops():
    # Connect to the MySQL database
    mydb = connect_to_mysql()
    cursor = mydb.cursor()
    sql_query = "SELECT latDes, longDes FROM Stops;"
    cursor.execute(sql_query)
    rows = cursor.fetchall()
    cursor.close()
    mydb.close()
    
    # Connect to the SQLite database
    connection = sqlite3.connect("/home/daybroken/Desktop/NEA/myDatabase.db")
    sqlite_cursor = connection.cursor()
    
    # Clear existing data in SQLite `stops` table
    sqlite_cursor.execute("DELETE FROM stops")
    
    # Insert rows from MySQL into SQLite
    for row in rows:
        sqlite_cursor.execute("INSERT INTO stops (LAT, LONG) VALUES (?, ?)", (row[0], row[1]))
    
    # Commit the changes and close the SQLite connection
    connection.commit()
    connection.close()

            
def haversine(latPos, longPos, latDes, longDes):
    latPos, longPos, latDes, longDes = map(math.radians, [latPos, longPos, latDes, longDes])
    dlat = latDes - latPos
    dlong = longDes - longPos
    a = math.sin(dlat/2)**2 + math.cos(latPos) * math.cos(latDes) * math.sin(dlong/2)**2
    c = 2* math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = 6371 * c * 1000
    return distance

def remove_line():
    #Remove stop from table
    connection = sqlite3.connect("/home/daybroken/Desktop/NEA/myDatabase.db")
    cursor = connection.cursor()
    cursor.execute("DELETE FROM stops WHERE id = (SELECT MIN(id) FROM stops);")
    connection.commit()
    cursor.execute("SELECT COUNT(*) FROM stops;")
    remaining_stops = cursor.fetchone()[0]
    connection.close()
    #If there are no more stops then display end signal and terminate
    if remaining_stops == 0:
        display_array(strip, Matrixs["END"])
        time.sleep(5)
        #Turn the current expedition into an inactive expedition
        conn = connect_to_mysql()
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE ActiveExpeditions 
                JOIN (
                    SELECT Stops.TripID
                    FROM Stops
                    JOIN ActiveExpeditions ON Stops.TripID = ActiveExpeditions.TripID
                    WHERE Stops.TrackerID = %s
                    AND ActiveExpeditions.ActiveTrip = TRUE
                ) AS subquery
                ON ActiveExpeditions.TripID = subquery.TripID
                SET ActiveExpeditions.ActiveTrip = 0
                """, (getTrackerID(),))
    #Indicate a new stop
    else:
        display_array(strip, Matrixs["DOTS"])
        
def main():
    while True:
        turn_off_all_leds(strip)
        connection = sqlite3.connect("/home/daybroken/Desktop/NEA/myDatabase.db")
        cursor = connection.cursor()
        
        #Check if there is location data, if not display dots
        cursor.execute("SELECT LAT, LONG, COG FROM data LIMIT 1;")
        data_row = cursor.fetchone()
        if not data_row:
            print("No GPS data available")
            display_array(strip, Matrixs["OK"])
            time.sleep(2)
            connection.close()
            continue
        
        display_array(strip, Matrixs["DOTS"])
        cursor.execute("SELECT LAT, LONG FROM stops ORDER BY id ASC LIMIT 1;")
        stop_row = cursor.fetchone()
        connection.close()
        
        if not stop_row:
            print("No stops available")
            display_array(strip, Matrixs["END"])
            time.sleep(5)
            sys.exit()
        
        latPos, longPos, cog = map(float, data_row)
        latDes, longDes = map(float, stop_row)
        bearing = calculate_bearing(latPos, longPos, latDes, longDes)
        pointer = compass_directions(bearing, cog)
        distance_to_stop = haversine(latPos, longPos, latDes, longDes)
        
        if distance_to_stop <= 10:
            remove_line()
            turn_off_all_leds(strip)
        display_array(strip, Matrixs[pointer])
            

if __name__ == "__main__":
    display_array(strip, Matrixs["OK"])
    time.sleep(5)
    write_stops()
    main()
