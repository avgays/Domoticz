# Broadlink A1 mini
# Author: avgays
# Using python library created by Matthew Garrett
# https://github.com/mjg59/python-broadlink
"""
<plugin key="BroadlinkRM" name="Broadlink RM" author="avgays" version="0.1.0" wikilink="http://www.domoticz.com/wiki/Developing_a_Python_plugin" externallink="http://www.ibroadlink.com/">
    <params>
        <param field="Address" label="IP Address" width="200px" required="true" default="192.168.0.14"/>
        <param field="Port" label="Port" width="30px" required="true" default="80"/>
        <param field="Mode1" label="MAC Address" width="150px" required="true" default="b4430daa813b"/>
        <param field="Mode6" label="Debug" width="75px">
            <options>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal"  default="true" />
            </options>
        </param>
    </params>
</plugin>
"""
import Domoticz
import broadlink
import socket


class BasePlugin:
    myRM = 1
    isFound = False
    
    def __init__(self):
        return

    def onStart(self):
        if Parameters["Mode6"] == "Debug":
            Domoticz.Debugging(1)
        if (len(Devices) == 0):
            Domoticz.Device(Name="Temp", Unit=1, TypeName="Temperature").Create()
        self.myRM=broadlink.a1(host=(Parameters["Address"], int(Parameters["Port"])), mac=bytearray.fromhex(Parameters["Mode1"]))
        try:
            self.isFound = self.myRM.auth()
        except socket.timeout:
            self.isFound = False
            Domoticz.Error("RM not found")
        Domoticz.Heartbeat(60)
        Domoticz.Debug("onStart called")

    def onStop(self):
        Domoticz.Log("onStop called")

    def onConnect(self, Status, Description):
        Domoticz.Log("onConnect called")

    def onMessage(self, Data, Status, Extra):
        Domoticz.Log("onMessage called")

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Debug("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level)+ "', Hue: " + str(Hue))

    def onNotification(self, Data):
        Domoticz.Log("onNotification: " + str(Data))

    def onDisconnect(self):
        Domoticz.Log("onDisconnect called")

    def onHeartbeat(self):
        if(self.isFound): 
            try:
                temperature=self.myRM.check_temperature()
                UpdateDevice(1, 1, str(temperature),100,100)
                Domoticz.Debug("Temp: " + str(temperature))
            except socket.timeout:
                Domoticz.Debug("RM Timeout")
        else:
            try:
                self.isFound = self.myRM.auth()
            except socket.timeout:
                self.isFound = False
                Domoticz.Error("RM not found")
        Domoticz.Debug("onHeartbeat called")

global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Status, Description):
    global _plugin
    _plugin.onConnect(Status, Description)

def onMessage(Data, Status, Extra):
    global _plugin
    _plugin.onMessage(Data, Status, Extra)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Data):
    global _plugin
    _plugin.onNotification(Data)

def onDisconnect():
    global _plugin
    _plugin.onDisconnect()

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

def UpdateDevice(Unit, nValue, sValue):
    # Make sure that the Domoticz device still exists (they can be deleted) before updating it 
    if (Unit in Devices):
        if (Devices[Unit].nValue != nValue) or (Devices[Unit].sValue != sValue):
            Devices[Unit].Update(nValue, str(sValue))
            Domoticz.Debug("Update "+str(nValue)+":'"+str(sValue)+"' ("+Devices[Unit].Name+")")
    return
