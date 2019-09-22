import time
import os
import sys
import struct
import operator
import queue
import threading
import traceback
import numpy as np

import cyPyUSB
import cyPyUSB.core
import cyPyUSB.util
import cyPyUSB.backend.libusb1

#  Import modified pycryptodomex AES ciphers.
# ¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯
from cyCrypto.Cipher import AES

from modify import modify

from modify2 import modify2

#  Detect 32 / 64 Bit Architecture.
# ¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯
arch = struct.calcsize("P") * 8

eeg_process = 1


#  Add a relative local path to CyKIT.
# ¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯
localPath = ((sys.argv[0]).replace('/','\\')).split('\\')
localPath = localPath[0:(len(localPath) -1)]
localPath = str('\\'.join(localPath ))
if localPath == None:
    localPath = ".\\"

sys.path.insert(0, localPath)

#  Custom print class. Workaround for OSError: raw write().
# ¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯
class mirror():
    def text(custom_string):
        try:
            print(str(custom_string))
            return
        except OSError as exp:
            return
     
parameters = len(sys.argv)
if parameters > 4:
    eeg_config = sys.argv[4]
else:
    eeg_config = ""
     

if parameters > 4 and "verbose" in eeg_config:
    verbose = True
else:
    verbose = False

if parameters > 4 and "path" in eeg_config:
    mirror.text("[Python Search Path] " + str(sys.path))


#  Setup [ pyUSB (Default) / pywinusb ]
# ¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯


if verbose == True:
    mirror.text("> Importing (pyusb) \\cyPyUSB")
eeg_driver = "pyusb"
sys.path.insert(0, localPath + '\\cyUSB')
sys.path.insert(0, localPath + '\\cyUSB\\libusb')

tasks = queue.Queue()
encrypted_data = bytearray()

class ControllerIO():
    
    #  Initialize at thread creation.
    # ¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯
    def __init__(self):
        global BTLE_device_name
        BTLE_device_name = ""
        self.infoData = {}

    #  Set Information. (Name, Info)
    # ¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯
    def setInfo(self, name, info):
        if "str" in str(type(info)):
            self.infoData[str(name)] = str(info)
        else:
            self.infoData[name] = info # Preserve Object
        return
        
    #  Retrieve Information by Name. 
    # ¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯
    def getInfo(self, name):
        if str(name) not in self.infoData:
            return "0"
        else:
            return self.infoData[str(name)]

def resolve_mode(dataSTR):
    changed_mode = -1
    if dataSTR == str([0, 0, 128, 14, 128, 12, 0 ,0]):
        changed_mode = 0
        
    if dataSTR == str([1, 0, 128, 16, 0, 16, 0, 0]):
        changed_mode = 1
        
    if dataSTR == str([1, 0, 128, 16, 32, 16, 0, 0]):
        changed_mode = 2
        
    if dataSTR == str([1, 0, 128, 16, 64, 16, 0, 0]):
        changed_mode = 3
        
    if dataSTR == str([1, 0, 128, 16, 128, 16, 0, 0]):
        changed_mode = 4
    
    if dataSTR == str([1, 1, 0, 16, 0, 16, 0, 0]):
        changed_mode = 5
    
    if dataSTR == str([1, 1, 0, 16, 32, 16, 0, 0]):
        changed_mode = 6
    
    if dataSTR == str([1, 1, 0, 16, 64, 16, 0, 0]):
        changed_mode = 7
    
    if dataSTR == str([1, 1, 0, 16, 128, 16, 0, 0]):
        changed_mode = 8
    
    return changed_mode
    
