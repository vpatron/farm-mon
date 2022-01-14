import onewire
import ds18x20
import time

BAD_READ_LOW = -30      # -30C = -22F
BAD_READ_HIGH = 65      # 65C = 149F
DELAY_CONV_S = 0.75

class Thermometer:
    def __init__(self, pin, addr):
        # Setup OneWire bus and temp sensor
        #   pin = GPIO pin
        #   rom = specific device's address in ROM code (a 8-value bytearray)
        self.ow = onewire.OneWire(pin)
        self.addr = addr
        self.ow.select_rom(self.addr)
        self.sensor = ds18x20.DS18X20(self.ow)
        self.temp = -99.99

    def start_conv(self):
        # Send command to sensor to start conversion
        self.sensor.convert_temp()

    def temp_C(self, last=False):
        # Do not call this until 750 ms or more after start_conv()
        if last:
            return self.temp
        self.temp = self.sensor.read_temp(self.addr)

        # Reread if bad. Have gotten bad (e.g. 85C (185F) reading at room temp.
        if self.temp <= BAD_READ_LOW or self.temp >= BAD_READ_HIGH:
            self.sensor.convert_temp()
            time.sleep(DELAY_CONV_S)
            self.temp = self.sensor.read_temp(self.addr)
        return self.temp

    def temp_F(self, last=False):
        # Do not call this until 750 ms or more after start_conv()
        if last:
            return self.temp * 9/5 + 32
        return self.temp_C() * 9/5 + 32
