import os
import shutil
import shelve
import uuid
import base64
import nmcli
import threading
import hashlib

class Configuration():
    def __init__(self):
        
        configfilename ="/home/bfg/bgate/config"
        nmcli.disable_use_sudo()    
        self.on=False
        try:
            self.config=shelve.open(configfilename) 
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
            self.config={}
        self.configloaded=True
        self.funclist()        # коды параметров конфигурации. в интерфейсе числа. в программе и файле названия.

#        self.tomap={}
#        for name in self.mapto:
#            self.tomap[self.mapto[name]]=name
        self.write("factory","003")        
        self.write("macgate","%012x"%uuid.getnode())

        if  self.read("macgate") is None:
            self.write("macgate","%012x"%uuid.getnode())
            self.write("uuid",uuid.uuid1())
            self.write("brokerip","192.168.31.20")
            self.write("brokerport",1883)
            self.write("brokertopic","BFGS5")
            self.write("factory","jyjytgvjxdjr")
            
          
            
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
            self.config[parameter]=value
        try:
            self.config.sync()
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
        if idcon!=data: #это не тот запрос,что был в прошлый раз
            if not ssid is None and not pas is None:
                connected=None
                for d in nmcli.device.wifi():
                    if d.in_use:
                        connected=d.ssid
                if connected and connected!=ssid:
                    print(f"disconnect {connected} connect to {ssid} {pas}")
                    nmcli.connection.down(connected) #сначала отключиться
                    nmcli.device.wifi_connect(ssid=ssid,password=pas) # потом подключится к новой
                    self.write(cfg+3,data) 
                    #сохраним id при следующем получении блютус команды с тем же ид 
                    #nmcli вызываться не будет
                    for c in nmcli.connection(): 
                        print(c)                    


    def f_nmcli_hotspot_wifi(self,cfg,key):
        #key=self.read(cfg+1)
        #if key==None:
        #    key='bgate'
        mac=self.read('macgate')
        factory=self.read('factory')
        print(mac,factory,cfg,key)
        ssid=b'BG'+base64.b64encode(bytes.fromhex(mac)+factory.encode()) 
        pas=base64.b64encode(hashlib.sha1((mac+str(key)).encode()).digest()[:12])
        if not ssid is None and not pas is None:
            try:
                print(f"{ssid=} {pas=}")
                connected=None
                for d in nmcli.device.wifi():
                    if d.in_use:
                        connected=d.ssid
                if connected!=ssid and connected:
                    nmcli.connection.down(connected) #сначала отключиться
                    nmcli.device.wifi_hotspot(con_name= 'Hotspot', ssid = ssid, password= pas)
                    for c in nmcli.connection(): 
                        print(c)                    
                
            except:
                pass
    
    def f_nmcli_disconnect(self,cfg,data):
        for d in nmcli.device.wifi():
            if d.in_use:
                try:
                    nmcli.connection.down(connected) # отключиться если подключен
                except:
                    pass
                
    def f_nmcli_deleteconnection(self,cfg,data):
        try:
            nmcli.connection.delete(data)
        except:
            pass

    def f_nmcli_downconnection(self,cfg,data):
        try:
            nmcli.connection.down(data)
        except:
            pass
        
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
            110:self.f_nmcli_disconnect,
            120:self.f_nmcli_deleteconnection,
            120:self.f_nmcli_downconnection,
            200:self.f_nmcli_hotspot_wifi,
            201:'hotspotssid',
            202:'hotspotpassword',
            300:self.f_mqtt_connect,
            301:'brokerip',
            302:'brokerport',
            303:'brokertopic',
            304:'tokenapi'            
            }
    

    def configurate(self,confdata):
        cfg=confdata[0]
        data=confdata[1]
        if cfg in self.func:
            #есть такой пункт в конфигурации
            if isinstance(self.func[cfg],str):
                #это параметр. добавить ридонли для некоторых. пока так: cfg меньше 100 заводские настройки
                if cfg>100:
                    self.write(cfg,data)
            else:
                #это действие. запустим в отдельном потоке
                threading.Thread(target=self.func[cfg],args=(cfg,data)).start()
        
        
        
    
    
    
if __name__=='__main__':
    config=Configuration()
    config.print()
    
    config.configurate((200,"Xiaomi3"))

    config.configurate((101,"Xiaomi"))
    config.configurate((102,"Xiaomi2"))
    config.configurate((100,"Xiaomi3"))
    config.print()
    
    print('test config.read')
    print(config.read("macgate"))
    print(config.read("uuid"))
    print(config.read("brokerip"))
    print(config.read("brokerport"))
    print(config.read("brokertopic"))
        