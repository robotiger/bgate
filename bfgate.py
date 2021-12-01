# git clone https://github.com/robotiger/bgate.git
import serial
#import numpy as np
import math
import os
import sys
import shutil
import threading
import time
import random
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
import zlib
import nmcli
import socket,fcntl,struct
import requests
#import ipaddress
#local modules
import bgconfig
import bgcoder
import bgled
import zmq


ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])
UPLOAD_FOLDER = '/var/www/upload'

#app = Flask(__name__)
#app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
#app.secret_key = "my super secret key"

#app.wsgi_app = ProxyFix(app.wsgi_app)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(), 0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15].encode('utf-8')))[20:24])

#kjlkjlkj



def logi(s):
    logname='/home/bfg/bgate/bdata.log'
    logging.basicConfig(format='%(asctime)s | %(message)s', datefmt='%Y/%m/%d %H:%M:%S ', filename=logname, level=logging.INFO)
    logging.info(s)
    #print(s)




class bgzmq(threading.Thread):


    def __init__(self,stop_event):
        #global gmqttclient
        print("__init__")
        threading.Thread.__init__(self)  
        self.stop_event = stop_event
        self.queue= queue.Queue()       
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUSH)
        self.socket.connect(f'tcp://{config.read("hostzmqip")}:{config.read("hostzmqport")}')
                                   
    def connect(self):   
        if self.context.closed or self.socket.closed:
            self.context=zmq.Context()
            self.socket=self.context.socket(zmq.PUSH)      
            self.socket.connect(f'tcp://{config.read("hostzmqip")}:{config.read("hostzmqport")}')
            
    def __len__(self):
        return self.queue.qsize()
             
    def publish(self,data):
        self.queue.put(data)
        if self.queue.qsize()>2000: #ограничим длину буфера, на всякий
            self.queue.get()
            #print("bgzmq bufer overflow")
        
    def publoop(self):
        ## publoop ждем сообщений в очереди, как появятся отправляем
        print('publoop',self.stop_event.is_set())
        while not self.stop_event.is_set():
            self.connect()
            try:
                data = self.queue.get(timeout=2)
            except:
                data = None
                #print('qeue get timeout')
            if not data is None:
                self.socket.send(data)
        #self.socket.disconnect()
            

    def run(self): 
        print("run")
        self.publoop()
        
        


class bgmqtt(threading.Thread):


    def __init__(self,stop_event):
        #global gmqttclient
        print("__init__")
        threading.Thread.__init__(self)  
        self.stop_event = stop_event
        self.isconnected=False
        self.queue= queue.Queue()       
        self.cnt = 0
        self.mqttclient=mqtt.Client(config.read("macgate"))
        self.mqttclient.on_connect=self.on_connect
        self.mqttclient.on_disconnect=self.on_disconnect
        config.print()
        print('config read brokerip',config.read('brokerip'))
        
    
        
    def connect(self):
        ip,port = config.read("brokerip"),int(config.read("brokerport"))
        print(f"try to connect {ip}:{port}")
        if not self.isconnected:            
            try:
                print(f"first to try to connect {ip}:{port}")
                self.mqttclient.connect(ip,port=port)
                print(f"first  try to connect {ip}:{port}")
    
                time.sleep(1)
                #self.mqttclient.loop_start() 
                self.isconnected=True
            except:
                self.isconnected=False
                print(f"first except to connect {ip}:{port}")
                
                pass
            if not self.isconnected:
                print(f"fall\ntry to connect {ip=} {port=}")
                try:
                    #self.mqttclient.loop_start()                 
                    self.mqttclient.connect(ip,port=port)
                    print(f"second try to connect {ip}:{port}")
                    
                    time.sleep(1)
                    self.isconnected=True
                except:
                    self.isconnected=False
                    print(f"second except to connect {ip}:{port}")
                    
                    pass 
            if not self.isconnected:
                print("fall - quit")
                #quit()
            
            
    def disconnect(self):
        self.mqttclient.disconnect()
                        
            
    def publish(self,data):
        self.queue.put(data)
        
        
    def publoop(self):

        print('publoop',self.stop_event.is_set())
#        while self.running:
        while not self.stop_event.is_set():
            self.connect()
            time.sleep(1)            
            #print('publoop while')
#            while self.running and self.isconnected:
            while self.isconnected and not self.stop_event.is_set():
                try:
                    data = self.queue.get(timeout=2)
                    #print(f'qget {data}')
                except:
                    data = None
                    #print('qeue get timeout')
                if not data is None:
                    ret=self.mqttclient.publish(data['topic'],data['msg'])
                    if ret[0]!=0:
                        self.queue.put(data)
                        logi('cant sent message to %s'%(data))
            self.disconnect()
            time.sleep(0.5)
            
        self.mqttclient.loop_stop()      

        
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
        self.mqttclient.loop_stop()   
        
    def connected(self):
        return self.isconnected

    #def Print(self,txt):
        #if(not self.queue.empty()):
            #print(txt,self.queue.get())