def settings_menu(device, sIO, intf):
    
    data = None
    current_txt = "unknown"
    current_mode = -1
    current = ["","","","","","","","",""]
    
    if eeg_driver == "pyusb":
        device_firmware   = sIO.getInfo("deviceFirmware")
        software_firmware = sIO.getInfo("softFirmware")
        
        if device_firmware != "0x565" or software_firmware != "0x625":
            mirror.text("Hardware Information indicates your firmware might not be supported for mode changes via CyKIT")
            mirror.text("   Please Report your firmware and software to the software developer:")
            mirror.text("   Device   Firmware: " + device_firmware)
            mirror.text("   Software Firmware: " + software_firmware)
            mirror.text("\r\n Until it is concluded to be safe to update via CyKIT, ")
            mirror.text("  it is recommended you use an Emotiv program to make mode changes.")

        
    if data != None:
        current_mode = resolve_mode(str(data[12:20]))
        
        if current_mode != -1:
            current_txt = str(current_mode)
            current[current_mode] = "* (Active)"
        
        current[current_mode] 
                
    if sIO.getInfo("updateEPOC") != "None":
        mode_select = sIO.getInfo("updateEPOC")
        sIO.setInfo("updateEPOC", "None")
    else:
        mirror.text("\r\n")
        mirror.text("═" *100)
        mirror.text("  *** Important Advisories *** (Please Read)              ")
        mirror.text("═" *100)
        mirror.text("      The EPOC+ is connected directly to your computer via USB.                                                     ")
        mirror.text("      During this time, the device can not send data via Bluetooth or USB. \r\n\r\n                                 ")
        mirror.text("      To Change the EPOC+ mode, the device must be [Powered On] (ie. White light on)  while connected to USB.       ")
        mirror.text("      If the device is not turned on when a selection is made, no settings will be changed.\r\n\r\n                 ")
        mirror.text("      Changing to 256hz and or enabling MEMS (ie. gyro) data, will reduce the battery life.                         ")
        mirror.text("      EPOC+ (Typical) Battery Life = 12 Hours. \r\n\r\n                                                             ")
        mirror.text("      EPOC+ (14-bit mode) - key model# = 4                                                                               ")
        mirror.text("      EPOC+ (16-bit mode) - key model# = 6 \r\n                                                                      \r\n")
        mirror.text("═" *100)
        
        mirror.text("  EPOC+ Mode Selection Menu. [Current Mode: " + current_txt + "]")
        mirror.text("═" *100)
        mirror.text(" 0) EPOC (14-bit mode)                       " + str(current[0]))
        mirror.text(" 1) EPOC+ 128hz 16bit - MEMS off             " + str(current[1]))
        mirror.text(" 2) EPOC+ 128hz 16bit - MEMS 32hz  16bit     " + str(current[2]))
        mirror.text(" 3) EPOC+ 128hz 16bit - MEMS 64hz  16bit     " + str(current[3]))
        mirror.text(" 4) EPOC+ 128hz 16bit - MEMS 128hz 16bit     " + str(current[4]))
        mirror.text(" 5) EPOC+ 256hz 16bit - MEMS off             " + str(current[5]))
        mirror.text(" 6) EPOC+ 256hz 16bit - MEMS 32hz  16bit     " + str(current[6]))
        mirror.text(" 7) EPOC+ 256hz 16bit - MEMS 64hz  16bit     " + str(current[7]))
        mirror.text(" 8) EPOC+ 256hz 16bit - MEMS 128hz 16bit     " + str(current[8]) + "\r\n")
        mode_select = input(" Enter Mode: [0,1,2,3,4,5,6,7,8] or [Q] to Exit \> ")
    
    if mode_select.upper() == "Q":
        os._exit(0)
        
        
    if mode_select.isdigit() == True:
        mode_select = int(mode_select)
        if mode_select > -1 and mode_select < 9:
                
            EPOC_ChangeMode = mode_select
            
            ep_mode = [0x0] * 32

            if eeg_driver == "pyusb":
                ep_mode[0:3] = [0x55,0xAA,0x20,0x12] 
                ep_select = [0x00,0x82,0x86,0x8A,0x8E,0xE2,0xE6,0xEA,0xEE]
                ep_mode[4] = ep_select[EPOC_ChangeMode]

            #0 EPOC                                  0x00 (d.000)  55 AA 20 12 00     IN
            #1 EPOC+ 128hz 16bit - MEMS off          0x82 (d.130)  55 AA 20 12 82 00  IN 
            #2 EPOC+ 128hz 16bit - MEMS 32hz 16bit   0x86 (d.134)  55 AA 20 12 86     IN    55 AA 88 12 00
            #3 EPOC+ 128hz 16bit - MEMS 64hz 16bit   0x8A (d.138) 
            #4 EPOC+ 128hz 16bit - MEMS 128hz 16bit  0x8E (d.142)
            #5 EPOC+ 256hz 16bit - MEMS off          0xE2 (d.226)
            #6 EPOC+ 256hz 16bit - MEMS 32hz 16bit   0xE6 (d.230)
            #7 EPOC+ 256hz 16bit - MEMS 64hz 16bit   0xEA (d.234)
            #8 EPOC+ 256hz 16bit - MEMS 128hz 16bit  0xEE (d.238)
            
            mirror.text("\r\n>>> Sending Mode Update to EPOC+ >>> \r\n\r\n")
            try:
                if eeg_driver == "pywinusb":
                    
                    report = device.find_output_reports()
                    report[0].set_raw_data(ep_mode)
                    report[0].send()
                    mirror.text("*** Updated EPOC+ Settings ***")
                    
                    changed_mode = -1
                    wait_for_mode = 0
                    
                    while changed_mode != EPOC_ChangeMode:
                        wait_for_mode += 1
                        if wait_for_mode > 10000:
                            mirror.text("\r\n\r\n> Mode change incomplete. Please try again. ")
                            mirror.text("\r\n> Confirm the device is turned on during update. *** ")
                            os._exit(0)
                            
                        for inputReport in successReport:
                            data = inputReport.get()
                            dataSTR = str(data[12:20])
                            #using STR comparison instead of built-in SET due to py error.
                            changed_mode = resolve_mode(dataSTR)
                            
                    mirror.text("\r\n>>> (Confirmation) >>> EPOC+ Mode Changed to: " + str(changed_mode) + " \r\n\r\n")
                            
                if eeg_driver == "pyusb":
                    if intf == None:
                        mirror.text("> Invalid Descriptor ")
                        os._exit(0)
                    report = cyPyUSB.util.find_descriptor(intf, custom_match = \
                                                          lambda e: cyPyUSB.util.endpoint_direction(e.bEndpointAddress) == cyPyUSB.util.ENDPOINT_OUT)
                    report.write(ep_mode)
                    
                    
            except Exception as e:
                exc_type, ex, tb = sys.exc_info()
                imported_tb_info = traceback.extract_tb(tb)[-1]
                line_number = imported_tb_info[1]
                print_format = "{}: Exception in line: {}, message: {}"
                mirror.text(" ¯¯¯¯ eegThread.run() Error Communicating With USB.")
                mirror.text(" =E.3: " + print_format.format(exc_type.__name__, line_number, ex))    
                os._exit(0)
        
                



