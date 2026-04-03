import subprocess
import time
import mysql.connector
import sys
from utilities import connect_to_mysql


#Ru#n pairTRacker and wait for it to complete
pair_tracker = subprocess.Popen(["/home/daybroken/myenv/bin/python3","/home/daybroken/Desktop/NEA/pairTracker.py"])
pair_tracker.wait()

#Run Upload GPS Script & Led HAT script at the same time to run in parallel
gps_write = subprocess.Popen(["/home/daybroken/myenv/bin/python3","/home/daybroken/Desktop/NEA/upload_gps.py"])
time.sleep(5)
led_hat = subprocess.Popen(["/home/daybroken/myenv/bin/python3","/home/daybroken/Desktop/NEA/led_hat.py"])

try:
    #Whilst LED hat script is still running...
    while led_hat.poll() is None:
        time.sleep(1)
        
    print('Terminating')
    gps_write.terminate()
    led_hat.terminate()
    sys.exit()
    
    
    
except Exception as e:
    print(e)
    

