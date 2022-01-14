import machine, ssd1306
from machine import Pin
from time import time, sleep

# Heltek 8 (ESP8266) hardwired pin assignments
PIN_RESET = 16  # GPIO16 = OLED reset
PIN_SDA = 4
PIN_SCL = 5
I2C_FREQ = 100000

DISP_BLANK_TMOUT = 60
DISP_WIDTH = 128
DISP_HEIGHT = 32
LINE_HEIGHT = 12        # N pixels tall each line
LINE_CHARS = 16         # N chars for each line
LINE_LINES = 3          # N lines of text
CHAR_WIDTH = 8

class OLED:

    def __init__(self):
        # Take OLED out of reset
        self.pin_rst = Pin(PIN_RESET, Pin.OUT)
        self.pin_rst.value(0)
        sleep(0.05)
        self.pin_rst.value(1)

        # OLED is 128 pixels wide x 32 pixels tall, I2C interface
        self.i2c = I2C(scl=Pin(PIN_SCL), sda=Pin(PIN_SDA), freq=I2C_FREQ)
        self.oled = ssd1306.SSD1306_I2C(DISP_WIDTH, DISP_HEIGHT, self.i2c)
        self.oled.fill(0) 
        self.oled.show()
        self.visible = True

    def clear(self):
        self.oled.fill(0) 
        self.oled.show()

    def text(self, text='', row=0, col=0):
        width = len(text)
        # Erase the line (fill the rectangle with 0)
        self.oled.fill_rect(col*CHAR_WIDTH, row*LINE_HEIGHT, width*CHAR_WIDTH, LINE_HEIGHT, 0)
        self.oled.text(text, col*CHAR_WIDTH, row*LINE_HEIGHT)
        self.oled.show()

    def blank(self, blnk):
        if blnk:
            self.visible = False
            self.oled.poweroff()
        else:
            self.visible = True
            self.oled.poweron()

