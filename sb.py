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
import struct
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


class BlAdvCoder:
    
    @staticmethod
    def commandledencoder(mac,r,g,b,t,p,o):
        ## используется для управления светодиодом бикона
        ## формирует строку для отправки в блютус модуль.
        ## входные параметры мак адрес '010203040506', яркость цветов r,g,b, длительность в секундах, период в милисекундах, время включения в милисекундах
        try:
            enc_data= struct.pack('>5s6s3B3h',b'\xab\xba\x0f\00\04',bytes.fromhex(mac),r,g,b,t,p,o)
        except:
            return None
        crc=zlib.crc32(enc_data)&0xffff
        #print(crc32.to_bytes().hex(' '))
        return struct.pack('>20sH',enc_data,crc)
    
          
    @staticmethod
    def decode2(dpin):
        #dpo={'macgate':config['macgate']}
        
        dp1=dict(zip(['mac','rssi','band'],struct.unpack('2x6s3x2b',dpin[:13])))
        if len(dpin)==43: # from beacons
            dp2=dict(zip(['mfg','uuid','cnt','ext','exd','txpower'],       struct.unpack('6s16sHBBb', dpin[16:])))
            dp3=dict(zip(['mfg','cnt','type','uuid','ext','exd','txpower'],struct.unpack('5sH2s8sBib',dpin[16:41])))
            if dp2['mfg'].hex()=='1aff4c000215': #apple beacon
                dpo={**dp1,**dp2}
            if dp3['mfg'].hex()=='16ffb1bf00': #hitech beacon
                dpo={**dp1,**dp3}
            for c in dpo:
                if c in ['mac','mfg','uuid']:
                    dpo[c]=dpo[c].hex()
            #dpo['gate']=config['macgate']
            dpo['raw']=dpin.hex()
            return dpo
             

    @staticmethod   
    def aesdecode(dpin):
        key= b'fkytbwpt69xsbna3'
        salt=b'lrjk;rdfkdldkhcngfle45'
        dlina=dpin[13]
        mfg=dpin[14:17].hex()
#        print(dlina,ffmfg.hex(),once.hex(),coded.hex())
        if mfg=='ffb1bf':
            dlina,mfg,once,coded=struct.unpack('13xb3s4s%ds'%(dlina-7),dpin)         
            nonce=hashlib.sha1(once+salt)
            rcv =AES.new(key,AES.MODE_EAX,nonce=nonce.digest()).decrypt(coded)
            crc,cfg,data=struct.unpack('Hh%ds'%(dlina-11),rcv)
            crcc=zlib.crc32(data)&0xffff
            if crc==crcc:
                return (cfg,data)
            else:
                return (0,'')



class SerialBgate(threading.Thread):


    def __init__(self,port):
        print("__init__")
        threading.Thread.__init__(self)  
        self.port=port
        self.pack=b''
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


            
    def f_ab(self,s):
        return len(self.pack)==0 and s==0xab

    def f_ba(self,s):
        return len(self.pack)==1 and s==0xba
    
    def f_dl(self,s):
        if len(self.pack)==2:
            self.length=s
            return True
        else:
            return False

    def f_ta(self,s):
        return len(self.pack)<self.length+7
        
            
    def paddbyte(self,serstr):
        
        for s in serstr:
            if self.f_ab(s) and self.f_ba(s) and self.f_dl(s) and self.f_ta(s):
                self.pack+=bytes([s])
            else:
                crc1 = struct.unpack('H',self.pack[-2:])
                crc2 = zlib.crc32(self.pack[:-2]) & 0xffff
                if crc1==crc2:
                    print(self.pack.hex(' '))
                self.pack=b''
               

    def SerialDaemon(self):
       
        with serial.Serial(self.port, 115200, timeout=1) as ser:  
            while(self.runing):
                self.paddbyte(ser.read())
                #sib=ser.read()
                #if len(sib)>0:
                    #ib=sib[0]
##                    print(sib,ib) #f
                    #if self.cnt==0:
                        #if ib==0xab:
                            #self.cnt=1
                    #elif self.cnt==1:
                        #if ib==0xba:
                            #self.cnt=2
                    #elif self.cnt==2:
                        #self.leng=ib
                        #self.length=ib
                        #self.cnt=3
                    #elif self.cnt==3:
                        #self.idpack=ib*256
                        #self.cnt=4
                    #elif self.cnt==4:
                        #self.idpack+=ib
                        #self.cnt=5
                        #self.datapack=b''
                    #elif self.cnt==5:
 ##                       print(self.length,self.leng)
                        #if self.length>0:
##                            print("add")
                            #self.datapack+=sib
                            #self.length-=1
                        #else:
                            #self.cnt=6
                    #if self.cnt==6:
                        #self.crc=ib*256
                        #self.cnt=7
                    #elif self.cnt==7:
                        #self.crc+=ib
                        #self.cnt=0

##                        print(self.datapack[39:],b"\x03\x08HB")
                        #if len(self.datapack)>=13: # and self.datapack[39:]==b"\x03\x08HB":
##                            if self.datapack[2:8] in bfiltermac :
                            #if True:
                                #print(self.datapack[0:6].hex())
                                #print(self.port,end=': ')
                                ##print("len %d lp %d id %d "%(len(self.datapack),self.leng,self.idpack),end='')
                                ##for d in self.datapack:
                                ##    print("%02x "%d,end='')
                                ##print(' ')
                                #print(self.datapack.hex(' '))
                                #if len(self.datapack)==43:
                                    #d=BlAdvCoder.decode2(self.datapack)
                                    ##publish
                                    #print(d)               
                                #else:
                                ##if len(self.datapack)==44:
                                    #d=BlAdvCoder.aesdecode(self.datapack)
                                    ##config
                                    #print(d)                                
                                ##BlAdvCoder.aesdecode(self.datapack)
                                ##decode(self.datapack[13:])

            


        
    




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






