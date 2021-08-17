import serial
#import numpy as np
import math
import os
import sys
import shutil
import threading
import time
import queue
import datetime
import logging
import uuid
import msgpack
import paho.mqtt.client as mqtt 
#from flask import Flask, jsonify
#from flask import request
#from flask import send_from_directory, send_file, safe_join
#from flask import flash, redirect, url_for
#from werkzeug.utils import secure_filename
#from werkzeug.contrib.fixers import ProxyFix
import json
import requests
import threading
import shelve
import hashlib
#import nmcli
import socket,fcntl,struct
import requests
import ipaddress
#local modules
import bgconfig
import gpledthread


ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])
UPLOAD_FOLDER = '/var/www/upload'

#app = Flask(__name__)
#app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
#app.secret_key = "my super secret key"

#app.wsgi_app = ProxyFix(app.wsgi_app)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



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







def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(), 0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15].encode('utf-8'))
        )[20:24])





def logi(s):
    logname='/home/bfg/bgate/bdata.log'
    logging.basicConfig(format='%(asctime)s | %(message)s', datefmt='%Y/%m/%d %H:%M:%S ', filename=logname, level=logging.INFO)
    logging.info(s)
    #print(s)









class bgmqtt(threading.Thread):


    def __init__(self):
        global gmqttclient
        print("__init__")
        threading.Thread.__init__(self)  

        self.isconnected=False
        self.queue= queue.Queue()       
        self.cnt = 0
        self.mqttclient=mqtt.Client(config.read("macgate"))
        self.mqttclient.on_connect=self.on_connect
        self.mqttclient.on_disconnect=self.on_disconnect
        config.print()
        print('brokerip',config.read('brokerip'))
        
    
        
    def connect(self):
        ip,port = config.read("brokerip"),config.read("brokerport")
        print(f"try to connect {ip}:{port}")
        
        
        try:
            
            self.mqttclient.connect(ip,port=port)
            time.sleep(1)
            #self.mqttclient.loop_start() 
            self.isconnected=True
        except:
            self.isconnected=False
            pass
        if not self.isconnected:
            print(f"fall\ntry to connect {ip=} {port=}")
            try:
                #self.mqttclient.loop_start()                 
                self.mqttclient.connect(ip,port=port)
                time.sleep(1)
                self.isconnected=True
            except:
                self.isconnected=False
                pass 
        if not self.isconnected:
            print("fall - quit")
            #quit()
            
            
    def disconnect(self):
        self.mqttclient.disconnect()
                        
            
    def publish(self,data):
        self.queue.put(data)
        
        
    def publoop(self):
        while self.running:
            while self.running and self.isconnected:
                data = self.queue.get()
                ret=self.mqttclient.publish(data['topic'],data['msg'])
                if ret[0]!=0:
                    self.queue.put(data)
                    logi('cant sent message to %s'%(data))
            self.disconnect()
            time.sleep(0.5)
            self.connect()
            time.sleep(1)
            

        
    def on_disconnect(self,client,userdata,rc):
        logi("disconnect mqtt %d"%rc)
        self.isconnected=False
        #quit()
    
    def on_connect(self,client,eserdata,flag,rc):
        global isconnected
        if rc==0:
            print("connected ok")
            isconnected= True   
        else:
            print("bad connect",rc)
            isconnected= False

    def run(self): 
        print("run")
        self.running=True
        #self.mqttclient.loop_forever()
        self.mqttclient.loop_start()
        self.publoop()
        
        
    def stop(self):
        print("stop")
        self.running=False        
        self.mqttclient.loop.stop()        

    #def Print(self,txt):
        #if(not self.queue.empty()):
            #print(txt,self.queue.get())


class bgserial(threading.Thread):

    def __init__(self,port):
        print("__init__")
        threading.Thread.__init__(self)  
        self.port=port
        

        
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
        return len(self.pack)<self.length+7 and len(self.pack)>2
        
            
    def paddbyte(self,serstr):
        
        for s in serstr:
            #print(s,bytes([s]).hex(),self.f_ab(s), self.f_ba(s) , self.f_dl(s) , self.f_ta(s))

            if self.f_ab(s) or self.f_ba(s) or self.f_dl(s) or self.f_ta(s):
                self.pack+=bytes([s])
            else:
                if len(self.pack)>20:
                    #print(self.pack.hex(' '))
                    crc1 = struct.unpack('>H',self.pack[-2:])
                    crc2 = zlib.crc32(self.pack[:-2]) & 0xffff
                    print(f"{crc1=} {crc2=}")
                    if crc1==crc2:
                        self.datapack=self.pack[5:-2]
                        #print('data',self.pack[5:-2].hex(' '))
                        if len(self.datapack)==43:
                            d=BlAdvCoder.decode2(self.datapack)
                            #publish
                            ret=bgmq.publish({'topic':'BFG5','msg':msgpack.packb(d,use_bin_type=True)})                            
                            print(d)               
                        else:
                        #if len(self.datapack)==44:
                            dc=BlAdvCoder.aesdecode(self.datapack)
                            #config
                            print(dc)      
                        
                            #logi("%s %s %d %d %d %d %s %s"%(dp["gate"],dp["mac"],dp["band"],dp["rssi"],dp["txpower"],dp["cnt"],dp["uuid"],ret))
                        
                    self.pack=b''
               

    def reader(self):
       
        with serial.Serial(self.port, 115200, timeout=1) as self.ser:  
            while(self.runing):
                self.paddbyte(ser.read())

    def write(self,data):
        self.ser.write(data)


    


if __name__ == '__main__':
    #ls={}

    
    led=gpledthread.gpled('r1 s1 r0 s1') 
    led.start()
    led.setprog('g1 s1 g0 s1')
  
    print("Print configuration")
    config=bgconfig.Configuration()
    config.print()

    mqt=bgmqtt()
    mqt.start()
    
    bgs=bgserial("/dev/ttyS1")
    bgs.start()
    
    
    
    
    
    ##for c in config:
    ##    print(c,config[c])        
    ##argv=sys.argv
    #argv=["i","/dev/ttyS1"]
    #for  arg in range(1,len(argv)):
        #print("<",arg,">")
        ##ls[arg]=SerialBgate(argv[arg])
        ##ls[arg].start()
    
    
    ##app.run(debug=True)
    #while True:
        #time.sleep(1)
    ##t=input("Enter to exit")
    
    ##for  b in ls:
        ##ls[b].stop()
        ##ls[b].join()
    
    
    
    


"""
для nmcli нужно доустановить пакет dnsmasq-base
"""