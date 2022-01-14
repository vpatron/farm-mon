from machine import Pin
from flowcounter import FlowCount
from button import Button
from time import sleep
import oled

PIN_FLOWCOUNTER = 14    # Use GPION as counter input
PIN_BUTTON = 0          # GPIO0 is onboard button

disp = oled.OLED()
disp.clear()
disp.text('Flowcounter Test', row=0)

btn = Button(Pin(PIN_BUTTON, Pin.IN, Pin.PULL_UP), activelow=True)
flow = FlowCount(Pin(PIN_FLOWCOUNTER, Pin.IN, Pin.PULL_UP))

while True:
    if btn.was_pressed():
        flow.volume(reset=True)
    disp.text('pulses:{}     '.format(flow.ctr_pulses), row=1)
    disp.text('liters:{:.3f}     '.format(flow.volume()), row=2)
    sleep(0.2)
