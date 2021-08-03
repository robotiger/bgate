import serial
#import numpy as np
import math
import os
import sys
import threading
import time
import queue
import datetime
import logging
import uuid
import zlib
import hashlib
from Crypto.Cipher import AES
from struct import *
#import blescan
#import bluetooth._bluetooth as bluez


#from matplotlib.lines import Line2D
#import matplotlib.pyplot as plt
#import matplotlib.animation as animation

filtermac=[
[0x00, 0x01, 0x95, 0x3f, 0xc8, 0x9b]
#[0x62,0x66,0xdc,0xc1,0xde,0xfb],
#[0xa5,0x75,0xcf,0x0c,0x91,0x97],
#[0xe1,0x8d,0x8d,0x38,0xc4,0x24],
#[0xee,0xd5,0x99,0x05,0xae,0xd3],
#[0xef,0x11,0x48,0x83,0x11,0x5b],
#[0xf4,0xb8,0x5e,0xde,0xb2,0x08],
#[0xfd,0x03,0x97,0x13,0xda,0x76]
]

bfiltermac=[
b'\x00\x01\x95\x3f\xc8\x9b',
#b'\xaf\xbf\xcf\xdf\xef\xff',
#b'\x62\x66\xdc\xc1\xde\xfb',
#b'\xa5\x75\xcf\x0c\x91\x97',
#b'\xe1\x8d\x8d\x38\xc4\x24',
#b'\xee\xd5\x99\x05\xae\xd3',
#b'\xef\x11\x48\x83\x11\x5b',
#b'\xf4\xb8\x5e\xde\xb2\x08',
#b'\xfd\x03\x97\x13\xda\x76'
]


def logi(s):
    logname='/home/bfg/bgate/bdata'
    logging.basicConfig(format='%(asctime)s | %(message)s', datefmt='%Y/%m/%d %H:%M:%S ', filename=logname, level=logging.INFO)
    logging.info(s)
    print(s)


class makemesage:
    def __init__(self):
        self.key= b'fkytbwpt69xsbna3'
        #           0123456789012345
        self.salt=b'lrjk;rdfkdldkhcngfle45'
    def message(self,cfg,data):
        once=AES.new(self.key,AES.MODE_EAX).nonce
        self.ronce=once[:4]
        print(self.ronce.hex())
        self.nonce=hashlib.sha1(self.ronce+self.salt)
        print(self.nonce.hexdigest())
        if len(data)>19:
            return None
        mes=pack('2sh%ds'%len(data),once[:2],cfg,data)
        coded,tag = AES.new(self.key,AES.MODE_EAX,nonce=self.nonce.digest()).encrypt_and_digest(mes) 
        lc=len(coded)
        lr=len(self.ronce)
        print(coded.hex())
        return pack('5B4s23s', lc+4+lr,lc+3+lr,0xff,0xb1,0xbf,self.ronce,coded+b'\x00'*(24-lc))

    def decode(self,mes):
#16 ff b1 bf c3 79 4a 0e 04 fb e1 e4 03 59 40 db 75 1b dc 28 db b3 75 
#00 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19 20 21 22
#len        !nonce      ! mes
                        # once! cfg ! data
        dlina=mes[0]
        ffmfg=mes[1:4]
        once=mes[4:8]
        coded=mes[8:dlina+1]
        print(dlina,ffmfg.hex(),once.hex(),coded.hex())
        if ffmfg.hex()=='ffb1bf':
            nonce=hashlib.sha1(once+self.salt)
            rcv =AES.new(self.key,AES.MODE_EAX,nonce=nonce.digest()).decrypt(coded)
            ronce,cfg,data=unpack('2sh%ds'%(dlina-11),rcv)
            print(ronce==once[:2],cfg,data)

def decode(mes):
    key= b'fkytbwpt69xsbna3'
    salt=b'lrjk;rdfkdldkhcngfle45'
    dlina=mes[0]
    ffmfg=mes[1:4]
    once=mes[4:8]
    coded=mes[8:dlina+1]
    print(dlina,ffmfg.hex(),once.hex(),coded.hex())
    if ffmfg.hex()=='ffb1bf':
        nonce=hashlib.sha1(once+salt)
        rcv =AES.new(key,AES.MODE_EAX,nonce=nonce.digest()).decrypt(coded)
        ronce,cfg,data=unpack('2sh%ds'%(dlina-11),rcv)
        print(ronce==once[:2],cfg,data)


