import os
import shutil
import shelve
import uuid
import base64
import nmcli
import threading
import hashlib

import bgled


def ip_addresses():
    ip=[]
    for a in nmcli.device.show_all():
        if int(a['GENERAL.STATE'].split()[0])==100:
            ip.append(a['IP4.ADDRESS[1]'].split('/')[0].split('.')[3])
    return ip



class Configuration():
    def __init__(self,stop_event):
        print('Config __init__')
        self.led=bgled.bgled(stop_event)
        self.led.setprog('g0 y0 r1') #все выключим сначала
        self.led.start()
        self.stop_event=stop_event
        configfilename ="/home/bfg/bgate/config"
        nmcli.disable_use_sudo()    
        self.on=False
        self.config=shelve.open(configfilename) 

        """        
        try:
            print('try to open config file')
            self.config=shelve.open(configfilename) 
            print('config file opened')
            #print('config shelve',config)
        except:
            if os.path.isfile(configfilename+'.res'):
                ## если есть резервный файл конфигурации используем его
                os.rename(configfilename,configfilename+'.bro')
                shutil.copyfile(configfilename,configfilename+'.bro')
                shutil.copyfile(configfilename+'.res',configfilename)
            try:
                self.config=shelve.open(configfilename) 
            except:
                os.remove(configfilename) #не открывается копия удалим её и создадим новую конфигурацию
            
                try:
                    self.config=shelve.open(configfilename) 
                except:
                    # файл и копия не открываются, новый не создается
                    # сделаем словарь. работать будет, но после конфигурирования. 
                    # ситуация почти невероятная, нужен человек
                    #self.config={}
                    print('config is dictionary')
        """
        self.configloaded=True
        self.funclist()        # коды параметров конфигурации. в интерфейсе числа. в программе и файле названия.

