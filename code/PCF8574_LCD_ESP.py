import time

"""
This code is modified for MicroPython.
This came from https://github.com/sunfounder/SunFounder_SensorKit_for_RPi2/tree/master/Python
Modified for Pin definition for Raspberry Pico
"""

LCD_WIDTH = 20  # n characters wide
LCD_LINES = 4   # LCD number of lines
DELAY = 0.002   # seconds between writes

class LCD:

    def __init__(self, i2c, addr=0x27, bl=True):
        self.LCD_ADDR = addr
        self.BLEN = True
        self.i2c = i2c
        seq = [
            0x33,   # Must initialize to 8-line mode at first
            0x32,   # Then initialize to 4-line mode
            0x28,   # 2 Lines & 5*7 dots
            0x0C,   # Enable display without cursor
            0x01,   # Clear Screen
            ]
        for data in seq:
            self.send_command(data)
            time.sleep(DELAY * 2)
        self.write_byte(0x08)


    def write_byte(self, data):
        #print("I2C.writeto()", end="") #DEBUG
        self.i2c.writeto(self.LCD_ADDR, bytes([data]))
        #print(". Done.") #DEBUG

    def write_word(self, data):
        if self.BLEN:
            data |= 0x08
        else:
            data &= 0xF7
        self.write_byte(data)

    def send_command(self, cmd):

        # Bit positions
        # +---------b7 or b3
        # |+--------b6 or b2
        # ||+-------b5 or b1
        # |||+------b4 or b0
        # ||||+-----BLEN (backlight, 1=enable)
        # |||||+----EN (data is latched on falling edge)
        # ||||||+---RW (1=read, 0=write)
        # |||||||+--RS (1=data, 0=command)
        # ||||||||
        # 76543210

        # Send bit7-4 firstly
        buf = cmd & 0xF0
        buf |= 0x04               # RS = 0, RW = 0, EN = 1
        self.write_word(buf)
        time.sleep(DELAY)
        buf &= 0xFB               # Make EN = 0
        self.write_word(buf)

        # Send bit3-0 secondly
        buf = (cmd & 0x0F) << 4
        buf |= 0x04               # RS = 0, RW = 0, EN = 1
        self.write_word(buf)
        time.sleep(DELAY)
        buf &= 0xFB               # Make EN = 0
        self.write_word(buf)

    def send_data(self, data):
        # Send bit7-4 firstly
        buf = data & 0xF0
        buf |= 0x05               # RS = 1, RW = 0, EN = 1
        self.write_word(buf)
        time.sleep(DELAY)
        buf &= 0xFB               # Make EN = 0
        self.write_word(buf)
        time.sleep(DELAY)

        # Send bit3-0 secondly
        buf = (data & 0x0F) << 4
        buf |= 0x05               # RS = 1, RW = 0, EN = 1
        self.write_word(buf)
        time.sleep(DELAY)
        buf &= 0xFB               # Make EN = 0
        self.write_word(buf)


    def clear(self):
        """Clear Screen"""
        self.send_command(0x01)

    def backlight(self, ena=None):
        """Enable the backlight."""
        if ena == None:
            return self.BLEN
        if ena:
            buf = 0x08
        else:
            buf = 0x00
        self.BLEN  = ena
        self.write_byte(buf)

    def write(self, x, y, text):
        """Write text starting at position (x,y)"""
        if x < 0:
            x = 0
        if x > LCD_WIDTH - 1:
            x = LCD_WIDTH - 1
        if y <0:
            y = 0
        if y > LCD_LINES - 1:
            y = LCD_LINES - 1

        # Move cursor
        addr = 0x80 + x + 0x40*(y % 2) + 0x14*(y > 1)
        self.send_command(addr)

        if len(text) > 0:
            for ch in text:
                self.send_data(ord(ch))
        
    def write_screen(self, text):
        """Clear the screen and write the text contained in text. Line
        breaks are \n."""
        self.clear()
        for line, txt in enumerate(text.split('\n')):
            self.write(0, line, txt)

    def cursor_show(self, ena):
        if ena:
            self.send_command(0x0f) # 0x0F = big block cursor
        else:
            self.send_command(0x0c) # 0x0E = no cursor

    def cursor_right(self):
        """Move cursor one position to the right."""
        self.send_command(0b00010100)

    def cursor_left(self):
        """Move cursor one position to the left."""
        self.send_command(0b00010000)
