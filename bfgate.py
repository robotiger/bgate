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
import msgpack
import paho.mqtt.client as mqtt 
#import blescan
#import bluetooth._bluetooth as bluez


#from matplotlib.lines import Line2D
#import matplotlib.pyplot as plt
#import matplotlib.animation as animation


"""
   00 03 9c 97 89 7e 7c a8 01 ff 7f a9 25 02 01 1a 1b ff 8f 03 16 01 01 00 48 00 e4 3c 74 20 55 97 9c 89 a8 7c 7e 36 97 9c 89 a8 7c 7e   

HIBEACON ble4
   00 03 62 66 dc c1 de fb 01 ff 7f bc 25 02 01 06 1a ff 4c 00 02 15 00 00 00 01 7f 48 92 db f5 8c 11 9d c0 98 49 b7 01 64 b2 8a f8
   00 03 62 66 dc c1 de fb 01 ff 7f d7 26 02 01 06 1a ff 4c 00 02 15 00 00 00 01 7f 48 92 db f5 8c 11 9d c0 98 49 b7 05 02 2a c7 f8  
   00 03 11 e7 bb 3e 29 7b 01 ff 7f be 25 02 01 06 1a ff 4c 00 02 15 00 00 00 01 76 7d 25 88 86 36 5b b1 fa 2f 31 41 04 07 00 2b f8
-1 0  1  2  3   4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 
   type | mac             |bits |tx|rs|pr|flags   |le|us|idmfg|id?  |     UUID                                      |major|minor|tx
   const| id              |const   |var  |const   | const           |       id                                      |var                
                                                               cccccccccccccccccrrrrrrrrrrrrccccccccccccccccccccc    

HB ble5 
   00 03 95 39 6e 74 da 05 01 ff 7f c0 27 02 01 06 16 ff b1 bf 00 1c 5f 01 00 95 39 6e 74 da 05 00 00 00 00 00 f8 72 d3 03 08 48 42 
43 00 03 af bf cf df ef ff 01 ff 7f f2 26 02 01 06 16 ff bf b1 00 00 7d 01 00 ff ff ff ff ff ff 00 00 00 00 00 f8 42 c4 03 08 48 42
   00 03 41 92 11 c2 a3 4c 01 ff 7f c1 26 02 01 06 16 ff b1 bf 00 00 0b 01 00 41 92 11 c2 a3 4c 00 00 00 00 00 f8 41 ab 03 08 48 42 
   00 03 a4 59 b0 20 45 81 01 ff 7f ca 26 02 01 06 16 ff b1 bf 00 00 0d 01 00 a4 59 b0 20 45 81 00 00 00 00 00 f8 4d b4 03 08 48 42   
-1 0  1  2  3   4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 
   type | mac             |bits |tx|rs|pr|flags   |le|us|idmfg|pid|cnt |dev  + id              |ty|exdata     |tp|crc  |ln|st|name
   const| id              |const   |var  |const   | const         |var | id                    |var              |crc  |const
                                                               cccccccccccccccccrrrrrrrrrrrrccccccccccccccccccccc    

   
len 44  change to 43
0:type:00 03
2:mac: af bf cf df ef ff
8: 01 ff 
10:txpower:7f 
11:rssi: f2
12:port: 26
13-15: 02 01 06 длина тип флаги
16: 17 длина
17: ff пользовательский тип
18-19: fe c0 ид производителя
#! 11 длина exclude
20! 00 ид пакета широковещательный
21-22! 00 84 счетчик пакета
23:! 01 тип устройства
24:! 00 подтип
25-30! ff ff ff ff ff ff ид
31! 00 тип данных
33-35! 00 00 00 00 данные    
36! f8 мощность передачи  
37! 57 контрольная сумма  
38! 2b контрольная сумма 
39 03 длина

40 08 тип короткое имя
41-42 48 42  HB
"""





def logi(s):
    logname='/home/bfg/bgate/bdata'
    logging.basicConfig(format='%(asctime)s | %(message)s', datefmt='%Y/%m/%d %H:%M:%S ', filename=logname, level=logging.INFO)
    logging.info(s)
    print(s)



