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
from flask import Flask, jsonify
from flask import request
from flask import send_from_directory, send_file, safe_join
from flask import flash, redirect, url_for
from werkzeug.utils import secure_filename
from werkzeug.contrib.fixers import ProxyFix
import json
import requests
import threading
import shelve
import hashlib
import nmcli
import time


import socket,fcntl,struct
import requests
import ipaddress
#local modules
import configbgate
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



gmqttclient=None




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
        global gmqttclient
        print("__init__")
        threading.Thread.__init__(self)  
        self.port=port
        self.isconnected=False
        self.queue = queue.Queue() 
        self.cnt = 0
        self.mqttclient=mqtt.Client(config.read("macgate"))
        gmqttclient=self.mqttclient
        self.mqttclient.on_connect=self.on_connect
        self.mqttclient.on_disconnect=self.on_disconnect
        self.Connect()
        
    def Connect(self):
        print("try to connect ",config["database"],config["brokerport"])
        try:
            
            self.mqttclient.connect(config["database"],port=config["brokerport"])
            time.sleep(1)
            #self.mqttclient.loop_start() 
            self.isconnected=True
        except:
            self.isconnected=False
            pass
        if not self.isconnected:
            print("fall\ntry to connect ",config["broker"],config["brokerport"])
            try:
                #self.mqttclient.loop_start()                 
                self.mqttclient.connect(config["broker"],port=config["brokerport"])
                time.sleep(1)
                self.isconnected=True
            except:
                self.isconnected=False
                pass 
        if not self.isconnected:
            print("fall - quit")
            quit()
            
    def Publish(self,topic,msg):
        ret=self.mqttclient.publish(topic,msg)
        if ret[0]!=0:
            #logi("cant sent mqtt %s %s"%(topic,ret))
            #quit()
            
            self.mqttclient.disconnect()
            time.sleep(1)
            self.mqttclient.connect(config["broker"],port=config["brokerport"])
            time.sleep(1)
            ret=self.mqttclient.publish(topic,msg)
            if ret[0]!=0:
                logi('cant sent message to %s'%(topic))
        return ret
        
    def on_disconnect(self,client,userdata,rc):
        logi("disconnect mqtt %d"%rc)
        quit()
    
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
        self.runing=True
        self.SerialDaemon()
        
        
    def stop(self):
        print("stop")
        self.runing=False        

    def Print(self,txt):
        if(not self.queue.empty()):
            print(txt,self.queue.get())



    def SerialDaemon(self):
       
        with serial.Serial(self.port, 115200, timeout=1) as self.ser:  
            while(self.runing):
                sib=self.ser.read()
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


                        #print(self.port,end=': ')
#                        print("len %d lp %d id %d "%(len(self.datapack),self.leng,self.idpack),end='')
#                        for d in self.datapack:
#                            print("%02x "%d,end='')
#                        print(' ')



#                        if len(self.datapack)==43:
                        if len(self.datapack)>=13: # and self.datapack[39:]==b"\x03\x08HB":

                            dp=self.DecodeB(self.datapack)
#                            print(dp)

                            if "mfg" in dp:
                                #print(config["topic"],dp["gate"],dp["mfg"],dp["mac"],dp["rssi"],dp["band"],dp["txpower"],dp["cnt"],dp["uuid"])
                                ret=self.Publish(config["topic"],msgpack.packb(dp,use_bin_type=True))
                                logi("%s %s %d %d %d %d %s %s"%(dp["gate"],dp["mac"],dp["band"],dp["rssi"],dp["txpower"],dp["cnt"],dp["uuid"],ret))
#                                self.mqttclient.publish(config["topic"]+"/"+config["macgate"],msgpack.packb(dp,use_bin_type=True))
                                                    
                                #logi('p:%s;mac:%02x%02x%02x%02x%02x%02x; %2x%2x id:%02x%02x%02x%02x%02x%02x%02x%02x n:%6d txpower:%3d; rssi:%d; ch:%d'%(

                                                    
            


        
    
    


class wifistate(threading.Thread):


    def __init__(self):
        print("__init__")
        threading.Thread.__init__(self)  
        nmcli.disable_use_sudo()
        
    def wifitest(self):            
        for d in nmcli.device.wifi():
            if d.in_use:
                wifid=d.to_json()
                #self.mqtt
                #print(d)
                #nmcli.connection.down(d.ssid)        
        

    #def wifitest(self):
        #while(self.runing):
            #try:
                #resp=os.popen("nmcli device wifi list")        
                #res=resp.readlines()
                #for red in res:
                    #col = red.split()
                    #if col[0]=='*':
                        ##print(col[6])
                        #dpo["gate"]=config["macgate"]
                        #wifid={"ssid":col[1],"chan":col[3],"signal":col[6],"gate":config["macgate"]}
                        #self.mqttclient.publish("WIFI",msgpack.packb(wifid,use_bin_type=True))
                

            #except:
                #print('wifi is not connected') 
            #time.sleep(30)
        
    def run(self): 
        print("run")
        self.runing=True
        self.wifitest()
        
        
    def stop(self):
        print("stop")
        self.runing=False        



if __name__ == '__main__':
    ls={}
    #config=shelve.open("/home/bfg/bgate/config")
    
    #try:
        #resp=os.popen("nmap --open -p 5432 %s.%s.%s.0/24"%
                      #tuple(get_ip_address('wlan0').split('.')[0:3])
                      ##tuple(get_ip_address('wlp7s0').split('.')[0:3])
                     #)
        #res=resp.readlines()
        #for d in res:
            ##print(d[0:20])
            #if d[0:20]=='Nmap scan report for':
                #if '(' in d:
                    #config["database"]=d[d.find('(')+1:d.find(')')]
                #else:    
                    #config["database"]=d[21:-1]
    #except:
        #print('wifi is not connected')
    
    
    gpled=gpledthread.gpled('r1 s1 r0 s1') 
    gpled.start()
    gpled.setprog('g1 s1 g0 s1')
  
    print("Print configuration")
    config=configbgate.Configuration()
    config.print()
    
    #for c in config:
    #    print(c,config[c])        
    #argv=sys.argv
    argv=["i","/dev/ttyS1"]
    for  arg in range(1,len(argv)):
        print("<",arg,">")
        #ls[arg]=SerialBgate(argv[arg])
        #ls[arg].start()
    
    
    #app.run(debug=True)
    while True:
        time.sleep(1)
    #t=input("Enter to exit")
    
    #for  b in ls:
        #ls[b].stop()
        #ls[b].join()
    
    
    
    


"""
нужно доустановить пакет dnsmasq-base

список действующих подключений. если подключенний нет создадим хотспот
nmcli conn show -a

список устройств
nmcli dev


Подключаться к сети вайфай
nmcli dev wifi connect Xiaomi1 password "12345pibfg"

создать хотспот.   указывать ssid нужно уникальный. можно по маку или уиду
nmcli dev wifi hotspot ifname wlx1cbfce465b17 ssid tea password "12345pibfg"
nmcli dev wifi hotspot ssid tea password "12345pibfg"

отключить hotspot, 
nmcli con down Hotspot

отключенный хоспот включить
nmcli con up Hotspot


удалить хотспотТекущее время 0
nmcli conn del Hotspot

Характеристики подключения пожалуй интересны мощность сигнала и канал
nmcli dev wifi
IN-USE  SSID     MODE            CHAN  RATE      SIGNAL  BARS  SECURITY 
*       Xiaomi1  Инфраструктура  6     117 МБ/с  71      ▂▄▆_  WPA2     

hcitool test
"""
