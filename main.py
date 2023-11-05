import umqtt_robust2 as mqtt
from machine import Pin
from neopixel import NeoPixel
from machine import UART
from machine import Pin, I2C
from time import sleep
from time import ticks_ms
import time
from gps_bare_minimum import GPS_Minimum
from mpu6050 import MPU6050  

n = 12  
p = 26  
np = NeoPixel(Pin(p, Pin.OUT), n)  

gps_port = 2  
gps_speed = 9600  

uart = UART(gps_port, gps_speed)  
gps = GPS_Minimum(uart)  

i2c = I2C(0) 
imu = MPU6050(i2c)

tackled = False
hovedstød = False
antal_fald = 0
antal_hovedstød = 0

def set_color(r, g, b):
    for i in range(n):
        np[i] = (r, g, b)
    np.write()


def clear():
    for i in range(n):
        np[i] = (0, 0, 0)
    np.write()

def get_adafruit_gps(): 
    speed = lat = lon = None  
    if gps.receive_nmea_data():
        if gps.get_speed() != -999 and gps.get_latitude() != -999.0 and gps.get_longitude() != -999.0 and gps.get_validity() == "A":
            
            speed = str(gps.get_speed())
            lat = str(gps.get_latitude())
            lon = str(gps.get_longitude())
            
            gps_data = f"{lat},{lon},{speed}"
            return gps_data
        else:
            print("Invalid GPS data")
    return None 

while True: 
    try:
        gps_data = get_adafruit_gps()
        if gps_data: 
            print(f'\ngps_data is: {gps_data}')
            mqtt.web_print(gps_data, 'annamig/feeds/mapfeed/csv')  
            time.sleep(3) 
        
        print(imu.get_values())
        values = imu.get_values()
        value_x = values["acceleration x"]
        print("Acceleration X er:", value_x)

        if tackled == False and value_x < 0.8:
            tackled = True
            hovedstød = False
            print ("taklet")
            antal_fald = antal_fald +1
            print("antal tacklinger: ", antal_fald)
            mqtt.web_print(f'\aantal tacklinger: {antal_fald}', 'annamig/feeds/ESP32feed')
        sleep(3)
        
        
        if tackled == True and value_x > 1:
            print ("hovedstød")
            print("antal hovedstød: ", antal_hovedstød)
            hovedstød = True
            tackled = False
            print("Hovedstød")
            antal_hovedstød = antal_hovedstød +1
            print(antal_hovedstød)
            mqtt.web_print(f'\aantal hovedstød: {antal_hovedstød}', 'annamig/feeds/ESP32feed') 
        sleep(3)
        
        
        color_picker = mqtt.besked
        if color_picker == "1": 
            color = (0, 255, 0)  # Grøn
            set_color(*color) 
            time.sleep(2) 
            clear()
        elif color_picker == "2":
            color = (255, 255, 0)  # Gul
            set_color(*color) 
            time.sleep(2) 
            clear() 
        elif color_picker == "3":
            color = (255, 0, 0)  # Rød
            set_color(*color)
            time.sleep(2)
            clear()

        if len(mqtt.besked) != 0:
            mqtt.besked = ""
        
        mqtt.sync_with_adafruitIO()
        print(".", end='')
  
    except KeyboardInterrupt:
        print('Ctrl-C pressed...exiting')
        mqtt.c.disconnect()
        mqtt.sys.exit()