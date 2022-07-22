import os
import sys
import time
import OPi.GPIO as g


g.setwarnings(False)
g.setmode(g.BOARD)

prog='y1 g1 s1 g0 s1 r1 s2 r0 y0'

for item in prog.split():
    cmd=item[0].lower()
    val=item[1:]
    if cmd=='s':
        time.sleep(float(val))
    if cmd=='r':
        if val=='1':
            g.setup(12,g.OUT)
            g.output(12,0)
            g.cleanup(12)
        else:
            g.setup(12,g.IN)
            g.cleanup(12)
    if cmd=='g':
        if val=='1':
            g.setup(15,g.OUT)
            g.output(15,0)
            g.cleanup(15)
        else:
            g.setup(15,g.IN)
            g.cleanup(15)
    if cmd=='y':
        if val=='1':
            g.setup(11,g.OUT)
            g.output(11,0)
            g.cleanup(11)
        else:
            g.setup(11,g.IN)
            g.cleanup(11)


g.cleanup()