#        self.tomap={}
#        for name in self.mapto:
#            self.tomap[self.mapto[name]]=name

        if  self.read("macgate") is None:
            self.write("macgate","%012x"%uuid.getnode())
            self.write("uuid",uuid.uuid1())
            self.write("brokerip","192.168.31.20")
            self.write("brokerport",'1883')
            self.write("brokertopic","BFG5")
            self.write("factory","0012")        
            


            
    def read(self, parameter):
        try:
            idx=int(parameter)
            parameter=self.func[idx]
        except:
            pass
        if isinstance(parameter,str):
            return self.config.get(parameter,None)        
        return None
        

    def write(self, parameter, value):
        try:
            idx=int(parameter)
            parameter=self.func[idx]
        except:
            pass
        if isinstance(parameter,str):
            print(f'store into config {parameter=} {value=}')
            self.config[parameter]=value
        try:
            print('try to sync')
            self.config.sync()
            print('sync done')
        except:
            pass #dict cant be saved
        
    def print(self):
        for v in self.config:
            print(v,self.config[v])
        
    def data(self):
        return self.config
    
    def close(self):
        self.config.close()
        
        

    def f_nmcli_connect_to_wifi(self,cfg,data):
        ssid=self.read(cfg+1)
        pas=self.read(cfg+2)
        idcon=self.read(cfg+3)
        print(f'{idcon=} {data=} {ssid=} {pas=} {cfg=}')
        if idcon!=data: #это не тот запрос,что был в прошлый раз
            if not ssid is None and not pas is None:
                connected=None
                for d in nmcli.device.wifi():
                    if d.in_use:
                        connected=d.ssid
                if connected: # and connected!=ssid:
                    print(f"disconnect {connected} connect to {ssid} {pas}")
                    nmcli.connection.down(connected) #сначала отключиться если были подключены
                try:    
                    nmcli.device.wifi_connect(ssid=ssid,password=pas) # потом подключится к новой
                except:
                    pass
                self.write(cfg+3,data) 
                    #сохраним id при следующем получении блютус команды с тем же ид 
                    #nmcli вызываться не будет
                for c in nmcli.connection(): 
                    print(c)                    


    def f_nmcli_hotspot_wifi(self,cfg,key):
        skey=self.read(203)
        if skey != key:            
            self.write(203,key)
            mac=self.read('macgate')
            factory=self.read('factory')
            print(mac,factory,cfg,key)
            ssid=b'BG'+base64.b64encode(bytes.fromhex(mac)+factory.encode()) 
            pas=base64.b64encode(hashlib.sha1((mac+str(key)).encode()).digest()[:12])
            if not ssid is None and not pas is None:
                try:
                    print(f"hotspot {ssid=} {pas=}")
                    connected=None
                    for d in nmcli.device.wifi():
                        if d.in_use:
                            connected=d.ssid
                    if connected: #!=ssid and connected:
                        nmcli.connection.down(connected) #сначала отключиться
                    
                    print(f"hotspot {ssid=} {pas=}")
                    try:
                        nmcli.device.wifi_hotspot(con_name= 'Hotspot', ssid = ssid, password= pas)
                    except:
                        print('except')
                    for c in nmcli.connection(): 
                        print(c)                    
                    
                except:
                    pass
    
    def f_nmcli_disconnect(self,cfg,data):
        for d in nmcli.device.wifi():
            if d.in_use:
                try:
                    nmcli.connection.down(d.name) # отключиться если подключен
                except:
                    pass
                
    def f_nmcli_deleteconnection(self,cfg,data):
        try:
            print(f'delete connection {data}')
            nmcli.connection.delete(data)
            print('deleted')            
        except:
            pass

    def f_nmcli_downconnection(self,cfg,data):
        try:
            print(f'down connection {data}')
            nmcli.connection.down(data)
            print('down')
        except:
            pass
    
    def f_ospopen(self,cfg,data):
        print(f'{cfg=} {data=}')
        res=os.popen(data) #.decode())
        res.close()
    
    def f_ledprog(self,cfg,data):
        #print(f'f_ledprog {cfg=} {data=}')
        self.led.setprog(data) #.decode())            

    def f_ledwhoimi(self,cfg,data):
        f=self.read('factory')
        if f==data:
        #print(f'f_ledprog {cfg=} {data=}')
            self.led.setprog('R0 g1 r0 G1') #.decode())            

    def f_ledip(self,cfg,data):
        print(f'{data} in {ip_addresses()}')
        if data in ip_addresses():
            self.led.setprog('R0 G1 R0 g1') #.decode())            


    def f_exit(self,cfg,data):
        self.stop_event.set()

    def f_extcommand(self,cfg,data):
        #self.stop_event.set()
        with open('/home/bfg/bgate/extcommand.sh','w') as ef:
            ef.write(data) #.decode())
    
    def f_mqtt_connect(self,cfg,data):
        pass

    def funclist(self):
        self.func={
            
            1:'macgate',
            2:'uuidgate',
            3:'factory',
            100:self.f_nmcli_connect_to_wifi,
            101:'wifissid',
            102:'wifipassword',
            110:self.f_nmcli_connect_to_wifi,
            111:'wifissid1',
            112:'wifipassword1',
            120:self.f_nmcli_connect_to_wifi,
            121:'wifissid2',
            122:'wifipassword2',

            180:self.f_nmcli_disconnect,
            181:self.f_nmcli_deleteconnection,
            182:self.f_nmcli_downconnection,
            #200:self.f_nmcli_hotspot_wifi,     проблемы исправить. потом включим
            201:'hotspotssid',
            202:'hotspotpassword',
            203:'hotspotkey',
            300:self.f_mqtt_connect,
            301:'brokerip',
            302:'brokerport',
            303:'brokertopic',
            304:'tokenapi',
            333:'brokerconnected',
            700:self.f_ledprog,
            701:self.f_ledwhoimi,
            702:self.f_ledip,
            900:self.f_ospopen,
            905:self.f_extcommand,
            990:self.f_exit
            }
    

    def configurate(self,cfg,data):
        

        if cfg in self.func:
            #есть такой пункт в конфигурации
            if isinstance(self.func[cfg],str):
                #это параметр. добавить ридонли для некоторых. пока так: cfg меньше 100 заводские настройки
                if cfg>=100:
                    print(f" write {cfg=} {data=}")
                    self.write(cfg,data)
            else:
                #это действие. запустим в отдельном потоке
                threading.Thread(target=self.func[cfg],args=(cfg,data)).start()
        
        
        
    
    
    
if __name__=='__main__':
    
    print(get_ip_address())
    
    stop_event = threading.Event()    
    config=Configuration(stop_event)
    config.print()
    
    config.configurate(201,"Xiaomi3")

    config.configurate(101,"Xiaomi_26A3")
    config.configurate(102,"12345pibfg")
    config.configurate(100,"Xiaomi3")
    config.print()
    
    print('test config.read')
    print(config.read("macgate"))
    print(config.read("uuid"))
    print(config.read("brokerip"))
    print(config.read("brokerport"))
    print(config.read("brokertopic"))
        