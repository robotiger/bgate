import shelve
import uuid
config=shelve.open("/home/bfg/bgate/config")
print("Print configuration")
#for c in config:
#    print(c,config[c])
#if not config.get("macgate",None):
config["macgate"]     ="%012x"%uuid.getnode()
config["uuid"]        = uuid.uuid1()
config["brokerip"]    ="10.18.2.20"
config["brokerport"]  ="1883"
config["brokertopic"] ="BFG5"
config["factory"]     ="0012"
config["eap"]         ="peap"
config["identity"]    ="bfg"
config["wifissid"]    ="spring"
config["wifipassword"]="M46jiI5d"
config["hostzmqip"]   ="10.18.2.20"
config["hostzmqport"] ="5566"
config["idcon"]       ="spring"

    
for i,j in enumerate(config):
    print(i,j,config[j])
print('можно откорректировать конфигурацию')
while(True):
    t=input('key value for change')
    if t=='':
        break
    key,val=t.split()
    config[key]=val
    config.sync()
    
config.close()
    
"""
27+ 
29+
31+
32+
33
38+
40
41
42
43
"""
