import shelve
config=shelve.open("/home/bfg/bgate/config")
print("Print configuration")
for c in config:
    print(c,config[c])

