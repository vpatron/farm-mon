from machine import Pin, Timer

# Pulses per liter -- Filled up a 5 gallon bucket with hose at full on
# and got 8661 pulses. Maybe took 20 seconds.
#   1 gallon = 3.7854 liters
#   8661 / 18.927 = 468.17 pulses per liter
#   8661 / 5 = 1772.2 pulses per gallon
#
# Max frequency count -- bench test showed max 2500 Hz frequency input
#   Pump data shows 13.4 gpm at 20 psi with 5' suction lift
#   13.4 gal * 3.7854 l/g = 50.72 liters
#   50.72 l/m / 60 seconds * 468.2 pulses/l = 395.8 Hz
#   so well within 2.5 kHz max
#
# What is max gal/min?
#   2500Hz * 60sec/min / 1772.2ppg = 84.64 gal/min max frequency
#   So plenty of margin to read frequency fast enough


CONV_L_TO_GAL = 1/3.7854    # Liter to gallon conversion ratio


class FlowCount:
    def __init__(self, pin):
        self.pin = pin
        self.ctr_pulses = 0     # raw pulse count
        self.ratio_ppl = 468    # pulses per liter of liquid
        self.acc_liters = 0     # liters accumulated
        self.ctr_reset = False  # flag for IRQ to reset count

        # Interrupt callback for every pin pulse detected
        self.pin.irq(trigger=Pin.IRQ_FALLING, handler=self._cb_pulse)

    def __del__(self):
        del self.pin

    def _cb_pulse(self, _):
        # Call this every pulse detected. IRQ must use integer only!
        self.ctr_pulses += 1
        if self.ctr_reset:
            self.ctr_reset = False
            self.acc_liters = 0
            self.ctr_pulses = 0
        elif self.ctr_pulses >= self.ratio_ppl:
            self.ctr_pulses = 0
            self.acc_liters += 1

    def volume(self, reset=False):
        liters = self.acc_liters + self.ctr_pulses / self.ratio_ppl
        if reset:
            self.ctr_reset = True
            self.acc_liters = 0
            self.ctr_pulses = 0
        return liters

    def volume_gal(self, reset=False):
        gal = self.volume(reset=reset) * CONV_L_TO_GAL
        return gal
