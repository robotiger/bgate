import shelve
config=shelve.open("/home/bfg/bgate/config")
print("Print configuration")
#for c in config:
#    print(c,config[c])
for i,j in enumerate(config):
    print(i,j,config[j])
