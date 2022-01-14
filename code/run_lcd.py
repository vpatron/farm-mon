import wifi
import ujson
from machine import Pin, I2C
from PCF8574_LCD_ESP import LCD
import time
import urequests
import socket
import button
import flowcounter
import therm_ds18
import pressure


# GPIO
PIN_SDA = 4
PIN_SCL = 5
I2C_FREQ = 100000

# CONSTANTS
GPIO_BUTTON = 0             # onboard button is on GPIO0
PIN_FLOWCOUNTER = 14
PIN_1WIRE = 13
POST_RATE = 360             # Update Thingspeak every N seconds
DISP_TIMEOUT = 60           # Show display for N seconds when button is pressed
DELAY_TEMP_CONV = 0.75      # Wait N seconds after conversion to read temperature
WIFI_TIMEOUT = 60           # wait N seconds for hotspot. Else just shows readings on LCD.
TEST_URL = 'http://mobile.hotspot/index.html'   # page local to the hotspot

def show_ip(seconds):
	lcd.clear()
	lcd.write_screen(wi.ip)
	time.sleep(seconds)
	lcd.clear()

# Read in config file
with open('config.json', 'r') as f:
    config = ujson.loads(f.read())
API_KEY = config['api_key']
print(config) #DEBUG

# Setup LCD
i2c = I2C(scl=Pin(PIN_SCL, Pin.OPEN_DRAIN), sda=Pin(PIN_SDA, Pin.OPEN_DRAIN), freq=I2C_FREQ)
lcd = LCD(i2c, addr=0x27, bl=True)

# Intro screen
lcd.write_screen(
    config['hostname'] + '\n' +
    config['ssid'])
time.sleep(1)

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

tm_old = time.time()
tm_post = tm_old + 10   # Send first post in N seconds
tm_blank = tm_old + DISP_TIMEOUT

# Get an updated temperature
therm.start_conv()
time.sleep(DELAY_TEMP_CONV)
tempF = therm.temp_F()

# DISPLAY FORMAT
# +----------------+
# |g:12.34  sts:120|
# |t:-12.3F  psi:24|
# +----------------+

# Connect to hotspot
wi = wifi.WIFI(hostname=config['hostname'])
wi.disconnect()     # force disconnect in case it was on an old hotspot name
time.sleep(1)
wi = wifi.WIFI(config['hostname'])
wi.connect(config['ssid'], config['pwd'])
tm_tmout = time.time() + WIFI_TIMEOUT
while time.time() < tm_tmout:
    if wi.is_connected:
        break
    time.sleep(0.5)
show_ip(2)
lcd.clear()

# Set time from NTP server
#ntptime.settime()

sts_old = ''
while True:
    # Check for button press and show the display if pressed
    tm_now = time.time()
    while time.time() == tm_now:
        time.sleep(0.1)
        if btn.was_pressed():
            tm_blank = tm_now + DISP_TIMEOUT
            lcd.backlight(True)
            continue
    tm_old = tm_now
    
    # *** Falls through every second ***

    # Check wifi connection. Show reconnects on the LCD with IP addr.
    sts = wi.check(config['ssid'], config['pwd'])
    if sts != sts_old:
        print(sts, wi.is_connected, wi.ip, time.localtime()[0:6])   #DEBUG
        if sts == 'con':
            show_ip(2)
    sts_old = sts
    
    # tm_count counts down from high of POST_RATE to 0. Zero is when 
    # http request should be done. Use this to time when to do readings
    # etc. tm_count is monotonic.
    if tm_now > tm_post:
        tm_post += POST_RATE
    tm_count = tm_post - tm_now

    # Do a temperature conversion (1 wire) several seconds ahead of post
    if tm_count == 30:
        therm.start_conv()

    # These measurements update on LCD every second. Temperature is
    # updated only just before post.
    # Get water volume accumulated in gallons. Get water pressure in psi.
    gal = round(flow.volume_gal(reset=True), 3)
    psi = press.read_psi(clip=True)

    # Update display
    tempF = therm.temp_F(last=True)
    gal = flow.volume_gal()
    psi = press.read_psi(clip=True)
    lcd.write(0, 0, 'g:{:<6.2f}'.format(gal))
    lcd.write(0, 1, 't:{:<5}'.format(str(round(tempF, 1)) + 'F'))
    lcd.write(10, 1, 'psi:{:.0f}'.format(psi))
    if sts == 'con':
        lcd.write(9, 0, 'sts:{:<3n}'.format(tm_post - tm_now))
    else:
        lcd.write(9, 0, 'sts:{}'.format(sts))
        tm_post = time.time() + 30   # Send first N seconds after good connection

    # Blank the display after timeout. Or update readings if not yet
    # timeout.
    if lcd.backlight():
        if tm_now >= tm_blank:
            lcd.backlight(False)

    # Check if it's time to post
    if tm_count == 0:
        time.sleep(DELAY_TEMP_CONV)
        # Get temperature and water volume. Reset water volume.
        try:
            tempF = round(therm.temp_F(), 2)
        except IOError:
            tempF = -99.99

        # Post to Thingspeak
        url = 'https://api.thingspeak.com/update?api_key={}&field1={}&field2={}&field3={}'.format(
            API_KEY, str(gal), str(psi), str(tempF))
        sts = wi.http_get(url)
        print(sts)  #DEBUG

        # Show the 3 char status on LCD
        lcd.write(9, 0, 'sts:{}'.format(sts))
        time.sleep(2)
