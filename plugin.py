@@ -0,0 +1,215 @@
# Lifx Plugin
#
#
"""
<plugin key="Lifx" name="Lifx Plugin" author="avgays" version="1.0.0" wikilink="http://www.domoticz.com/wiki/plugins/plugin.html" externallink="https://www.lifx.com/">
    <params>
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
_myuuid_templ='6a2e5c43-2342-4346-aea1-02ffad4454'
lightsd_socket = socket.socket(socket.AF_UNIX)
lightsd_socket.connect("/var/run/lightsd//socket")
lightsd_socket.settimeout(1)  # seconds
_mydevices={1:'d073d51098ca', 2:'d073d5109790',3:'d073d5109540',4:'d073d5108234',5:'d073d501aeb7',6:'d073d501a4f1',7:'d073d500477a',8:'d073d50031f8',9:'d073d5144e8b',}
_inv_mydevices = {v: k for k, v in _mydevices.items()}
devtypes={"Original 1000":(244,73),"White 800":(244,73),"LIFX Z":(244,73)}
#devtypes={"Original 1000":(241,2),"White 800":(244,73),"LIFX Z":(241,2)}
_HBpass=0

class BasePlugin:
    enabled = False
    def __init__(self):
         return

    def onStart(self):
        global _mydevices
        if Parameters["Mode6"] == "Debug":
            Domoticz.Debugging(1)
        if (len(Devices) == 0):
              for i in _mydevices:
                myName = "Lamp"
                myType=244
                mySType=73
                myAdress=_mydevices[i]
                myuuid=_myuuid_templ+str(random.randint(0, 9))+str(random.randint(0, 9))
                request = json.dumps({"method": "get_light_state", "params": [myAdress], "jsonrpc": "2.0","id": myuuid,}).encode(ENCODING, "surrogateescape")
                lightsd_socket.sendall(request)
                response = bytearray()
                while True:
                     response += lightsd_socket.recv(READ_SIZE)
                     try:
                         json.loads(response.decode(ENCODING, "ignore"))
                         break
                     except Exception:
                         continue
                response = response.decode(ENCODING, "surrogateescape")
                myResult =json.loads(response)["result"]
                if (len(myResult)>0):
                    myModel=str(myResult[0]["_model"])
                    myName = str(myModel)
                    #myType=devtypes[myModel][0]
                    #mySType=devtypes[myModel][1]
                    Domoticz.Debug(myModel+ " " + str(myType)+ " " + str(mySType))
                else:
                    Domoticz.Debug("Empty")
                # #myResult[0]["_model"]
                # #myResult[0]["label"]------
                # #myResult[0]["power"]
                # #myResult[0]["hsbk"]
                # myName = "Lamp"
                # if (myResult[0]):
                #     myName = str(myResult[0]["label"]) 
                #   #Domoticz.Device(Name="Lamp",  Unit=i, Type=244, Subtype=73, Switchtype=7).Create()
                
                Domoticz.Device(Name=myName,  Unit=i, Type=myType, Subtype=mySType, Switchtype=7).Create()
                Domoticz.Log("Devices created. " + str(i))
                
              Domoticz.Debug("Devices created. XXX ")

        Domoticz.Heartbeat(25)
        Domoticz.Debug("onStart called")

    def onStop(self):
        Domoticz.Debug("onStop called")

    def onConnect(self, Status, Description):
        Domoticz.Debug("onConnect called")

    def onMessage(self, Data, Status, Extra):
        Domoticz.Debug("onMessage called")

    def onCommand(self, Unit, Command, Level, Hue):
        global _mydevices
        myAdress=_mydevices[Unit]
        if (Command == 'On'):
            request = json.dumps({"method": "power_on", "params": [myAdress], "jsonrpc": "2.0",}).encode(ENCODING, "surrogateescape")
            UpdateDevice(Unit, 1, Devices[Unit].sValue)
        elif (Command == 'Off'):
            request = json.dumps({"method": "power_off", "params": [myAdress], "jsonrpc": "2.0",}).encode(ENCODING, "surrogateescape")
            UpdateDevice(Unit, 0, Devices[Unit].sValue)
        elif (Command == 'Set Level'):
            myLevel=Level/100
            request = json.dumps({"method": "set_light_from_hsbk", "params": [myAdress, 0,0,myLevel,3500,0], "jsonrpc": "2.0",}).encode(ENCODING, "surrogateescape")
            lightsd_socket.sendall(request)
            request = json.dumps({"method": "power_on", "params": [myAdress], "jsonrpc": "2.0",}).encode(ENCODING, "surrogateescape")
            UpdateDevice(Unit, 1, str(Level))
            
        lightsd_socket.sendall(request)    
        Domoticz.Debug("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))
        Domoticz.Debug("request:    " + str(request))
        Domoticz.Debug("Device nValue:    " + str(Devices[Unit].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[Unit].sValue + "'")

    def onNotification(self, Data):
        Domoticz.Debug("onNotification: " + str(Data))

    def onDisconnect(self):
        Domoticz.Debug("onDisconnect called")

    def onHeartbeat(self):
        global _mydevices, _myuuid_templ, _inv_mydevices, _HBpass
        if(_HBpass==0):
            myuuid=_myuuid_templ+str(random.randint(0, 9))+str(random.randint(0, 9))
            request = json.dumps({"method": "get_light_state", "params": ["*"], "jsonrpc": "2.0","id": myuuid,}).encode(ENCODING, "surrogateescape")
            lightsd_socket.sendall(request)
            response = bytearray()
            while True:
                response += lightsd_socket.recv(READ_SIZE)
                try:
                    json.loads(response.decode(ENCODING, "ignore"))
                    break
                except Exception:
                    continue
    
            response = response.decode(ENCODING, "surrogateescape")
            myResult =json.loads(response)["result"]
            for i in range(len(myResult)):
                myLevel=str(int(myResult[i]["hsbk"][2]*100))
                myAdress=str(myResult[i]["_lifx"]["addr"].replace(":",""))
                myDevice=_inv_mydevices[myAdress]
                myPower=1 if (myResult[i]["power"]) else 0
                UpdateDevice(myDevice, myPower, myLevel)
                Domoticz.Debug("Lifx #" + str(myDevice) + " power " + str(myPower) + " Level " + str(myLevel))
                
            Domoticz.Debug("onHeartbeat called")
            _HBpass=4
        else:
            _HBpass-=1
            Domoticz.Debug("onHeartbeat passed")

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
#    return base64.b64encode(s.encode('utf-8')).decode("utf-8")
    return base64.b64encode(s.encode('utf-8')).decode("utf-8")
\ No newline at end of file
