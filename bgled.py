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
    def __init__(self,newprog):
        # Call the Thread class's init function
        Thread.__init__(self)
        self.prog=newprog
        g.setwarnings(False)
        g.setmode(g.BOARD)        
        
    def setprog(self,newprog):
        print("newprog",newprog)
        self.prog=newprog

    def run(self):
        print('start prog',self.prog)
        pin={
            'r':(off,12),
            'R':(on,12),
            'g':(off,15),
            'G':(on,15),
            'y':(off,11),
            'Y':(on,11)
            }
             
        while len(self.prog)>0:
            for item in self.prog.split():
                cmd=item[0]
                if cmd in pin:
                    pin[cmd][0](pin[cmd][1])               
                    val=item[1:]
                    time.sleep(float(val))
                time.sleep(0.1)
        
def main():
    # Create an object of Thread
    th = bgled('G1 g1 R1 r1 Y1 y1')
    # start the thread
    th.start()
    # print some logs in main thread
    for i in range(5):
        print('Hi from Main Function')
        time.sleep(10)
        th.setprog('R1 r1')
        print('Hi from Main Function')
        time.sleep(10)
        th.setprog('Y2 y2')
    # wait for thread to finish
    th.setprog('')
    th.join()
if __name__ == '__main__':
    main()