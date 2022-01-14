#import ntptime
import wifi
import ujson
import oled
from machine import Pin
import time
import urequests
import socket
import button
import flowcounter
import therm_ds18
import pressure

# CONSTANTS
GPIO_BUTTON = 0             # onboard button is on GPIO0
PIN_FLOWCOUNTER = 14
PIN_1WIRE = 13
POST_RATE = 360             # Update Thingspeak every N seconds
DISP_TIMEOUT = 60           # Show display for N seconds when button is pressed
DELAY_TEMP_CONV = 0.75      # Wait N seconds after conversion to read temperature

# Read in config file
with open('config.json', 'r') as f:
    config = ujson.loads(f.read())
API_KEY = config['api_key']


# Intro screen
disp = oled.OLED()
disp.text(config['hostname'], row=0)
disp.text('connecting to', row=1)
disp.text(config['ssid'], row=2)
time.sleep(2)

# Connect to hotspot
wi = wifi.WIFI(config['hostname'])
wi.connect(config['ssid'], config['pwd'])
while not wi.is_connected:
    time.sleep(0.2)
disp.clear()
disp.text(wi.ip, row=2, col=1)

# Set time from NTP server
#ntptime.settime()

#---------
# Setup IO
#---------

# Button press shows display for a few seconds
btn = button.Button(Pin(GPIO_BUTTON, Pin.IN, Pin.PULL_UP), activelow=True)

# Setup OneWire bus and temp sensor
therm = therm_ds18.Thermometer(Pin(PIN_1WIRE), bytearray(config['1wire_addr1']))

# Water flow sensor
flow = flowcounter.FlowCount(Pin(PIN_FLOWCOUNTER, Pin.IN, Pin.PULL_UP))

# Water pressure
press = pressure.Pressure() 

# DISPLAY FORMAT
# +----------------+
# |g:12.34  pst:120|
# |t:-12.3F  psi:24|
# | 255.255.255.255|
# +----------------+


tm_old = time.time()
tm_post = tm_old + 10   # Send first post in N seconds
tm_blank = tm_old + DISP_TIMEOUT

# Get an updated temperature
therm.start_conv()
time.sleep(DELAY_TEMP_CONV)
tempF = therm.temp_F()

while True:
    tm_now = time.time()
    while time.time() == tm_now:
        # Check for button press and show the display if pressed
        time.sleep(0.1)
        if btn.was_pressed():
            tm_blank = tm_now + DISP_TIMEOUT
            disp.blank(False)
            continue
    tm_old = tm_now
    # Loop every second as needed

    # Check if it's almost time to post
    if tm_now == tm_post - 1:
        therm.start_conv()

    # Check if it's time to post
    if tm_now >= tm_post:
        tm_post = tm_now + POST_RATE
        time.sleep(DELAY_TEMP_CONV)
        # Get temperature and water volume. Reset water volume.
        try:
            tempF = round(therm.temp_F(), 2)
        except IOError:
            tempF = -99.99
        # Get water volume accumulated in gallons. Get water pressure in psi.
        gal = round(flow.volume_gal(reset=True), 3)
        psi = press.read_psi(clip=True)
        # Post to Thingspeak
        url = 'https://api.thingspeak.com/update?api_key={}&field1={}&field2={}&field3={}'.format(
            API_KEY, str(gal), str(psi), str(tempF))
        #print(url)
        wi.http_get(url)

    # Blank the display after timeout. Or update readings if not yet
    # timeout.
    if disp.visible:
        if tm_now < tm_blank:
            tempF = therm.temp_F(last=True)
            gal = flow.volume_gal()
            psi = press.read_psi(clip=True)
            disp.text('g:{:<6.2f}'.format(gal), row=0)
            disp.text('t:{:<5}'.format(str(round(tempF, 1)) + 'F'), row=1)
            disp.text('psi:{:.0f}'.format(psi), row=1, col=10)
            disp.text('pst:{:<3n}'.format(tm_post - tm_now), row=0, col=9)
        else:
            disp.blank(True)

    #print(tm_now, tm_blank, tm_post, tm_post - tm_now)
