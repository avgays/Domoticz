# Domoticz Lifx Plugin
# Uses lightsd, a daemon to control smart bulbs by lopter: https://github.com/lopter/lightsd/
#
"""
<plugin key="Lifx" name="Lifx Plugin" author="avgays" version="1.2.1" wikilink="http://www.domoticz.com/wiki/plugins/plugin.html" externallink="https://www.lifx.com/">
    <params>
        <param field="Address" label="IP Address" width="200px" required="true" default="127.0.0.1"/>
        <param field="Port" label="Port" width="50px" required="true" default="32069"/>
        <param field="Mode3" label="Unix Socket" width="200px" required="true" default="/var/run/lightsd//socket"/>
        <param field="Mode4" label="Socket Type" width="75px" required="true">
            <options>
                <option label="UNIX" value="UNIX" default="true" />
                <option label="INET" value="INET"  />
            </options>
        </param>
        <param field="Mode5" label="Rescan" width="75px">
            <options>
                <option label="True" value="Rescan"/>
                <option label="False" value="Normal"  default="true" />
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
import json
import base64
import socket
import random

READ_SIZE = 4096
ENCODING = "utf-8"
#devtypes={"Original 1000":(244,73),"White 800":(244,73),"LIFX Z":(244,73)}

class BasePlugin:
    lightsd_socket=""
    mydevices={}
    inv_mydevices = {}
    HBpass=0
    
    def __init__(self):
         return

    def onStart(self):
        if Parameters["Mode6"] == "Debug":
            Domoticz.Debugging(1)
            
        if Parameters["Mode4"] == "INET":
            Domoticz.Debug("INET")
            self.lightsd_socket = socket.socket(socket.AF_INET)
            self.lightsd_socket.connect((str(Parameters["Address"]),int(Parameters["Port"])))
            
        else:
            Domoticz.Debug("UNIX")
            self.lightsd_socket = socket.socket(socket.AF_UNIX)
            self.lightsd_socket.connect(str(Parameters["Mode3"]))
            
        self.lightsd_socket.settimeout(1)  # seconds            
        confFile=str(Parameters["HomeFolder"])+"_lifx"
        try:
            with open(confFile) as infile:
                self.mydevices = json.load(infile)
        except Exception:
            self.mydevices={}
        self.inv_mydevices = {v: k for k, v in self.mydevices.items()}
        
        #Domoticz.Device(Name="myName",  Unit=2, Type=244, Subtype=73, Switchtype=7).Create()
        #Domoticz.Device(Name="myName1",  Unit=5, Type=244, Subtype=73, Switchtype=7).Create()
        if Parameters["Mode5"] == "Rescan":
            for Device in list(self.mydevices.keys()):
                Domoticz.Debug(Device + ":"+ self.mydevices[Device])
                try:
                    found=Devices[int(Device)]
                except KeyError:
                    self.mydevices.pop(Device)
            k=0
            for devices in self.mydevices.keys():
                k=max(k,int(devices))
            myResult = queryLIFX()
            Domoticz.Debug("Devices " + str(self.mydevices))
            Domoticz.Debug("Devices " + str(k))
            for i in range(len(myResult)):
                myName = "Lamp"
                myPower=1
                myLevel=100
                myType=244
                mySType=73
                myPower=1 if (myResult[i]["power"]) else 0
                myLevel=str(int(myResult[i]["hsbk"][2]*100))
                MACADDR=str(myResult[i]["_lifx"]["addr"].replace(":",""))
                #myName = str(myResult[i]["Label"])
                myName = str(myResult[i]["_model"])
                try:
                    Unit=int(self.inv_mydevices[MACADDR])
                    UpdateDevice(Unit, myPower, myLevel)
                    Domoticz.Debug("Devices exist. " + str(k))
                except Exception:
                    k+=1
                    Domoticz.Device(Name=myName,  Unit=(k), Type=myType, Subtype=mySType, Switchtype=7).Create()
                    self.mydevices[str(k)]=MACADDR
                    Domoticz.Debug("Devices created. " + str(k))    
                    UpdateDevice(k, myPower, myLevel)
            with open(confFile, 'w') as outfile:
                json.dump(self.mydevices, outfile)
        self.inv_mydevices = {v: k for k, v in self.mydevices.items()}
        Domoticz.Heartbeat(25)
        Domoticz.Debug("onStart called")
        
    def onStop(self):
        Domoticz.Debug("onStop called")

    def onConnect(self, Status, Description):
        Domoticz.Debug("onConnect called")

    def onMessage(self, Data, Status, Extra):
        Domoticz.Debug("onMessage called:")

    def onCommand(self, Unit, Command, Level, Hue):
        MACADDR=self.mydevices[str(Unit)]
        if (Command == 'On'):
            setLIFX("power_on", [MACADDR])
            UpdateDevice(Unit, 1, Devices[Unit].sValue)
        elif (Command == 'Off'):
            setLIFX("power_off", [MACADDR])
            UpdateDevice(Unit, 0, Devices[Unit].sValue)
        elif (Command == 'Set Level'):
            myResult = queryLIFX(Params=MACADDR)
            h, s, b, k = myResult[0]["hsbk"]
            b=Level/100
            setLIFX("set_light_from_hsbk", [MACADDR, h,s,b,k,0])
            setLIFX("power_on", [MACADDR])
            UpdateDevice(Unit, 2, str(Level))
        Domoticz.Debug("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))

    def onNotification(self, Data):
        Domoticz.Debug("onNotification: " + str(Data))

    def onDisconnect(self):
        Domoticz.Debug("onDisconnect called")

    def onHeartbeat(self):
        if(self.HBpass==0):
            myResult = queryLIFX()
            for i in range(len(myResult)):
                myLevel=str(int(myResult[i]["hsbk"][2]*100))
                MACADDR=str(myResult[i]["_lifx"]["addr"].replace(":",""))
                myPower=1 if (myResult[i]["power"]) else 0
                try:
                    myDevice=int(self.inv_mydevices[MACADDR])
                    UpdateDevice(myDevice, myPower, myLevel)
                    Domoticz.Debug("Lifx #" + str(myDevice) + " power " + str(myPower) + " Level " + str(myLevel))
                except KeyError:
                    Domoticz.Debug("Unknown LIFX device found")
            self.HBpass=4
        else:
            self.HBpass-=1

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

def stringToBase64(s):
    return base64.b64encode(s.encode('utf-8')).decode("utf-8")

def queryLIFX(Command="get_light_state", Params="*"):
    request = json.dumps({"method": Command, "params": [Params], "jsonrpc": "2.0","id": str(random.randint(1, 50)),}).encode(ENCODING, "surrogateescape")
    _plugin.lightsd_socket.sendall(request)
    response = bytearray()
    while True:
        response += _plugin.lightsd_socket.recv(READ_SIZE)
        try:
            json.loads(response.decode(ENCODING, "ignore"))
            break
        except Exception:
            continue
    response = response.decode(ENCODING, "surrogateescape")
    return json.loads(response)["result"]
    
def setLIFX(Command, Params=["*"]):
    request = json.dumps({"method": Command, "params": Params, "jsonrpc": "2.0",}).encode(ENCODING, "surrogateescape")
    _plugin.lightsd_socket.sendall(request) 
    return
