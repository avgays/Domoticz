# Broadlink A1
# Author: avgays
# Using python library created by Matthew Garrett
# https://github.com/mjg59/python-broadlink
"""
<plugin key="BroadlinkA1" name="Broadlink A1" author="avgays" version="0.3.2" wikilink="http://www.domoticz.com/wiki/Developing_a_Python_plugin" externallink="http://www.ibroadlink.com/">
    <params>
        <param field="Address" label="IP Address" width="200px" required="true" default="192.168.0.24"/>
        <param field="Port" label="Port" width="30px" required="true" default="80"/>
        <param field="Mode1" label="MAC Address" width="150px" required="true" default="b4430d704be6"/>
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


myLight={0:(0,'Dark'),1:(1,'Dim'),2:(2,'Normal'),3:(3,'Bright')}
myNoise={0:(1,'Quiet'),1:(1,'Normal'), 2:(2,'Noisy'),3:(4,'Very noisy')}
myAir={0:(1,'Excellent'),1:(1,'Good'), 2:(2,'Normal'),3:(3,'Bad')}

class BasePlugin:
    myA1 = 1
    isFound = False
    downcount = 0
    
    def __init__(self):
        return

    def onStart(self):
        if Parameters["Mode6"] == "Debug":
            Domoticz.Debugging(1)
        if (len(Devices) == 0):
            Domoticz.Device(Name="A1", Unit=1, TypeName="Temp+Hum").Create()
            Domoticz.Device(Name="Sound", Unit=2, TypeName="Alert").Create()
            Domoticz.Device(Name="Air", Unit=3, TypeName="Alert").Create()
            Domoticz.Device(Name="Light", Unit=4, TypeName="Alert").Create()
            
        self.myA1=broadlink.a1(host=(Parameters["Address"], int(Parameters["Port"])), mac=bytearray.fromhex(Parameters["Mode1"]))
        try:
            self.isFound = self.myA1.auth()
        except socket.timeout:
            self.isFound = False
            Domoticz.Error("A1 not found")
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
            result=self.myA1.check_sensors_raw()
            temperature = result['temperature']
            humidity = result['humidity']
            noise = result['noise']
            light = result['light']
            air_quality = result['air_quality']
            hum_stat=3
            if (humidity<30): hum_stat=2
            elif (humidity>=30 and humidity<=45): hum_stat=0
            elif (humidity>=45 and humidity<=70): hum_stat=1
            UpdateDevice(1, 1, str(temperature) + ";" + str(humidity)+ ";"+ str(hum_stat))
            UpdateDevice(2, int(myNoise[noise][0]), str(myNoise[noise][1]))
            UpdateDevice(3, int(myAir[noise][0]), str(myAir[noise][1]))
            UpdateDevice(4, int(myLight[light][0]), str(myLight[light][1]))
            Domoticz.Debug("result temp: " + str(temperature) + ", Hym: " + str(humidity) + ", noise: " + str(noise) + "', light: " + str(light) + ", air_quality: " + str(air_quality) + ", hum_stat: " + str(hum_stat))
        else:
            try:
                self.isFound = self.myRM.auth()
            except socket.timeout:
                self.isFound = False
                Domoticz.Error("A1 not found")
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
            Devices[Unit].Update(nValue=nValue, sValue=str(sValue), SignalLevel=100, BatteryLevel=255)
            Domoticz.Log("Update "+str(nValue)+":'"+str(sValue)+"' ("+Devices[Unit].Name+")")
    return
