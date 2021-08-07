import serial
# import numpy as np
import math
import os
import sys
import threading
import time
import queue
import collections
import enum
import datetime
import logging
import zlib


class DebugLevel():
    none = 5
    error = 4
    warning = 3
    info = 2
    debug = 1
    all = 0


dlevel = DebugLevel.info


ble_ad_type_desc_dict =\
{
    0x01: "Flags for discoverability",
    0x02: "Partial list of 16 bit service UUIDs",
    0x03: "Complete list of 16 bit service UUIDs",
    0x04: "Partial list of 32 bit service UUIDs",
    0x05: "Complete list of 32 bit service UUIDs",
    0x06: "Partial list of 128 bit service UUIDs",
    0x07: "Complete list of 128 bit service UUIDs",
    0x08: "Short local device name",
    0x09: "Complete local device name",
    0x0A: "Transmit power level",
    0x0D: "Class of device",
    0x0E: "Simple Pairing Hash C",
    0x0F: "Simple Pairing Randomizer R",
    0x10: "Security Manager TK Value",
    0x11: "Security Manager Out Of Band Flags",
    0x12: "Slave Connection Interval Range",
    0x14: "List of 16-bit Service Solicitation UUIDs",
    0x15: "List of 128-bit Service Solicitation UUIDs",
    0x16: "Service Data - 16-bit UUID",
    0x17: "Public Target Address",
    0x18: "Random Target Address",
    0x19: "Appearance",
    0x1A: "Advertising Interval",
    0x1B: "LE Bluetooth Device Address",
    0x1C: "LE Role",
    0x1D: "Simple Pairing Hash C-256",
    0x1E: "Simple Pairing Randomizer R-256",
    0x20: "Service Data - 32-bit UUID",
    0x21: "Service Data - 128-bit UUID",
    0x22: "LE Secure Connections Confirmation Value",
    0x23: "LE Secure Connections Random Value",
    0x24: "URI",
    0x3D: "3D Information Data",
    0xFF: "Manufacturer Specific Data"
}
def splitBleAdvertisingIntoFields(rawdata):
    fields = []
    cnt = 0
    try:
        while(cnt < len(rawdata)):
            field_len = rawdata[cnt]
            cnt += 1
            field_type = rawdata[cnt]
            cnt += 1
            field_data = rawdata[cnt:cnt + field_len - 1]
            cnt += field_len - 1
            fields.append([field_len, field_type, field_data])
    except Exception:
        if dlevel <= DebugLevel.warning:
            print("[WARN] Can't parse advertising data")
    return fields


def decodeBleAdvertisingFields(fields):
    decode_fields = []
    try:
        for field in fields:
            desc = ble_ad_type_desc_dict.get(field[1])
            if desc != None:
                decode_fields.append([desc, field[2]])
            else:
                decode_fields.append(["unknown", field[2]])
    except Exception:
        if dlevel <= DebugLevel.warning:
            print("[WARN] Can't decode advertising fields")
    return decode_fields


def getBleAdvertisingManufacturer(rawdata):
    cnt = 0
    manufacturer = None
    try:
        while (cnt < len(rawdata)):
            field_len = rawdata[cnt]
            cnt += 1
            field_type = rawdata[cnt]
            cnt += 1
            field_data = rawdata[cnt:cnt + field_len - 1]
            cnt += field_len - 1
            if (field_type == 0xFF):
                manufacturer = field_data[0:2]
        return manufacturer
    except Exception:
        if dlevel <= DebugLevel.warning:
            print("[WARN] Can't parse advertising data")


# command class
class Command:
    def __init__(self, cid, data):
        self.id = cid
        self.dlc = len(data)
        self.data = data

    def encode(self):
        enc_data = bytearray.fromhex('ABBA')
        enc_data.append(self.dlc)
        enc_data.extend(bytearray.fromhex(format(self.id, '04X')))
        for d in self.data:
            enc_data.append((d + 256) % 256)
        crc32 = zlib.crc32(enc_data)
        enc_data.extend(bytearray.fromhex(format((crc32 & 0x0000FFFF), '04X')))
        if dlevel <= DebugLevel.debug:
            print('[DEBUG] Cmd encoded: ', ''.join('{:02x}'.format(x) for x in enc_data))
        return enc_data


