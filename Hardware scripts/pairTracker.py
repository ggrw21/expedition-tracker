from utilities import connect_to_mysql, getTrackerID, Matrixs, Colours
import sqlite3
from rpi_ws281x import PixelStrip, Color
import random
import time
import sys

# LED strip configuration
LED_COUNT = 64      
LED_PIN = 18          
LED_FREQ_HZ = 800000    
LED_DMA = 10          
LED_BRIGHTNESS = 30
LED_INVERT = False
LED_CHANNEL = 0

#Get the strip ready for writing
strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip.begin()

def turn_off_all_leds(strip):
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, Color(0,0,0))
    strip.show()

def checkIfPaired():
    #Checking if a pairing record for this tracker exists
    conn = connect_to_mysql()
    with conn.cursor() as cursor:
        cursor.execute('''SELECT Paired FROM TrackerPair WHERE TrackerID = %s''',(getTrackerID(),))
        result =  cursor.fetchone()
    if result == None:
        return False
    return True

def createPairingRecord():
    #Create a record of this tracker in the pairing database#
    while True:
        conn = connect_to_mysql()
        pairingCode = random.randint(100000,999999)
        #Check if the pairingCode alreasdy exists
        with conn.cursor() as cursor:
            cursor.execute('''SELECT * FROM TrackerPair WHERE TrackerCode = %s''',(pairingCode,))
            if cursor.fetchone() == None:
                cursor.execute('''INSERT INTO TrackerPair (TrackerID, TrackerCode, Paired)
        VALUES (%s, %s, %s)''', (getTrackerID(),pairingCode, False))
                conn.commit()
                break
        
def display_array(strip, array, colour):
    # Loop through the 2D array and set the pixel colors
    for y in range(len(array)):
        for x in range(len(array[y])):
            if array[y][x] == 1:
                index = x + y * 8
                strip.setPixelColor(index, colour)
    strip.show()

def getPairing():
    #Checking if a pairing record for this tracker exists
    conn = connect_to_mysql()
    with conn.cursor() as cursor:
        cursor.execute('''SELECT TrackerCode, Paired FROM TrackerPair WHERE TrackerID = %s''',(getTrackerID(),))
        result = cursor.fetchone()
    resultList = list(str(result[0]))
    return resultList, result[1]

def main():
    #If there isnt a record for this tracker create one
    if not checkIfPaired():
        createPairingRecord()
    pairingCode, paired = getPairing()
    #If the tracker is already paired exit the pairing process
    if paired == 1:
        sys.exit()
    while True:
        #Iterate through each digit of the code and of the colour array
        for digit, colour in zip(pairingCode, Colours):
                #Display each digit in a loop
                display_array(strip, Matrixs[int(digit)], colour)
                time.sleep(2)
                turn_off_all_leds(strip)
                pairingCode, paired = getPairing()
                #If pairing is completed exit the process
                if paired == 1:
                    turn_off_all_leds(strip)
                    print('Paired')
                    sys.exit()

                
            
        
if __name__ == '__main__':
    main()   
    