class bgserial(threading.Thread):

    def __init__(self,stop_event,port):
        print("__init__")
        threading.Thread.__init__(self)  
        self.stop_event=stop_event
        self.port=port
        self.pack=b''
        self.length=1
        
    def run(self): 
        print("run serial")
        self.reader()
        

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
        #print(s,end=' ')
        return len(self.pack)<self.length+7 and len(self.pack)>2


    def reader(self):
        buf=b''
        with serial.Serial(self.port, 115200, timeout=1) as self.ser:  
            while(not self.stop_event.is_set()):
                buf=self.ser.read() #!?
                buf=self.paddbyte(buf)        
            
    def paddbyte(self,serstr):
        for s in serstr:  
            #print(f'{bytearray([s]).hex()},{self.f_ab(s)=} {self.f_ba(s)=} {self.f_dl(s)=} {self.f_ta(s)=} len={len(self.pack)}')
            if self.f_ab(s) or self.f_ba(s) or self.f_dl(s) or self.f_ta(s):
                self.pack+=bytes([s]) #добавляем принятые байты в пакет
            else: 
                self.analize_packet()
                #self.pack=bytearray([s]) # новый пакет начинается с [s]     
                self.pack=bytes([s]) # новый пакет начинается с [s]     
                
    def analize_packet(self):   
        if len(self.pack)>20: # пакет принят. проверим контрольную сумму 
            #print(self.pack.hex(' '))
            crc1 = struct.unpack('>H',self.pack[-2:])[0]
            crc2 = zlib.crc32(self.pack[:-2]) & 0xffff
            #print(f"{crc1=} {crc2=}")
            if crc1==crc2: # 
                self.datapack=self.pack[5:-2]
                #print('data',self.datapack.hex(' '),'len',len(self.datapack))
                dc =bgcoder.BlAdvCoder.aesdecode(self.datapack) #попробуем расшифровать
                if dc: # удачно расшифровали используем для конфигурирования
                    logi(f' cfg {dc[0]} data {dc[1]}')                        
                    #print(f'закодирована {dc[0]} {dc[1]}')   
                    if dc[0]==707:
                        self.beaconled(dc[1])
                    else:
                        config.configurate(dc[0],dc[1].decode())
                else: 
                    d=bgcoder.BlAdvCoder.decode3(self.datapack)
                    if 'mfg' in d:
                        d['gate']=config.read('macgate')
                        d['factory']=config.read('factory')
                        d['timegate']=time.time()
                        topic=config.read('brokertopic')
                        #publish
                        #ret=mqt.publish({'topic':topic,'msg':msgpack.packb(d,use_bin_type=True)})      
                        zmqt.publish(msgpack.packb(d,use_bin_type=True))
                    #print(d)  
          
               


    def write(self,data):
        self.ser.write(data)
    
    def beaconled(self,data):
        enc_data=b'\xab\xba\x0f\00\04'+data
        crc32=zlib.crc32(enc_data)
        pack=struct.pack('>20sH',enc_data,crc32&0xffff)
        self.ser.write(pack)

    def commandled(self,mac,r,g,b,t,p,o):
        #mac beacon str ,red ,green, blue, time sec,  period msec , ontime msec
        try:
            enc_data= struct.pack('>5s6s3B3h',b'\xab\xba\x0f\00\04',bytes.fromhex(mac),r,g,b,t,p,o)
        except:
            return None
        crc32=zlib.crc32(enc_data)
        #print(crc32.to_bytes().hex(' '))
        return struct.pack('>20sH',enc_data,crc32&0xffff)
    
"""   for test
mac='c65a9cf5d474'        
cmd=commandled('c65a9cf5d474',4,5,6,259,259,259)
print('cmd',cmd.hex(' '))
"""


if __name__ == '__main__':

    stop_event = threading.Event()

    print("Print configuration")
    config=bgconfig.Configuration(stop_event)
    config.configurate(700,'R1 r1') # моргаем красным пока включаемся
    
   
    
    config.print()

    #mqt=bgmqtt(stop_event)
    #mqt.start()

    zmqt=bgzmq(stop_event)
    zmqt.start()

    
    bgs=bgserial(stop_event,"/dev/ttyS1")
    bgs.start()
    
    
    while(not stop_event.is_set()):
        #print(threading.enumerate())
        time.sleep(15)
        #if mqt.isconnected:
            #config.configurate(700,'r1 G1') # mqtt соединение установлено выключим красный и включим зеленый
            ##bgs.write(bgs.commandled('c65a9cf5d474',220,220,1,1,450,15))
        #else:
            #config.configurate(700,'R1 g1') #иначе включим красный и отключим зеленый
            #time.sleep(45)
            #mqt.connect()

        if zmqt.socket.closed or len(zmqt)>10:
            config.configurate(700,'R1 g1') # mqtt соединение установлено выключим красный и включим зеленый            
        else:
            config.configurate(700,'r1 G1') #иначе включим красный и отключим зеленый

    
    
        wificon='no wifi'
        for d in nmcli.device.wifi():
            if d.in_use:    
                wificon='wifi'
        for c in nmcli.connection():
            if c.conn_type=='wifi' and c.device!='--' and c.name=='Hotspot':
                wificon='hotspot'
         
        ledwifi={
            'no wifi': 'y1',
               'wifi': 'Y1',
            'hotspot': 'Y1 y1'
                }

        config.configurate(700,ledwifi[wificon]) 
        #if wificon=='no wifi':
            #config.f_nmcli_connect_to_wifi(100,random.randbytes(4).hex())
        #    config.f_nmcli_connect_to_wifi(100,random.randint(0,4000000000).to_bytes(4,'big').hex())
zmqt.join()
bgs.join()
bgled.bgled.ledoff()
config.close()


"""
для nmcli нужно доустановить пакет dnsmasq-base
для reboot создать /etc/shutdown.allow  с именем юзера
"""
"""
    def f_nmcli_connect_to_wifi(self,cfg,data):
        ssid=self.read(cfg+1)
        pas=self.read(cfg+2)
        idcon=self.read(cfg+3)
        print(f'{idcon=} {data=} {ssid=} {pas=} {cfg=}')
        if idcon!=data: #это не тот запрос,что был в прошлый раз"""