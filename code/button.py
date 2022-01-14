from machine import Pin

class Button:

    def __init__(self, pin, activelow=True):
        self.pin = pin
        self.activelow = activelow
        self.state = self.pin.value()

    def was_pressed(self):
        # Returns True only on the transition of when the button was pressed
        now = self.pin.value()
        if self.state != now:
            self.state = now
            if self.activelow:
                return now == 0
            else:
                return now == 1
        return False

    def is_pressed(self):
        # Returns the real-time state of the button
        if self.activelow:
            return self.pin.value() == 0
        else:
            return self.pin.value() == 1

