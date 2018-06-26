#Domoticz Python plugin for Monitoring and logging of battery UPS level 
"""
<plugin key="UPS" name="Raspi UPS" author="avgays" version="0.1" wikilink="" externallink="http://www.raspberrypiwiki.com/index.php/Raspi_UPS_HAT_Board">
    <params>
        <param field="Mode1" label="Polling interval (minutes, 2 min)" width="40px" required="true" default="5"/>
        
        <param field="Mode4" label="UPS Model" width="75px">
            <options>
                <option label="1.1" value="1.1" />
                <option label="1.0" value="1.0"  default="true" />
            </options>
        </param>

        <param field="Mode5" label="Log" width="75px">
            <options>
                <option label="True" value="Yes" />
                <option label="False" value="No"  default="true" />
            </options>
        </param>
        <param field="Mode6" label="Debug" width="75px">
            <options>
                <option label="True" value="Debug" />
                <option label="False" value="Normal"  default="true" />
            </options>
        </param>
    </params>
</plugin>
"""
import Domoticz
from datetime import datetime
from datetime import timedelta

import struct
import smbus
import sys
import os

# import xml.etree.ElementTree as xml
# import glob

# 

icons = {"UPS_full": "UPS_full.zip",
         "UPS_ok": "UPS_ok.zip",
         "UPS_low": "UPS_low.zip",
         "UPS_empty": "UPS_empty.zip"}

class BasePlugin:

    def __init__(self):
        self.debug = False
        self.nextupdate = datetime.now()
        self.pollinterval = 5  # default polling interval in minutes
        self.error = False
        self.myLog = False
        self.voltage = 0
        self.percent = 0
        self.bus = smbus.SMBus(1) # 1 = /dev/i2c-1 (port I2C1)
        self.address = 0x36
        self.v_constant = 78.125
        return

    def onStart(self):
        global icons
        Domoticz.Debug("onStart called")
        if Parameters["Mode6"] == 'Debug':
            self.debug = True
            Domoticz.Debugging(1)
            DumpConfigToLog()
        else:
            Domoticz.Debugging(0)
        
        if Parameters["Mode4"] == '1.0':
            self.address = 0x36
            self.v_constant = 78.125
        else:
            self.address = 0x62
            self.v_constant = 305

        ## load custom battery images
        for key, value in icons.items():
            if key not in Images:
               Domoticz.Image(value).Create()
               Domoticz.Debug("Added icon: " + key + " from file " + value)

        Domoticz.Debug(">>>>>>>>>Number of icons loaded = " + str(len(Images)))
        for image in Images:
            Domoticz.Debug(">>>>>>>>>>>>>Icon " + str(Images[image].ID) + " " + Images[image].Name)

        # check polling interval parameter
        try:
            temp = int(Parameters["Mode1"])
        except:
            Domoticz.Error("Invalid polling interval parameter")
        else:
            if temp < 2:
                temp = 2  # minimum polling interval
                Domoticz.Error("Specified polling interval too short: changed to 2 minutes")
            elif temp > 60:
                temp = 60  # maximum polling interval is 60 minutes
                Domoticz.Error("Specified polling interval too long: changed to 60 minutes")
            self.pollinterval = temp
        Domoticz.Log("Using polling interval of {} minutes".format(str(self.pollinterval)))
        
        # check log param
        if Parameters["Mode6"] == 'Debug':
            self.myLog = True
            logFile=str(Parameters["HomeFolder"])+"ups.log"
        
        if (len(Devices) == 0):
            Domoticz.Device(Name="UPSPers", Unit=1, TypeName="Custom", Options={"Custom": "1;%"}).Create()
            Domoticz.Device(Name="UPSVolts", Unit=2, TypeName="Voltage").Create()

    def onStop(self):
        Domoticz.Debug("onStop called")
        Domoticz.Debugging(0)

    def onHeartbeat(self):
        now = datetime.now()
        if now >= self.nextupdate:
            self.nextupdate = now + timedelta(minutes=self.pollinterval)
            self.pollUPS()

    # UPS specific methods
    def pollUPS(self):
        Domoticz.Debug("pollUPS called")
        self.voltage = self.readVoltage()
        self.percent = self.readCapacity()
        self.UpdatePercent(1, self.percent)
        Devices[2].Update(nValue=0, sValue=str(self.voltage))
    
    def readVoltage(self):
        read = self.bus.read_word_data(self.address, 2)
        swapped = struct.unpack("<H", struct.pack(">H", read))[0]
        voltage = swapped * self.v_constant /1000000
        return voltage

    def readCapacity(self):
        read = self.bus.read_word_data(self.address, 4)
        swapped = struct.unpack("<H", struct.pack(">H", read))[0]
        capacity = swapped/256
        return capacity

    def UpdatePercent(self, Unit, Percent):
        # Make sure that the Domoticz device still exists (they can be deleted) before updating it
        levelBatt = int(Percent)
        if levelBatt >= 75:
            icon = "UPS_full"
        elif levelBatt >= 50:
            icon = "UPS_ok"
        elif levelBatt >= 25:
            icon = "UPS_low"
        else:
            icon = "UPS_empty"
        if levelBatt < 10:
            os.system("sudo shutdown")
        try:
            Devices[Unit].Update(nValue=0, sValue=str(levelBatt), Image=Images[icon].ID)
        except:
            Domoticz.Error("Failed to update device unit " + str(Unit))
            Domoticz.Error("icon " + str(icon) + "levelBat" + str(levelBatt))
        return

global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

# Generic helper functions
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return
