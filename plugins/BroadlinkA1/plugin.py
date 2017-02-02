# Broadlink A1 mini
# Author: avgays
# Using python library created by Matthew Garrett
# https://github.com/mjg59/python-broadlink
"""
<plugin key="BroadlinkA1" name="Broadlink A1" author="avgays" version="0.3.1" wikilink="http://www.domoticz.com/wiki/Developing_a_Python_plugin" externallink="http://www.ibroadlink.com/">
    <params>
        <param field="Address" label="IP Address" width="200px" required="true" default="192.168.0.24"/>
        <param field="Port" label="Port" width="30px" required="true" default="80"/>
        <param field="Mode1" label="MAC Address" width="150px" required="true" default="b4430d704be6"/>
        <param field="Mode2" label="Reconect Delay, minutes" width="30px" required="true">
            <options>
                <option label="1" value="1"/>
                <option label="2" value="2" default="true"/>
                <option label="3" value="3"/>
                <option label="4" value="4"/>
                <option label="5" value="5"/>
            </options>
        </param>
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


myLight={0:'Dark',1:'Dim',2:'Normal',3:'Bright'}
myNoise={0:'Quiet',1:'Normal', 2:'Noisy',3:'Very noisy'}
myAir={0:'Excellent',1:'Good', 2:'Normal',3:'Bad'}


class BasePlugin:
    myA1 = 1
    delay = 1
    isFound = False
    isConnected = False
    downcount = 0
    
    def __init__(self):
        return

    def onStart(self):
        if Parameters["Mode6"] == "Debug":
            Domoticz.Debugging(1)
        self.delay = int(Parameters["Mode2"])
        if (len(Devices) == 0):
            Domoticz.Device(Name="A1", Unit=1, TypeName="Temp+Hum").Create()
            Domoticz.Device(Name="Sound", Unit=2, TypeName="Text").Create()
            Domoticz.Device(Name="Air", Unit=3, TypeName="Text").Create()
            Domoticz.Device(Name="Light", Unit=4, TypeName="Text").Create()
            Domoticz.Log("Devices A1 created.")
            
        self.myA1=broadlink.a1(host=(Parameters["Address"], int(Parameters["Port"])), mac=bytearray.fromhex(Parameters["Mode1"]))
        try:
            self.isFound = self.myA1.auth()
            self.isConnected = True
        except socket.timeout:
            self.isConnected = False
            self.isFound = False
        if (isConnected):
            Domoticz.Debug("onStart called. isConnected: " + str(self.isConnected) + " isFound: " + str(self.isFound))
        else:
            Domoticz.Error("Devices A1 at "+ Parameters["Address"] +" not found")
        Domoticz.Heartbeat(60)
        Domoticz.Debug("onStart called")
        Domoticz.Debug("Delay is set " + str(self.delay) + " minutes")

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
        result=self.myA1.check_sensors_raw()
        temperature = result['temperature']
        humidity = result['humidity']
        noise = result['noise']
        light = result['light']
        air_quality = result['air_quality']
        hum_stat=77
        if (humidity<30):
            hum_stat=2
        elif (humidity>=30 and humidity<=45):
            hum_stat=0
        elif (humidity>=45 and humidity<=70):
            hum_stat=1
        else:
            hum_stat=3
        UpdateDevice(1, 1, str(temperature) + ";" + str(humidity)+ ";"+ str(hum_stat))
        UpdateDevice(2, 1, str(myNoise[noise]))
        UpdateDevice(3, 1, str(myAir[noise]))
        UpdateDevice(4, 1, str(myLight[light]))
        
        Domoticz.Debug("result temp: " + str(temperature) + ", Hym: " + str(humidity) + ", noise: " + str(noise) + "', light: " + str(light) + ", air_quality: " + str(air_quality) + ", hum_stat: " + str(hum_stat))
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