# command extractor class from bytearray
# [START1][START2][DLC][IDH][IDL][D0][D1]...[Dn][CRCH][CRCL]
class CommandExtractor:
    def __init__(self):
        self.cnt = 0
        self.cnt_dmax = 0
        self.data_storage = collections.deque()
        self.cmd_id = 0
        self.cmd_dlc = 0
        self.cmd_data = []
        self.cmd_crc = 0
        self.crc_calc = 0

    def extract(self):
        if (len(self.data_storage) > 0):
            while (len(self.data_storage) > 0):
                rb = self.data_storage.popleft()
                # startbytes
                if self.cnt == 0:
                    if rb == 0xAB:
                        self.cnt = 1
                elif self.cnt == 1:
                    if rb == 0xBA:
                        self.cnt = 2
                    else:
                        self.cnt = 0
                # dlc
                elif self.cnt == 2:
                    self.cmd_dlc = rb
                    self.cnt_dmax = 5 + rb
                    self.cnt = 3
                # id
                elif self.cnt == 3:
                    self.cmd_id = rb * 256
                    self.cnt = 4
                elif self.cnt == 4:
                    self.cmd_id += rb
                    self.cmd_data.clear()
                    self.cnt = 5
                # data and crc
                else:
                    # crc
                    if self.cnt == self.cnt_dmax:
                        self.cmd_crc = rb * 256
                        self.cnt += 1
                    elif self.cnt == self.cnt_dmax + 1:
                        self.cmd_crc += rb
                        # compose temp buffer for crc calculation
                        temp_crc_buf = bytearray.fromhex('ABBA')
                        temp_crc_buf.append(self.cmd_dlc)
                        temp_crc_buf.extend(bytearray.fromhex(format(self.cmd_id, '04X')))
                        temp_crc_buf.extend(self.cmd_data)
                        self.crc_calc = zlib.crc32(temp_crc_buf) & 0x0000FFFF
                        # check crc
                        if self.cmd_crc == self.crc_calc:
                            self.cnt = 0
                            if dlevel <= DebugLevel.debug:
                                print('[DEBUG] Extract succeded, cmd id: ', format(self.cmd_id, '02x'), ', dlc: ', format(self.cmd_dlc, '02x'),
                                      ', data: ', ''.join('{:02x}'.format(x) for x in self.cmd_data), ', crc: ', format(self.cmd_crc, '04x'),
                                      ', calc crc: ', format(self.crc_calc, '04x'))
                            return Command(self.cmd_id, self.cmd_data)
                        else:
                            self.cnt = 0
                            if dlevel <= DebugLevel.debug:
                                print('[DEBUG] Extract failed, cmd id: ', format(self.cmd_id, '02x'), ', dlc: ', format(self.cmd_dlc, '02x'),
                                      ', data: ', ''.join('{:02x}'.format(x) for x in self.cmd_data), ', crc: ', format(self.cmd_crc, '04x'),
                                      ', calc crc: ', format(self.crc_calc, '04x'))
                            return None
                    # data
                    else:
                        self.cmd_data.append(rb)
                        self.cnt += 1


    def addAndExtract(self, data):
        if data != None:
            self.data_storage.extend(data)
            return self.extract()