class SerialBgate(threading.Thread):


    def __init__(self,port):
        print("__init__")
        threading.Thread.__init__(self)  
        self.port=port

        self.queue = queue.Queue() 
        self.cnt = 0
        self.mqttclient=mqtt.Client("bfg")
        self.mqttclient.connect("192.168.31.204")
        #self.mqttclient.subscribe("

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
            
    def DecodeB(self,dpin):
        dpo={}
        if len(dpin)>=43: #наши пакеты 43
            dpo["mac"]=dpin[2:8]
            dpo["raw"]=dpin
            if dpin[16:19]==b'\x1a\xffL\x00': #apple beacon ble4
                dpo["type"]=1
                dpo["uuid"]=dpin[22:38]
                dpo["cnt"]=dpin[38]*256+dpin[39]
                dpo["ext"]=dpin[40]
                dpo["exd"]=dpin[41]
                dpo["txpower"]=dpin[42] if dpin[42] < 127 else dpin[42]-256
            if dpin[16:19]==b'\x16\xff\xb1\xbf': #andrew beacon ble5
                dpo["type"]=2
                dpo["uuid"]=dpin[23:31]
                dpo["cnt"]=dpin[21]*256+dpin[22]
                dpo["ext"]=dpin[31]
                dpo["exd"]=dpin[32:36]                
                dpo["txpower"]=dpin[42] if dpin[42] < 127 else dpin[42]-256
        return dpo

    def SerialDaemon(self):
       
        with serial.Serial(self.port, 115200, timeout=1) as ser:  
            while(self.runing):
                sib=ser.read()
                if len(sib)>0:
                    ib=sib[0]
#                    print(sib,ib)
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


                        print(self.port,end=': ')
#                        print("len %d lp %d id %d "%(len(self.datapack),self.leng,self.idpack),end='')
#                        for d in self.datapack:
#                            print("%02x "%d,end='')
#                        print(' ')



#                        if len(self.datapack)==43:
                        if len(self.datapack)>=43: # and self.datapack[39:]==b"\x03\x08HB":

                            dp=DecodeB(self.datapack)
                            print(dp)
                            self.mqttclient.publish("BFG5",msgpack.backb(dp,use_bin_type=True))
                                                    
#                            print(self.port,end=': ')
#                            print("len %d lp %d id %d "%(len(self.datapack),self.leng,self.idpack),end='')
#                            for d in self.datapack:
#                                print("%02x "%d,end='')
#                            print(' ')

#                            if self.datapack[0:6] in bfiltermac :
                            logi('p:%s;mac:%02x%02x%02x%02x%02x%02x; %2x%2x id:%02x%02x%02x%02x%02x%02x%02x%02x n:%6d txpower:%3d; rssi:%d; ch:%d'%(
                            self.port,
                            int(self.datapack[2]),
                            int(self.datapack[3]),
                            int(self.datapack[4]),
                            int(self.datapack[5]),
                            int(self.datapack[6]),
                            int(self.datapack[7]), #mac

                            int(self.datapack[19]), #manid
                            int(self.datapack[18]), #manid2

                            int(self.datapack[23]), #dev type
                            int(self.datapack[24]), #dev subtype
                            int(self.datapack[25]), #id
                            int(self.datapack[26]), #id
                            int(self.datapack[27]), #id
                            int(self.datapack[28]), #id
                            int(self.datapack[29]), #id
                            int(self.datapack[30]), #id

                            int(self.datapack[21])*256+int(self.datapack[22]),

                            int(self.datapack[36]), #txpower
                            int(self.datapack[11])-256, #rssi
                            int(self.datapack[12]), #channel


                                                    
#                            int(self.datapack[6])*256+int(self.datapack[7]),
#                            int(self.datapack[8]),
#                            int(self.datapack[9]),
#                            int(self.datapack[10]),# if int(self.datapack[10]>127,
#                            int(self.datapack[11])-256,
#                            int(self.datapack[12]),

                            ))
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
for  arg in range(1,len(sys.argv)):
    print("<",arg,">")
    ls[arg]=SerialBgate(sys.argv[arg])
    ls[arg].start()

t=input("Enter to exit")

for  b in ls:
    ls[b].stop()
    ls[b].join()





