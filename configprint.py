import shelve
config=shelve.open("/home/bfg/bgate/config")
print("Print configuration")
#for c in config:
#    print(c,config[c])
if not config.get("macgate",None):
    config["macgate"]     ="%012x"%uuid.getnode()
    config["uuid"]        = uuid.uuid1()
    config["brokerip"]    ="192.168.31.20"
    config["brokerport"]  ="1883"
    config["brokertopic"] ="BFG5"
    config["factory"]     ="0012"
    
    
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
    