class ASerial():

    def __init__(self, port, baudrate):
        if dlevel <= DebugLevel.info:
            print("[INFO] Init aserial")
        self.running = False
        self.ser = serial.Serial(port, baudrate, timeout=0, bytesize=8, stopbits=serial.STOPBITS_ONE)
        self.cmdex = CommandExtractor()
        self.input_str = ""
        # keyboard input queue
        self.input_queue = queue.Queue()
        # serial read queue
        self.s_read_queue = queue.Queue()
        # threads
        self.input_thread = threading.Thread(target=self.handleInput)#, daemon=True)
        self.s_read_thread = threading.Thread(target=self.handleSRead)#, daemon=True)
        self.work_thread = threading.Thread(target=self.handleWork)#, daemon=True)
        # cmd vars
        self.seeadv_filters = []
        self.seeadv_timestop = datetime.datetime.now()
        self.seemac = []
        self.seemac_timestop = datetime.datetime.now()


    def start(self):
        if dlevel <= DebugLevel.info:
            print("[INFO] Start aserial")
        self.running = True
        self.input_thread.start()
        self.s_read_thread.start()
        self.work_thread.start()

    def stop(self):
        if dlevel <= DebugLevel.info:
            print("[INFO] Aserial stopped, tap enter to stop input thread")
        self.running = False

    def handleInput(self):
        if dlevel <= DebugLevel.info:
            print("[INFO] Start input thread")
        while (self.running):
            input_msg = input()
            self.input_queue.put(input_msg)
        if dlevel <= DebugLevel.info:
            print("[INFO] Stop input thread")

    def handleSRead(self):
        if dlevel <= DebugLevel.info:
            print("[INFO] Start serial read thread")
        while (self.running):
            sib = self.ser.read(1024)
            if len(sib) > 0:
                self.s_read_queue.put(sib)
        if dlevel <= DebugLevel.info:
            print("[INFO] Stop serial read thread")

    def handleWork(self):
        if dlevel <= DebugLevel.info:
            print("[INFO] Start work thread")
        while (self.running):
            # work with input data
            while (self.input_queue.qsize() > 0):
                self.input_str = self.input_queue.get()
                print(">> ", self.input_str)
                # stop aserial
                if (self.input_str == "stop"):
                    self.stop()
                    break
                # input commands
                else:
                    self.analyseInputCommand(self.input_str)
            # work with serial data
            rbytes = []
            # convert queue data to list for command extractor
            while (self.s_read_queue.qsize() > 0):
                rbytes.extend(list(self.s_read_queue.get()))
            # get response from extractor by sended read bytes
            resp = self.cmdex.addAndExtract(rbytes)
            if resp != None:
                self.analyseSerialCommand(resp)
        if dlevel <= DebugLevel.info:
            print("[INFO] Stop work thread")

    # change this function to add input commandS handlers
    def analyseInputCommand(self, input_str):
        input_parts = []
        main_part = ""
        if(input_str == ""):
            self.seeadv_timestop = datetime.datetime.now()
            self.seemac_timestop = datetime.datetime.now()
            return
        else:
            try:
                input_parts = input_str.split()
                main_part = input_parts[0]
            except Exception:
                print("Неправильная команда")
                return
        # --------------------------------------------------------------------------------------------------------------
        if (main_part == "help"):
            print("Доступные команды:")
            print("\t\t\tпустая команда (нажатие enter) останавливает вывод")
            print("help\t\tвывод доступных команд")
            print("stop\t\tзавершение работы")
            print("seeadv _\tвывод advertising-пакетов по введенным фильтрам за определенное кол-во секунд")
            print("\t\t\tАргументы: секунды (без аргумента - до остановки) код_фильтра (-m (mac-адреса) -c (каналы) -mf (коды производителя)) фильтр")
            print("seemac _\tвывод уникальных mac-адресов биконов за определенное кол-во секунд. Аргумент: секунды (без аргумента - до остановки)")
            print("ping\t\tпроверка доступности хост-устройства, ответ должен быть \"pong\"")
            print("info\t\tвывод информации о хост-устройстве")
            print("dtrsping _\tпроверка доступности бикона, ответ \"drts ok\" или \"drts fail\". Аргумент: mac-адрес")
            print("dtrsled _\tизменение настроек светодиода бикона")
            print("\t\t\tАргументы: mac-адрес R G B (0-255) общее_время (в сек., 0-65535) период (в мс. 0-65535) продолжительность (в мс. 0-65535)")
            print("dtrsledrgb _\tвключение светодиода бикона. Аргументы: mac-адрес R G B (0-255)")
            print("dtrsledoff _\tвыключение светодиода бикона")
            print("dtrsset _\tизменение настроек бикона. Аргументы: mac-адрес маска_настроек мощность (-40, -16...4) маска_каналов интервал (в мс.)")
            print("\t\t\tв маске настроек биты со значением 0 игнорируют настройку, со значением 1 используют передаваемые значения в настройке")
            print("\t\t\t0 бит - мощность, 1 бит - маска каналов, 2 бит - интервал. Маска 6 настроит каналы и интервал, маска 2 настроит только каналы")
            print("\t\t\tмаски каналов: 0 - 39+38+37, 32 - 39+38, 64 - 38+37, 128 - 39, 160 - 38, 192 - 37")
        # --------------------------------------------------------------------------------------------------------------
        elif (main_part == "seeadv"):
            try:
                tdelta = 0
                try:
                    tdelta = int(input_parts[1])
                except Exception:
                    tdelta = 8640000000
                self.seeadv_timestop = datetime.datetime.now() + datetime.timedelta(0, tdelta)
                self.seeadv_filters.clear()
                seedvfs_fcodes = {"-m", "-c", "-mf"}
                seedvfs_current_fcode = ""
                # parsing input
                for in_part in input_parts[1:]:
                    if in_part in seedvfs_fcodes:
                        seedvfs_current_fcode = in_part
                        self.seeadv_filters.append([in_part, []])
                    else:
                        if seedvfs_current_fcode == "-m":
                            self.seeadv_filters[len(self.seeadv_filters) - 1][1].append(list(bytearray.fromhex(in_part)))
                        elif seedvfs_current_fcode == "-c":
                            self.seeadv_filters[len(self.seeadv_filters) - 1][1].append(int(in_part))
                        elif seedvfs_current_fcode == "-mf":
                            mf = list(bytearray.fromhex(in_part))
                            mf.reverse()
                            self.seeadv_filters[len(self.seeadv_filters) - 1][1].append(mf)

                print("Вывод advertising-пакетов на ", tdelta, " сек.")
                if(len(self.seeadv_filters) > 0):
                    print("Следующие фильтры будут применены: ", self.seeadv_filters)
            except Exception:
                print("Неправильная команда")
        # --------------------------------------------------------------------------------------------------------------
        elif (main_part == "seemac"):
            try:
                tdelta = 0
                try:
                    tdelta = int(input_parts[1])
                except Exception:
                    tdelta = 8640000000
                self.seemac_timestop = datetime.datetime.now() + datetime.timedelta(0, tdelta)
                self.seemac.clear()
                print("Вывод уникальных mac-адресов на ", tdelta, " сек.")
            except Exception:
                print("Неправильная команда")
        # --------------------------------------------------------------------------------------------------------------
        elif (main_part == "ping"):
            try:
                cmd = Command(1, [])
                self.ser.write(cmd.encode())
            except Exception:
                print("Неправильная команда")
        # --------------------------------------------------------------------------------------------------------------
        elif (main_part == "info"):
            try:
                cmd = Command(2, [])
                self.ser.write(cmd.encode())
            except Exception:
                print("Неправильная команда")
        # --------------------------------------------------------------------------------------------------------------
        elif (main_part == "dtrsping"):
            try:
                cmdargs = list(bytearray.fromhex(input_parts[1]))
                if len(cmdargs) != 6:
                    print("Неправильная длина команды, проверьте аргументы")
                else:
                    cmd = Command(3, cmdargs)
                    self.ser.write(cmd.encode())
            except Exception:
                print("Неправильная команда")
        # --------------------------------------------------------------------------------------------------------------
        elif (main_part == "dtrsled"):
            try:
                # mac
                cmdargs = list(bytearray.fromhex(input_parts[1]))
                # all other args
                for in_part in input_parts[2:5]:
                    arg = int(in_part)
                    if(arg < 0 or arg > 0xFF):
                        print("Неправильные аргументы 2-4")
                        return
                    else:
                        cmdargs.append(arg)
                for in_part in input_parts[5:8]:
                    arg = int(in_part)
                    if (arg < 0 or arg > 0xFFFF):
                        print("Неправильные аргументы 5-7")
                        return
                    else:
                        cmdargs.append((arg & 0xFF00) >> 8)
                        cmdargs.append(arg & 0x00FF)
                if(len(cmdargs) != 15):
                    print("Неправильная длина команды, проверьте аргументы")
                else:
                    cmd = Command(4, cmdargs)
                    self.ser.write(cmd.encode())
            except Exception:
                print("Неправильная команда")
        # --------------------------------------------------------------------------------------------------------------
        elif (main_part == "dtrsledrgb"):
            try:
                # mac
                cmdargs = list(bytearray.fromhex(input_parts[1]))
                # all other args
                for in_part in input_parts[2:5]:
                    arg = int(in_part)
                    if(arg < 0 or arg > 0xFF):
                        print("Неправильные аргументы 2-4")
                        return
                    else:
                        cmdargs.append(arg)
                cmdargs.extend([0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])
                if (len(cmdargs) != 15):
                    print("Неправильная длина команды, проверьте аргументы")
                else:
                    cmd = Command(4, cmdargs)
                    self.ser.write(cmd.encode())
            except Exception:
                print("Неправильная команда")
        # --------------------------------------------------------------------------------------------------------------
        elif (main_part == "dtrsledoff"):
            try:
                # mac
                cmdargs = list(bytearray.fromhex(input_parts[1]))
                cmdargs.extend([0, 0, 0, 0, 0, 0, 0, 0, 0])
                if (len(cmdargs) != 15):
                    print("Неправильная длина команды, проверьте аргументы")
                else:
                    cmd = Command(4, cmdargs)
                    self.ser.write(cmd.encode())
            except Exception:
                print("Неправильная команда")
        # --------------------------------------------------------------------------------------------------------------
        elif (main_part == "dtrsset"):
            try:
                # mac
                cmdargs = list(bytearray.fromhex(input_parts[1]))
                # settings bitmask
                arg = int(input_parts[2])
                if(arg <= 0):
                    print("Неправильная маска настроек")
                    return
                else:
                    cmdargs.append(arg)
                # power
                arg = int(input_parts[3])
                if (arg < -40 or arg > 4):
                    print("Неправильная мощность")
                    return
                else:
                    cmdargs.append(arg)
                # channel mask. 0 - 39+38+37, 32 - 39+38, 64 - 38+37, 128 - 39, 160 - 38, 192 - 37
                available_channel_mask = [0, 32, 64, 128, 96, 160, 192]
                arg = int(input_parts[4])
                if(arg not in available_channel_mask):
                    print("Неправильная маска каналов")
                    return
                else:
                    cmdargs.append(arg)
                # interval
                arg = int(input_parts[5])
                if (arg < 0 or arg > 0xFFFF):
                    print("Неправильный интервал")
                    return
                else:
                    cmdargs.append((arg & 0xFF00) >> 8)
                    cmdargs.append(arg & 0x00FF)
                if(len(cmdargs) != 11):
                    print("Неправильная длина команды, проверьте аргументы")
                else:
                    cmd = Command(5, cmdargs)
                    self.ser.write(cmd.encode())
            except Exception:
                print("Неправильная команда")
        # all other commands from dictionary
        # --------------------------------------------------------------------------------------------------------------
        else:
            print("Неизвестная команда")

    # change this function to add serial command handlers
    def analyseSerialCommand(self, cmd):
        # response
        # --------------------------------------------------------------------------------------------------------------
        if cmd.id == 0:
            print("<< ", bytearray(cmd.data).decode('ascii'))
        # info
        # --------------------------------------------------------------------------------------------------------------
        elif cmd.id == 1:
            mac = cmd.data[0:6]
            print('host device info')
            print('mac: ', ''.join('{:02x}'.format(x) for x in mac))
        # ble packet
        # --------------------------------------------------------------------------------------------------------------
        elif cmd.id == 2:
            if (datetime.datetime.now() < self.seeadv_timestop):
                rep_type = cmd.data[0:2]
                mac = cmd.data[2:8]
                pri_phy = cmd.data[8]
                sec_phy = cmd.data[9]
                tx_pwr = cmd.data[10]
                rssi = cmd.data[11]
                channel = cmd.data[12]
                rawdata = cmd.data[13:len(cmd.data)]
                manufacturer = getBleAdvertisingManufacturer(rawdata)
                # empty filter
                if(len(self.seeadv_filters) == 0):
                    fields = splitBleAdvertisingIntoFields(rawdata)
                    print('rep_type: ', ''.join('{:02x}'.format(x) for x in rep_type),
                          ', mac: ', ''.join('{:02x}'.format(x) for x in mac),
                          ', pri_phy: ', format(pri_phy, '02x'), ', sec_phy: ', format(sec_phy, '02x'),
                          ', tx_pwr: ', tx_pwr - 256, ', rssi: ', rssi - 256, ', channel: ', channel,
                          #', raw data: ', ''.join('{:02x}'.format(x) for x in rawdata),
                          ', fields: ', fields)
                # non-empty filter
                else:
                    show_adv = True
                    for filter in self.seeadv_filters:
                        if filter[0] == "-m":
                            if mac not in filter[1]:
                                show_adv = False
                                break
                        elif filter[0] == "-c":
                            if channel not in filter[1]:
                                show_adv = False
                        elif filter[0] == "-mf":
                            if manufacturer not in filter[1]:
                                show_adv = False
                    if show_adv:
                        fields = splitBleAdvertisingIntoFields(rawdata)
                        print('rep_type: ', ''.join('{:02x}'.format(x) for x in rep_type),
                              ', mac: ', ''.join('{:02x}'.format(x) for x in mac),
                              ', pri_phy: ', format(pri_phy, '02x'), ', sec_phy: ', format(sec_phy, '02x'),
                              ', tx_pwr: ', tx_pwr - 256, ', rssi: ', rssi - 256, ', channel: ', channel,
                              # ', raw data: ', ''.join('{:02x}'.format(x) for x in rawdata),
                              ', fields: ', fields)

            if (datetime.datetime.now() < self.seemac_timestop):
                mac = cmd.data[2:8]
                if mac not in self.seemac:
                    self.seemac.append(mac)
                    print(len(self.seemac), '. mac: ', ''.join('{:02x}'.format(x) for x in mac))



# main
if (__name__ == '__main__'):
    try:
        dlevel = DebugLevel.info
        aser = ASerial(port="/dev/ttyS1", baudrate=115200)
        aser.start()
    except Exception:
        if dlevel <= DebugLevel.warning:
            print("[WARN] Can't connect to device")

