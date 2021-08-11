import zlib
import struct
import hashlib
from Crypto.Cipher import AES



class BlAdvCoder:
    
    @staticmethod
    def commandledencoder(mac,r,g,b,t,p,o):
        ## используется для управления светодиодом бикона
        ## формирует строку для отправки в блютус модуль.
        ## входные параметры мак адрес '010203040506', яркость цветов r,g,b, длительность в секундах, период в милисекундах, время включения в милисекундах
        try:
            enc_data= struct.pack('>5s6s3B3h',b'\xab\xba\x0f\00\04',bytes.fromhex(mac),r,g,b,t,p,o)
        except:
            return None
        crc32=zlib.crc32(enc_data)
        #print(crc32.to_bytes().hex(' '))
        return struct.pack('>20sH',enc_data,crc32&0xffff)
    
          
    @staticmethod
    def decode2(dpin):
        #dpo={'macgate':config['macgate']}
        
        dp1=dict(zip(['mac','rssi','band'],struct.unpack('2x6s3x2b',dpin[:13])))
        if len(dpin)==43: # from beacons
            dp2=dict(zip(['mfg','uuid','cnt','ext','exd','txpower'],       struct.unpack('6s16sHBBb', dpin[16:])))
            dp3=dict(zip(['mfg','cnt','type','uuid','ext','exd','txpower'],struct.unpack('5sH2s8sBib',dpin[16:41])))
            if dp2['mfg'].hex()=='1aff4c000215': #apple beacon
                dpo={**dp1,**dp2}
            if dp3['mfg'].hex()=='16ffb1bf00': #hitech beacon
                dpo={**dp1,**dp3}
            for c in dpo:
                if c in ['mac','mfg','uuid']:
                    dpo[c]=dpo[c].hex()
            dpo['gate']=config['macgate']
            dpo['raw']=dpin.hex()
            return dpo
        
    @staticmethod   
    def aesdecode(mes):
        key= b'fkytbwpt69xsbna3'
        salt=b'lrjk;rdfkdldkhcngfle45'
        dlina=mes[0]
        ffmfg=mes[1:4]
        once=mes[4:8]
        coded=mes[8:dlina+1]
        #print(dlina,ffmfg.hex(),once.hex(),coded.hex())
        if ffmfg.hex()=='ffb1bf':
            nonce=hashlib.sha1(once+salt)
            rcv =AES.new(key,AES.MODE_EAX,nonce=nonce.digest()).decrypt(coded)
            ronce,cfg,data=struct.unpack('2sh%ds'%(dlina-11),rcv)
            return (ronce==once[:2],cfg,data)        


"""
HB ble5 
   00 03 95 39 6e 74 da 05 01 ff 7f c0 27 02 01 06 16 ff b1 bf 00 1c 5f 01 00 95 39 6e 74 da 05 00 00 00 00 00 f8 72 d3 03 08 48 42 
43 00 03 af bf cf df ef ff 01 ff 7f f2 26 02 01 06 16 ff bf b1 00 00 7d 01 00 ff ff ff ff ff ff 00 00 00 00 00 f8 42 c4 03 08 48 42
   00 03 41 92 11 c2 a3 4c 01 ff 7f c1 26 02 01 06 16 ff b1 bf 00 00 0b 01 00 41 92 11 c2 a3 4c 00 00 00 00 00 f8 41 ab 03 08 48 42 
   00 03 a4 59 b0 20 45 81 01 ff 7f ca 26 02 01 06 16 ff b1 bf 00 00 0d 01 00 a4 59 b0 20 45 81 00 00 00 00 00 f8 4d b4 03 08 48 42   
-1 0  1  2  3   4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 
   type | mac             |bits |tx|rs|pr|flags   |le|us|idmfg|pid|cnt |dev  + id              |ty|exdata     |tp|crc  |ln|st|name
   const| id              |const   |var  |const   | const         |var | id                    |var              |crc  |const
                                                               cccccccccccccccccrrrrrrrrrrrrccccccccccccccccccccc                                                                   
 len 44  change to 43
0:type:00 03
2:mac: af bf cf df ef ff
8: 01 ff 
10:txpower:7f 
11:rssi: f2
12:port: 26
13-15: 02 01 06 длина тип флаги
16: 17 длина
17: ff пользовательский тип
18-19: fe c0 ид производителя
#! 11 длина exclude
20! 00 ид пакета широковещательный
21-22! 00 84 счетчик пакета
23:! 01 тип устройства
24:! 00 подтип
25-30! ff ff ff ff ff ff ид
31! 00 тип данных
33-35! 00 00 00 00 данные    
36! f8 мощность передачи  
37! 57 контрольная сумма  
38! 2b контрольная сумма 
39 03 длина

40 08 тип короткое имя
41-42 48 42  HB


"""


if __name__=='__main__':
    
    
    config={'macgate':'0123456987654'}
    
    p=[
     bytes.fromhex('00 03 00 01 95 3f c8 c4 01 ff 7f d3 25 1e ff b1 bf f3 72 d7 07 3d a5 7b 77 0a 1e ae 3f f3 ae f2 b2 cc f2 ff 63 6b 80 93 a4 ae f1 5a'),
     bytes.fromhex('00 03 be df b2 cf 7c a5 01 ff 7f be 25 02 01 06 1a ff 4c 00 02 15 00 00 00 01 bf b0 2e 70 dd b9 46 a0 cb 90 81 df 05 01 27 82 ec'),
     bytes.fromhex('00 03 c6 5a 9c f5 d4 74 01 ff 7f d5 25 02 01 06 16 ff b1 bf 00 82 5a 01 00 4c 33 88 55 76 3f 02 00 00 0a ce f8 bd 5d 03 08 48 42'),
     bytes.fromhex('00 00 fe 0e 9b 4b fa c1 01 ff 7f cc 25 02 01 04 1a ff 4c 00 02 15 b9 40 7f 30 f5 f8 46 6e af f9 25 55 6b 57 fe 6d 04 d7 18 61 c3')
     ]
    
    for i in p:
        #print(BlAdvDecoder.decode(i))
        if len(i)==43:
            d=BlAdvCoder.decode2(i)
            #publish
        if len(i)==44:
            d=BlAdvCoder.aesdecode(i[13:])
            #config
        print(d)
    #print(BlAdvDecoder.decode(bytes.fromhex('')))
    
    
    mac='c65a9cf5d474'
    mac='00'*6
    cmd=BlAdvCoder.commandledencoder(mac,4,5,6,259,259,259)
    print('cmd',cmd.hex(' '))
    
    