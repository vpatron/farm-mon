from machine import Pin, ADC

# OTUAYAUTO 100 Psi Pressure Transducer Sender Sensor
#   1/8" -27 NPT 27 NPT Thread Stainless for Oil Fuel Air Water Pressure with Harness
#   Price: $18.99
# TRANSDUCER OUTPUT: 0.5V – 4.5V linear voltage output. 0 psi outputs 0.5V, 50 psi outputs 2.5V, 100 psi outputs 4.5V
# WIDE RANGE OF APPLICATIONS: Plug and play for fuel, oil, air, water pressure inputs, can be used in oil tank, gas tank, and more

CAL_MIN_P = 0.0
CAL_MIN_V = 0.5
CAL_MAX_P =100.0
CAL_MAX_V = 4.5
ADC_VREF = 3.3
DEC_PLACES = 1

class Pressure:
    def __init__(self):
        self.adc = ADC(0)
        # y = mx+b; m = slope; b = y-mx
        self.slope = (CAL_MAX_P - CAL_MIN_P) / (CAL_MAX_V - CAL_MIN_V)   # psi/V = 25spi/V
        self.offset = CAL_MAX_P - self.slope*CAL_MAX_V                   # -12.5 psi

    def read_psi(self, clip=False):
        vadc= self.adc.read_u16() / 65535 * ADC_VREF
        
        # y = mx + b
        psi = self.slope * vadc + self.offset
        if clip:
            if psi < CAL_MIN_P:
                psi = CAL_MIN_P
            elif psi > CAL_MAX_P:
                psi = CAL_MAX_P
        return round(psi, DEC_PLACES)
