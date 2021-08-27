import shelve
config=shelve.open("/home/bfg/bgate/config.db")
print("Print configuration")
#for c in config:
#    print(c,config[c])
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
    