class EEG(object):

    def __init__(self, model, io, config):
        global running
        global cyIO
        
        config = config.lower()
        self.config = config
        self.time_delay = .001
        self.KeyModel = model
        self.running = True
        self.counter = "0"
        self.serial_number = ""
        self.lock = threading.Lock()
        self.cyIO = io
        self.cyIO.setInfo("updateEPOC","None") # Must be set before Setup()
        self.device = None                             # Must be set before Setup()
        self.myKey = self.Setup(model, config)
        self.recordInc = 1
        self.thread_1 = threading.Thread(name='eegThread', target=self.run, kwargs={'key': self.myKey, 'cyIO': self.cyIO}, daemon = False)
        self.stop_thread = False
        self.samplingRate = 128
        self.epoc_plus_usb = False
        self.report = None
        self.channels = 40
        self.blankcsv = False
        self.generic = False
        self.openvibe = False
        self.integer = False
        self.noheader = False
        self.blankdata = False
        self.nocounter = False
        self.nobattery = False
        self.baseline = False
        self.outputdata = False
        self.outputraw = False
        self.verbose = False
        self.noweb = False
        self.filter = False
        self.datamode = 1
        self.getSeconds = 0
        self.baseSeconds = 0
        

        self.configFlags = ["blankdata","blankcsv","nocounter","nobattery","baseline","noheader",
                       "integer","outputdata","generic","openvibe","baseline","outputraw",
                       "filter","allmode","eegmode","gyromode","verbose","noweb"]

        if "allmode" in config:       self.datamode = 0
        if "eegmode" in config:       self.datamode = 1
        if "gyromode" in config:      self.datamode = 2       
        
        if "nocounter" in config:     
            self.nocounter = True
            if self.datamode == 0:
                self.datamode = 1
        else:   self.nocounter = False
        
        if "ovdelay" in config:      
            myDelay = str(config).split("ovdelay:")
            self.ovdelay = myDelay[1][:3]
        else:                        
            self.ovdelay = 100
            
        if "ovsamples" in config:      
            mySamples = str(config).split("ovsamples:")
            self.ovsamples = int(mySamples[1][:3])
            if self.ovsamples > 512:
                self.ovsamples = 512
        else:                        
            self.ovsamples = 4
        
        if "delimiter" in config:     
            nDelimiter = str(config).split("delimiter=")[1]
            if len(nDelimiter) > 0:
                if "+" in nDelimiter:
                    nDelimiter = str(nDelimiter).split("+")[0]
                if nDelimiter.isdigit() and abs(int(nDelimiter)) < 1114112:
                    self.delimiter = chr(abs(int(nDelimiter)))
                else:
                    self.delimiter = ","
        else:
            self.delimiter = ","
        
        if "format" in config:     
            myFormat = str(config).split("format-")
            self.format = int(myFormat[1][:1])
        else:
            self.format = 0
            
        if "channel=" in config:     
            channel_select = str(config).split("channel=")[1]
            
            if "+" in channel_select:
                self.channel = str(channel_select).split("+")[0]
                
            else:
                self.channel = channel_select[0]
            if self.channel == "":
                self.channel == None
        else:
            self.channel = None
        
        
        if eval(self.cyIO.getInfo("verbose")) == True:
            mirror.text("    Format = " + str(self.format))
            try:
                mirror.text(" Delimiter = " + str(self.delimiter))
            except:
                self.delimiter = ","
                mirror.text(" Delimiter = " + str(self.delimiter))
                pass
        
        #  Set Config Flags and Insert Into Dictionary.
        # ¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯
        if eval(self.cyIO.getInfo("verbose")) == True:
            mirror.text("═" *90 + "\r\n")
            mirror.text(" Config Options = { \r\n")
        for index in self.configFlags:
            if str(index) in config:
                if eval(self.cyIO.getInfo("verbose")) == True:
                    mirror.text("   " + index + (chr(9)*2) + " " + str(True) + "  *")
                locals()['self.' + index] = True
            else:
                if eval(self.cyIO.getInfo("verbose")) == True:
                    mirror.text("   " + index + (chr(9)* 2) + str(False))
                locals()['self.' + index] = False
            self.cyIO.setInfo(index,str(locals()['self.' + index]))
        
        self.cyIO.setInfo("ovsamples", self.ovsamples)
        self.cyIO.setInfo("delimiter", self.delimiter)
        self.cyIO.setInfo("datamode", self.datamode)
        self.cyIO.setInfo("format", self.format)
        self.cyIO.setInfo("config", config)
        
        if eval(self.cyIO.getInfo("verbose")) == True:
            mirror.text("\r\n }")
        mirror.text("═" *50 + "\r\n")
        
        
    def start(self):
        
        self.running = True
        self.status = True
        for t in threading.enumerate():
            if 'eegThread' == t.getName():
                return self.cyIO
        self.thread_1.start()
        print('1 started')
        return self.cyIO

    
    def Setup(self, model, config):
        global BTLE_device_name
       
        #  Additional Product Names. (Not used for Data)
        # 'EPOC BCI', 'Brain Waves', 'Brain Computer Interface USB Receiver/Dongle', 'Receiver Dongle L01'
        deviceList  = ['EPOC+','EEG Signals', '00000000000', 'Emotiv RAW DATA',]
        DEVICE_UUID = "{81072f40-9f3d-11e3-a9dc-0002a5d5c51b}"
        DATA_UUID   = "{81072f41-9f3d-11e3-a9dc-0002a5d5c51b}"
        MEMS_UUID   = "{81072f42-9f3d-11e3-a9dc-0002a5d5c51b}"

        devicesUsed = 0        
        threadMax = 0
        detail_info = None
        device_firmware = ""
        software_firmware = ""
        intf = 0
        
        for t in threading.enumerate():
            if t.getName()[:6] == "Thread":
                threadMax += 1
                # Alternative 'backend' devices for pyUSB, could be added here.
        backend = cyPyUSB.backend.libusb1.get_backend(find_library="./libusb-1.0x64.dll")

        if str(backend) == "None":
           mirror.text("> Driver could not be found or unsuccessfully loaded.")
           os._exit(0)
        self.product_name = None
        all_devices = cyPyUSB.core.find(find_all=1, backend=backend)
        for select_device in all_devices:
            if eval(self.cyIO.getInfo("verbose")) == True:
                mirror.text("═" * 50)
            try:
                company = str(cyPyUSB.util.get_string(select_device, select_device.iManufacturer))
                product = str(cyPyUSB.util.get_string(select_device, select_device.iProduct))

                vid     = str(hex(select_device.idVendor))
                pid     = str(hex(select_device.idProduct))
            except:
                mirror.text("> USB Device (No Additional Information)")
                continue
            if eval(self.cyIO.getInfo("verbose")) == True:
                mirror.text(" Company: " + company)
                mirror.text("  Device: " + product)
                mirror.text("  Vendor: " + vid)
                mirror.text(" Product: " + pid)

            useDevice = ""
            for i, findDevice in enumerate(deviceList):

                if product == deviceList[i]:

                    mirror.text("\r\n> Found EEG Device [" +  findDevice + "] \r\n")
                    if "confirm" in config:
                        useDevice = input(" Use this device? [Y]es? ")
                    else:
                        useDevice = "Y"
                    if useDevice.upper() == "Y":
                        devicesUsed += 1
                        self.device = select_device
                        print('selected')

                        if threadMax < 100:


                            self.device.set_configuration()
                            cfg = self.device.get_active_configuration()

                            if product == 'EPOC+':
                                deviceList[1] = 'empty'
                                intf = cfg[(0,0)]
                                self.cyIO.setInfo("intf", intf)

                            else:

                                intf = cfg[(1,0)]
                                self.cyIO.setInfo("intf", intf)
                                print('33')

                            """
                            detail_info = None
                            intf = cfg[(0,0)]
                            while 1:
                                detail_info = list(self.device.ctrl_transfer(0xA1, 0x01, 0x0100, 0, 32))
                                mirror.text(str(detail_info))
                                data = ""
                                data = self.device.read(0x02, 32, 1000)
                                if data != "":
                                    mirror.text(">>>" + str(list(data)))
                                #time.sleep(.1)
                            """

                            while detail_info == None:

                                if product == 'EPOC+':
                                    detail_info = list(self.device.ctrl_transfer(0xA1, 0x01, 0x0100, 0, 32))
                                else:
                                    detail_info = list(self.device.ctrl_transfer(0xA1, 0x01, 0x0300, 1, 31))

                                if detail_info == None:
                                    continue
                                device_firmware   = "0x" + str(hex(detail_info[2]))[2:] +  str(hex(detail_info[3])[2:])
                                software_firmware = "0x" + str(hex(detail_info[4]))[2:] +  str(hex(detail_info[5])[2:])

                            if eval(self.cyIO.getInfo("verbose")) == True:
                                mirror.text(str(list(detail_info)))
                                mirror.text(" Device Firmware = "       + device_firmware)
                                mirror.text(" Software Firmware = "     + software_firmware)

                            self.serial_number = str(cyPyUSB.util.get_string(self.device, self.device.iSerialNumber))
                            self.product_name = str(cyPyUSB.util.get_string(self.device, select_device.iProduct))



        
        
        if devicesUsed == 0:
            mirror.text("\r\n> No USB Device Available. Exiting . . . \r\n")
            os._exit(0)
        
        self.cyIO.setInfo("DeviceObject", self.device)
        self.cyIO.setInfo("device",       self.product_name)
        self.cyIO.setInfo("deviceFirmware",  device_firmware)
        self.cyIO.setInfo("softFirmware",    software_firmware)

        self.cyIO.setInfo("serial",   self.serial_number)
        
        if self.product_name == 'EPOC+':
            settings_menu(self.device , self.cyIO, intf);
            return ""
        sn = bytearray()

        for i in range(0,len(self.serial_number)):
            sn += bytearray([ord(self.serial_number[i])])
            
        
        if len(sn) != 16:
            return           
            
        k = ['\0'] * 16
            
        # --- Model 6 >  [Epoc+::Consumer]
        if model == 6:
            k = [sn[-1],sn[-2],sn[-2],sn[-3],sn[-3],sn[-3],sn[-2],sn[-4],sn[-1],sn[-4],sn[-2],sn[-2],sn[-4],sn[-4],sn[-2],sn[-1]]
            self.samplingRate = 256
            self.channels = 40
        
        # --- Model 7 > [EPOC+::Standard]-(14-bit mode)
        if model == 7: 
            k = [sn[-1],00,sn[-2],21,sn[-3],00,sn[-4],12,sn[-3],00,sn[-2],68,sn[-1],00,sn[-2],88]
            self.samplingRate = 128
            self.channels = 40

            # 1223332414224421
        #  Set Sampling/Channels Specific to Headset.
        # ¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯
        self.cyIO.setInfo("sampling",str(self.samplingRate))
        self.cyIO.setInfo("channels",str(self.channels))
        self.cyIO.setInfo("keymodel",str(model))

        if eval(self.cyIO.getInfo("verbose")) == True:
            mirror.text("═" *90)
            mirror.text("   AES Key = " + str(k))
        return k
        
    #  PyWinUSB (/cyUSB) Raw Data Handler. Thread.
    # ¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯
    def dataHandler(self, data):
        if eeg_driver == "pyusb":
            return
        try:
            if self.outputraw == True:
                mirror.text(str(list(data)))
        except:
            pass
        join_data = ''.join(map(chr, data[1:]))
        tasks.put(join_data)
        # Note: PyWinUSB receives 33 bytes of data. First byte is always 0.
        return True

    #  (Epoc+) Data Conversion.
    # ¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯
    def convertEPOC_PLUS(self, value_1, value_2):
        
       
        edk_value = "%.8f" % (((int(value_1) * .128205128205129) + 4201.02564096001) + ((int(value_2) -128) * 32.82051289))
        if self.integer == True:
            return str(int(float(edk_value)))
        return edk_value
         
    #  eegThread. (Thread Start).
    # ¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯


    def run(self, key, cyIO):

        #  Display Active Python Process Threads.
        # ¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯
        if eval(cyIO.getInfo("verbose")) == True:
            t_array = str(list(map(lambda x: x.getName(), threading.enumerate())))
            mirror.text("\r\nActive Threads = {")
            mirror.text("   " + t_array)
            mirror.text("} \r\n")


        tasks.queue.clear()

        #  Bypass Sending Header Data.
        # ¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯
        if eval(cyIO.getInfo("noheader")) == False:

            #  Connected. Send Device Header to Data Stream.
            # ¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯
            if eval(cyIO.getInfo("status")) == True and eval(cyIO.getInfo("noweb")) == False:
                cyIO.sendInfo("device")
                cyIO.sendInfo("serial")
                cyIO.sendInfo("keymodel")
                cyIO.sendInfo("config")
                cyIO.sendInfo("datamode")
                cyIO.sendData(1,"CyKITv2:::Info:::delimiter:::" + str(ord(cyIO.getInfo("delimiter"))))

        self.generic = cyIO.getInfo("generic")

        #  Update Local Variables from ControllerIO Dictionary.
        # ¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯

        for index in self.configFlags:
            setattr(self, index, eval(cyIO.getInfo(index)))
                            
        #  EPOC+ Mode. (Direct USB Connection)
        # ¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯
        if key == "":
            while self.running:
                time.sleep(0)
                
                if eval(cyIO.getInfo("status")) != True:
                    time.sleep(0)
                    self.running = False
                    continue
            return
        AES_key = key


        #  Create AES(ECB) Cipher.
        # ¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯
        try:
            print(key)
            AES_key = bytes(bytearray(key))
            cipher = AES.new(AES_key, AES.MODE_ECB)

        except Exception as exception:
            mirror.text( " eegThread.run() : E1. Failed to Create AES Cipher ::: " + (str(exception)))

        while self.running:

            time.sleep(0)

            if self.blankdata == True:
                try:
                    if self.blank_data[self.KeyModel] == None:
                        mirror.text(" ¯¯¯¯ No 'blankdata' for this model. Disabling 'blankdata' Mode.")
                        self.blankdata = False
                        return
                    data = self.blank_data[self.KeyModel]
                    join_data = ''.join(map(chr, data))
                    time.sleep(0) # Slow it down.
                    encrypted_blank_cipher = b"0" + (cipher.encrypt(bytes(join_data,'latin-1')))               
                except Exception as e:
                    mirror.text(" ¯¯¯¯ eegThread.run() Failed to Create Blank Cipher. Disabling 'blankdata' Mode.")
                    mirror.text(" =E.4: " + str(e))
                    self.blankdata = False
                    return
                    
                if eeg_driver == "pyusb":
                    tasks.put(encrypted_blank_cipher[1:])

                
            if eeg_driver == "pyusb" and self.blankdata == False:


                print(self.device)
                task = self.device.read(0x82, 32, 100)
                print('2')
                tasks.put(task.tostring())


            
            sleep_time = time.time()
            dataLoss = 0

            pre_deep_learning = []


            while not tasks.empty() and self.running == True:
                time.sleep(0)

                if eeg_driver == "pyusb":
                    if self.blankdata == False:
                        try:
                            task = self.device.read(0x82, 32, 1000)
                            tasks.put(task.tostring())
                        except Exception as e:
                            if str(e.errno) != "10060":
                                mirror.text("Error.eeg() = " + str(e.errno))
                                exc_type, ex, tb = sys.exc_info()
                                imported_tb_info = traceback.extract_tb(tb)[-1]
                                line_number = imported_tb_info[1]
                                print_format = "{}: Exception in line: {}, message: {}"
                            if 'dataLoss' not in locals():
                                dataLoss = 0
                            dataLoss += 1
                            if dataLoss > 50:
                                mirror.text("\r\n ░░░ Device Interference or Turned Off ░░░ \r\n")
                                if cyIO.isRecording() == True:
                                    cyIO.stopRecord()
                    else:
                        time.sleep(0)
                        tasks.put(encrypted_blank_cipher[1:])


                #  Update Run-Time Config Options.
                # ¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯
                self.format = int(cyIO.getInfo("format"))
                self.datamode = int(cyIO.getInfo("datamode"))
                self.delimiter = cyIO.getInfo("delimiter")
                self.baseline = eval(cyIO.getInfo("baselinemode"))


                try:
                    counter_data = ""
                    packet_data = ""
                    filter_data = ""
                    if eeg_driver == "pyusb":
                        task = tasks.get()
                        data = cipher.decrypt(task)
                        if self.outputraw == True:
                            mirror.text(str(list(task)))

                    self.getSeconds = int(time.time() % 60)

                    #  Epoc+
                    # ¯¯¯¯¯¯¯¯
                    if self.KeyModel == 6 or self.KeyModel == 5:

                        if str(data[1]) == "16":
                            if self.datamode == 2:
                                continue

                        if str(data[1]) == "32":
                            self.format = 1
                            if self.datamode == 1:
                                continue

                        if self.nocounter == True:
                            counter_data = ""
                        else:
                            counter_data = str(data[0]) + self.delimiter + str(data[1]) + self.delimiter

                        # ~Format 0: (Default) (Decode to Floating Point)
                        # ¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯
                        if self.format < 1:

                            packet_data_list = []
                            for i in range(2,16,2):
                                packet_data = packet_data + str(self.convertEPOC_PLUS(str(data[i]), str(data[i+1]))) + self.delimiter
                                packet_data_list.append(float(self.convertEPOC_PLUS(str(data[i]), str(data[i+1]))))

                            for i in range(18,len(data),2):
                                packet_data = packet_data + str(self.convertEPOC_PLUS(str(data[i]), str(data[i+1]))) + self.delimiter
                                packet_data_list.append(float(self.convertEPOC_PLUS(str(data[i]), str(data[i+1]))))

                            packet_data = packet_data[:-len(self.delimiter)]
                            #mirror.text(str(packet_data))
                            pre_deep_learning.append(packet_data_list)
                            if (len(pre_deep_learning) >= 512):
                                pre_deep_learning_array = np.array(pre_deep_learning[-256:])
                                pre_deep_learning_array = np.reshape(pre_deep_learning_array, [256, -1])
                                filterarray = np.array(pre_deep_learning[-512:])
                                filterarray = np.reshape(filterarray, [512,-1])
                                pre_deep_learning = pre_deep_learning[-512:]
                                global pre_filter
                                pre_filter = filterarray
                                global npeeg
                                npeeg = pre_deep_learning_array
                                modify(pre_filter)
                                modify2(npeeg)
                                self.baseline = False

                            #  Averages Signal Data and Sends to Client.
                            # ¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯

                            if self.baseline == True:
                                
                                if (int(time.time() % 60) - self.baseSeconds) == 1:  # Baseline Every Second.
                                    #mirror.text("BASELINE ¯¯¯¯¯¯¯ " + str(self.baseline))
                                    try:
                                        if 'baseline_values' in locals():
                                            baseline_last = baseline_values
                                        baseline_values = [float(x) for x in packet_data.split(self.delimiter)]

                                        if baseline_values != None and 'baseline_last' in locals():
                                            baseline_values = list(map(operator.add, baseline_last, baseline_values))
                                            set_values = ([2] * len(baseline_values))
                                            baseline_values = list(map(operator.truediv, baseline_values, set_values))

                                            #  Re-order values.
                                            # ¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯
                                            # self.epocOrder = [2,3,0,1,4,5,6,7,8,9,12,13,10,11]
                                            #baseline_new = [baseline_values[i] for i in self.epocOrder]

                                            cyIO.setBaseline(baseline_values)
                                            
                                            send_baseline = [0.0,float(str(data[1]))] + baseline_values
                                            
                                            send_baseline = str(send_baseline)
                                            
                                            send_baseline = send_baseline[1:]
                                            
                                            send_baseline = send_baseline[:(len(send_baseline)-1)]
                                            if self.outputdata == True:
                                                mirror.text("Python Baseline:::")
                                                mirror.text(str(send_baseline))
                                            
                                            cyIO.sendData(1, "CyKITv2:::Baseline:::" + str(send_baseline))
                                    
                                    except Exception as e:
                                        exc_type, ex, tb = sys.exc_info()
                                        imported_tb_info = traceback.extract_tb(tb)[-1]
                                        line_number = imported_tb_info[1]
                                        print_format = "{}: Exception in line: {}, message: {}"
                                        mirror.text(" ¯¯¯¯ eegThread.run() Error Creating Baseline Data.")
                                        mirror.text(" =E.7: " + print_format.format(exc_type.__name__, line_number, ex))    
                                self.baseSeconds = int(time.time() % 60)
                            
                            #  Contact Quality. RMS Value.
                            # ¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯
                            #if self.quality == True:
                            #baseline_values = map(math.sqrt, baseline_values)

                            if self.nobattery == False:
                                    packet_data = packet_data + self.delimiter + str(data[16]) + str(self.delimiter) + str(data[17])


                            if self.outputdata == True:
                                pass
                                # print(packet_data)
                                #mirror.text(str(counter_data + packet_data))



                    try:
                        if self.filter == True and self.format == 0:
                            if 'baseline_values' in locals():
                                mirror.text(str("Baseline:"))
                                mirror.text(str(packet_data))
                                if self.nocounter == False:
                                    split_packet = packet_data.split(self.delimiter)
                                    split_packet = split_packet[:-2]
                                else:
                                    split_packet = packet_data.split(self.delimiter)


                                convert_packet = [float(x) for x in split_packet]
                                filter_data = map(operator.sub, baseline_values, convert_packet)
                                mirror.text(str("subtract::"))
                                mirror.text(str(convert_packet))
                                packet_data = str(filter_data)
                                packet_data = packet_data[1:]
                                packet_data = packet_data[:(len(packet_data)-1)]


                    except OSError as e:
                        error_info = str(e.errno)
                        if error_info == "10035":
                            self.time_delay += .001
                            time.sleep(self.time_delay)
                            continue

                        if error_info == 9 or error_info == 10053 or error_info == 10035 or error_info == 10054:
                            mirror.text("\r\n Connection Closing.\r\n")

                            tasks.queue.clear()
                            if self.generic == True:
                                cyIO.onClose("0")
                            else:
                                cyIO.onClose("1")
                                if eeg_driver == "pywinusb":
                                    self.device.close()
                                cyIO.stopRecord()
                            continue
                        mirror.text(" ¯¯¯¯ eegThread.run() Error creating OpenVibe Data and or Filtering Data.")

                except Exception as e:
                    exc_type, ex, tb = sys.exc_info()
                    imported_tb_info = traceback.extract_tb(tb)[-1]
                    line_number = imported_tb_info[1]
                    print_format = "{}: Exception in line: {}, message: {}"
                    mirror.text(" ¯¯¯¯ eegThread.run() Error Formatting Data.")
                    mirror.text(" =E.8: " + print_format.format(exc_type.__name__, line_number, ex))    

                    #  So Long. Merci for the <)))<.
                    # ¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯
        print('stopped!!!!!!!!!!!!!!!!!!!!!!!!!!')