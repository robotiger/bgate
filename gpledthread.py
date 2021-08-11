from threading import Thread
import time
import OPi.GPIO as g

# A class that extends the Thread class
class gpled(Thread):
    def __init__(self,newprog):
        # Call the Thread class's init function
        Thread.__init__(self)
        self.prog=newprog
        
    def setprog(self,newprog):
        print("newprog",newprog)
        self.prog=newprog
    
    def run(self):
        print('start prog',self.prog)
        while len(self.prog)>0:
            for item in self.prog.split():
                cmd=item[0].lower()
                val=item[1:]
                if cmd=='s':
                    time.sleep(float(val))
                if cmd=='r':
                    if val=='1':
                        g.setup(12,g.OUT)
                        g.output(12,0)
                        g.cleanup(12)
                        print("red on")
                    else:
                        g.setup(12,g.IN)
                        g.cleanup(12)
                        print("red off")
                if cmd=='g':
                    if val=='1':
                        g.setup(15,g.OUT)
                        g.output(15,0)
                        g.cleanup(15)
                        print("green on")
                    else:
                        g.setup(15,g.IN)
                        g.cleanup(15)
                        print("green off")
                if cmd=='y':
                    if val=='1':
                        g.setup(11,g.OUT)
                        g.output(11,0)
                        g.cleanup(11)
                        print("yellow on")
                    else:
                        g.setup(11,g.IN)
                        g.cleanup(11)
                        print("yellow off")                
                time.sleep(0.05)
        
def main():
    # Create an object of Thread
    th = gpled('g1 s1 g0 s1')
    # start the thread
    th.start()
    # print some logs in main thread
    for i in range(5):
        print('Hi from Main Function')
        time.sleep(10)
        th.setprog('r1 s1 r0 s1')
        print('Hi from Main Function')
        time.sleep(10)
        th.setprog('y1 s2 y0 s2')
    # wait for thread to finish
    th.setprog('')
    th.join()
if __name__ == '__main__':
    main()