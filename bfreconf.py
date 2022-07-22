import uuid
import shelve

config=shelve.open("/home/bfg/bgate/config")
#if not "macgate" in config:
config["macgate"]="%012x"%uuid.getnode()
config["uuid"]=uuid.uuid1()
config["broker"]="192.168.31.206"
config["brokerport"]=1883
config["topic"]="BFG5"
config.sync() 

