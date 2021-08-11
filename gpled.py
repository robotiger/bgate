import json
import os
import sys
import time
import OPi.GPIO as GPIO



def gpio(pin,state):
    if state:
        GPIO.setup(gi,GPIO.OUT)
        GPIO.output(pin,0)
    else:
        GPIO.setup(gi,GPIO.IN)
        #GPIO.output(pin,0)
       
    


def relrun(): 

#    for gi in inputs:
#        GPIO.setup(gi,GPIO.IN)
#        GPIO.add_event_detect(gi,GPIO.BOTH,callback=ambut)
#        print('callback added ',gi)
#    for go in outputs:
#        GPIO.setup(go,GPIO.OUT)
#        GPIO.remove_event_detect(gi)




if __name__ == '__main__':

    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)

    pin=11
    
    for t in range(10):
        gpio(pin,True)
        time.sleep(0.1)
        gpio(pin,False)
        time.sleep(0.3)


    GPIO.cleanup()

