from threading import Thread
import time
import OPi.GPIO as g


def on(pin):
    g.setup(pin,g.OUT)
    g.output(pin,0)
    g.cleanup(pin)  
    
def off(pin):
    g.setup(pin,g.IN)
    g.cleanup(pin)


# A class that extends the Thread class
class bgled(Thread):
    def __init__(self,stop_event):
        # Call the Thread class's init function
        Thread.__init__(self)
        self.stop_event=stop_event
        self.prog=''
        g.setwarnings(False)
        g.setmode(g.BOARD)        
        
    @staticmethod
    def ledoff():
        off(11)
        off(12)
        off(15)
        
    def setprog(self,newprog):
        #print("newprog",newprog)
        self.prog=newprog


    def run(self):
        self.running=True
        #print('start prog',self.prog)
        pin={
            'r':(off,12),
            'R':(on,12),
            'g':(off,15),
            'G':(on,15),
            'y':(off,11),
            'Y':(on,11)
            }
             
        while len(self.prog)>0 and not self.stop_event.is_set():
            for item in self.prog.split():
                cmd=item[0]
                if cmd in pin:
                    pin[cmd][0](pin[cmd][1])               
                    val=item[1:]
                    time.sleep(float(val))
                time.sleep(0.1)
        
def main():
    stop_event = threading.Event()
    # Create an object of Thread
    th = bgled(stop_event)
    th.setprog('G1 g1 R1 r1 Y1 y1')
    # start the thread
    th.start()
    # print some logs in main thread
    for i in range(5):
        time.sleep(10)
        print('red blink')
        th.setprog('R1 r1')
        time.sleep(10)
        print('yellow blink')
        th.setprog('Y2 y2')
    # wait for thread to finish
    th.setprog('')
    bgled.ledoff()
    th.join()

if __name__ == '__main__':
    main()
    