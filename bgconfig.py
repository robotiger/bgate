import os
import shutil
import shelve
import uuid

class Configuration():
    def __init__(self):
        
        configfilename ="/home/bfg/bgate/config"
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
        
        # коды параметров конфигурации. в интерфейсе числа. в программе и файле названия.
        self.mapto={
            1:'macgate',
            2:'uuidgate',
            3:'wifissid',
            4:'wifipassword',
            5:'hotspotssid',
            6:'hotspotpassword',
            7:'brokerip',
            8:'brokerport',
            9:'brokertopic',
           10:'tokenapi'
            }
#        self.tomap={}
#        for name in self.mapto:
#            self.tomap[self.mapto[name]]=name
            
        if  self.read("macgate") is None:
            self.write("macgate","%012x"%uuid.getnode())
            self.write("uuid",uuid.uuid1())
            self.write("brokerip","192.168.31.20")
            self.write("brokerport",1883)
            self.write("brokertopic","BFGS5")
            
          
            
    def read(self, parameter):
        try:
            idx=int(parameter)
            parameter=self.mapto[idx]
        except:
            pass
        return self.config.get(parameter,None)

    def write(self, parameter, value):
        try:
            idx=int(parameter)
            parameter=self.mapto[idx]
        except:
            pass
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
    
    
if __name__=='__main__':
    config=Configuration()
    config.print()