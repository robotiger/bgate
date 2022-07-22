import json
import os
import requests
import uuid
import os
import time
import OPi.GPIO as GPIO

inputs=[3,5,16,18,26]
outputs=[7,22,15,24,23,19,21]

def ambut(c):
    print('key pressed %d '%(c,))


def relrun(): 
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)

    for gi in inputs:
        GPIO.setup(gi,GPIO.IN)
        GPIO.add_event_detect(gi,GPIO.BOTH,callback=ambut)

        print('callback added ',gi)

    for go in outputs:
        GPIO.setup(go,GPIO.OUT)

def relstop():
    print("stop doorrelays")
    GPIO.setwarnings(False)
    for gi in inputs:
        GPIO.remove_event_detect(gi)
    GPIO.cleanup()


def toggle(pin):
    GPIO.output(outputs[pin],not GPIO.input(outputs[pin]))
    print("output %s  read %d"%(outputs[pin],GPIO.input(outputs[pin])))



if __name__ == '__main__':

    print('test inputs and outputs ',__name__)


    relrun()
    while(True):
        t=int(input("toggle output 0..6 to stop press 9>"))
        if t==9 :
            break
        toggle(t)
    relstop() 