class SerialBgate(threading.Thread):


    def __init__(self,port):
        print("__init__")
        threading.Thread.__init__(self)  
        self.port=port

        self.queue = queue.Queue() 
        self.cnt = 0

    def run(self): 
        print("run")
        self.runing=True
        self.SerialDaemon()
        
        
    def stop(self):
        print("stop")
        self.runing=False        

    def Print(self,txt):
        if(not self.queue.empty()):
            print(txt,self.queue.get())

    def SerialDaemon(self):
       
        with serial.Serial(self.port, 115200, timeout=1) as ser:  
            while(self.runing):
                sib=ser.read()
                if len(sib)>0:
                    ib=sib[0]
#                    print(sib,ib) #f
                    if self.cnt==0:
                        if ib==0xab:
                            self.cnt=1
                    elif self.cnt==1:
                        if ib==0xba:
                            self.cnt=2
                    elif self.cnt==2:
                        self.leng=ib
                        self.length=ib
                        self.cnt=3
                    elif self.cnt==3:
                        self.idpack=ib*256
                        self.cnt=4
                    elif self.cnt==4:
                        self.idpack+=ib
                        self.cnt=5
                        self.datapack=b''
                    elif self.cnt==5:
 #                       print(self.length,self.leng)
                        if self.length>0:
#                            print("add")
                            self.datapack+=sib
                            self.length-=1
                        else:
                            self.cnt=6
                    if self.cnt==6:
                        self.crc=ib*256
                        self.cnt=7
                    elif self.cnt==7:
                        self.crc+=ib
                        self.cnt=0

#                        print(self.datapack[39:],b"\x03\x08HB")
                        if len(self.datapack)>=13: # and self.datapack[39:]==b"\x03\x08HB":
                            if self.datapack[2:8] in bfiltermac :
#                            if True:
                                print(self.datapack[0:6].hex())
                                print(self.port,end=': ')
                                print("len %d lp %d id %d "%(len(self.datapack),self.leng,self.idpack),end='')
                                for d in self.datapack:
                                    print("%02x "%d,end='')
                                print(' ')
                                decode(self.datapack[13:])
#                   
#                            print("part for crc",end=': ')
#                            dp=self.datapack[20:37]
#                            for d in dp:
#                                print("%02x "%d,end='')
#                            print(' ')
  
#                            print("%x %x %X"%(self.datapack[37],self.datapack[38], zlib.crc32(dp)))


#                            print(self.port,end=': ')
#                            print("len %d lp %d id %d "%(len(self.datapack),self.leng,self.idpack),end='')
#                            for d in self.datapack:
#                                print("%02x "%d,end='')
#                            print(' ')

#                            if self.datapack[0:6] in bfiltermac :
#                            logi('p:%s;mac:%02x%02x%02x%02x%02x%02x; %2x%2x id:%02x%02x%02x%02x%02x%02x%02x%02x n:%6d txpower:%3d; rssi:%d; ch:%d'%(
#                            self.port,
#                            int(self.datapack[2]),
#                            int(self.datapack[3]),
#                            int(self.datapack[4]),
#                            int(self.datapack[5]),
#                            int(self.datapack[6]),
#                            int(self.datapack[7]), #mac#

#                            int(self.datapack[19]), #manid
#                            int(self.datapack[18]), #manid2

#                            int(self.datapack[23]), #dev type
#                            int(self.datapack[24]), #dev subtype
#                            int(self.datapack[25]), #id
#                            int(self.datapack[26]), #id
#                            int(self.datapack[27]), #id
#                            int(self.datapack[28]), #id
#                            int(self.datapack[29]), #id
#                            int(self.datapack[30]), #id

#                            int(self.datapack[21])*256+int(self.datapack[22]),

#                            int(self.datapack[36]), #txpower
#                            int(self.datapack[11])-256, #rssi
#                            int(self.datapack[12]), #channel


                                                    
#                            int(self.datapack[6])*256+int(self.datapack[7]),
#                            int(self.datapack[8]),
#                            int(self.datapack[9]),
#                            int(self.datapack[10]),# if int(self.datapack[10]>127,
#                            int(self.datapack[11])-256,
#                            int(self.datapack[12]),

#                            ))
#                                self.queue.put("%s%d"%(" "*((self.datapack[12]-37)*7),self.datapack[11]-256,))
                        
#                        print("%s%d"%(" "*((self.datapack[12]-37)*7),self.datapack[11]-256,))
                                
#                        for oneb in self.datapack:
#                            print('%x'%(oneb,),end=' ')
#                        print('')
            


        
    
    
    def readp(self):
        if not self.queue.empty():
            return self.queue.get()
        else:
            return None





ls={}
#M=makemessage()

for  arg in range(1,len(sys.argv)):
    print("<",arg,">")
    ls[arg]=SerialBgate(sys.argv[arg])
    ls[arg].start()
t=input("Enter to exit")

for  b in ls:
    ls[b].stop()
    ls[b].join()






