# Broadlink SP2 mini
#
# Author: avg
#
"""
<plugin key="BroadlinkSP2" name="Broadlink SP2 mini" author="avgays" version="1.0.0" wikilink="http://www.domoticz.com/wiki/plugins/plugin.html" externallink="http://www.ibroadlink.com/">
    <params>
        <param field="Address" label="IP Address" width="200px" required="true" default="192.168.0.22"/>
        <param field="Port" label="Port" width="30px" required="true" default="80"/>
        <param field="Mode1" label="MAC Address" width="150px" required="true" default="b4430d96fa54"/>
        <param field="Mode2" label="Reconect delay, minutes" width="150px" required="false" default="3"/>
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
    mySP2 = 1
    isPower = True
    isFound = False
    isConnected = False
    downcount = 0
    comBuff=''
    delay=1

    def __init__(self):
        return

    def onStart(self):
        if Parameters["Mode6"] == "Debug":
            Domoticz.Debugging(1)
            
        try: self.delay = int(Parameters["Mode2"])
        except ValueError: self.delay=1
        if (self.delay<1): self.delay=1
        
        if (len(Devices) == 0):
            Domoticz.Device(Name="SP2", Unit=1, Type=17, Switchtype=0,  Image=1).Create()
            Domoticz.Log("Devices SP2 created.")
            
        self.mySP2=broadlink.sp2(host=(Parameters["Address"], int(Parameters["Port"])), mac=bytearray.fromhex(Parameters["Mode1"]))
        try:
            self.isFound = self.mySP2.auth()
            self.isConnected = True
        except socket.timeout:
            self.isConnected = False
            self.isFound = False
        
        if(self.isConnected):
            UpdateDevice(1, self.mySP2.check_power(), "")
        else:
            Domoticz.Error("Devices SP2 at "+ Parameters["Address"] +" not found")
        Domoticz.Heartbeat(60)
        Domoticz.Debug("onStart called. isConnected: " + str(self.isConnected) + " isFound: " + str(self.isFound))
        Domoticz.Debug("Delay is set " + str(self.delay) + " minutes")

    def onStop(self):
        self.isConnected=False
        Domoticz.Log("onStop called")

    def onConnect(self, Status, Description):
        Domoticz.Log("onConnect called")

    def onMessage(self, Data, Status, Extra):
        Domoticz.Log("onMessage called")

    def onCommand(self, Unit, Command, Level, Hue):
        self.comBuff=str(Command)
        self.isPower = True if (Command == 'On') else False
        if(self.isConnected):
            i=3
            while (i):
                try:
                    self.mySP2.set_power(self.isPower)
                    UpdateDevice(1, self.isPower, "")
                    self.comBuff=""
                    break 
                except socket.timeout:
                    i-=1
                    continue
            if (i==0):    
                self.isConnected = False
                self.downcount=self.delay
                Domoticz.Error("Devices SP2  error. Will try to reconect in 5 minutes " + str(i) + " comBuff: " + self.comBuff )
            Domoticz.Debug("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level)+ "', Hue: " + str(Hue))

    def onNotification(self, Data):
        Domoticz.Log("onNotification: " + str(Data))

    def onDisconnect(self):
        Domoticz.Log("onDisconnect called")

    def onHeartbeat(self):
        if(self.isFound):
            if(self.isConnected):
                if (self.comBuff>""):
                    self.onCommand(1,self.comBuff,0,0)
                try:
                    self.isPower=self.mySP2.check_power()
                except socket.timeout:
                    self.isConnected = False
                    self.downcount=self.delay
                    Domoticz.Error("Devices SP2  error. Will try to reconect in 5 minutes" + " comBuff: " + self.comBuff )
                UpdateDevice(1, self.isPower, "")
            else:
                self.downcount-=1
                if (self.downcount==0): self.isConnected = True
        else:
            try:
                self.isFound=self.mySP2.auth()
                self.isConnected=True
            except socket.timeout:
                self.isConnected=False
                self.isFound=False
                Domoticz.Error("Devices SP2 not found.")
        Domoticz.Debug("onHeartbeat called. isConnected: " + str(self.isConnected) + " isFound: " + str(self.isFound) + " comBuff: " + self.comBuff )

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