# Domoticz Lifx Plugin
# Uses lightsd, a daemon to control smart bulbs by lopter: https://github.com/lopter/lightsd/
#
"""
<plugin key="Lifx2" name="Lifx Plugin 2" author="avgays" version="2.0" wikilink="http://www.domoticz.com/wiki/plugins/plugin.html" externallink="https://www.lifx.com/">
    <params>
        <param field="Address" label="IP Address" width="200px" required="true" default="127.0.0.1"/>
        <param field="Port" label="Port" width="50px" required="true" default="32069"/>
        <param field="Mode3" label="Unix Socket" width="200px" required="true" default="/run/lightsd/socket"/>
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
import math

READ_SIZE = 4096
ENCODING = "utf-8"
devtypes={"Original 1000":(241,4,7),"White 800":(241,3,7),"LIFX Z":(241,4,7),"Color 1000":(241,4,7),"Unknown":(241,4,7)}

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
                Domoticz.Debug("LIFX: " + str(myResult[i]["hsbk"]))
                myName = "Lamp"
                myPower=1
                myLevel=100
                myModel = myResult[i]["_model"]
                myType = devtypes[myModel][0] #myType=244
                mySType=devtypes[myModel][1] #mySType=73
                mySwitchtype=devtypes[myModel][2] #7
                myPower=10 if (myResult[i]["power"]) else 0
                myLevel=str(int(myResult[i]["hsbk"][2]*100))
                MACADDR=str(myResult[i]["_lifx"]["addr"].replace(":",""))
                myName = str(myResult[i]["label"])
                #myName = str(myResult[i]["_model"])
                try:
                    Unit=int(self.inv_mydevices[MACADDR])
                    UpdateDevice(Unit, myPower, myLevel)
                    Domoticz.Debug("Devices exist. " + str(Unit))
                except Exception:
                    k+=1
                    Domoticz.Device(Name=myName,  Unit=(k), Type=myType, Subtype=mySType, Switchtype=mySwitchtype).Create()
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

    def onCommand(self, Unit, Command, Level, Color):
        MACADDR=self.mydevices[str(Unit)]
        Domoticz.Debug("onCommand called for Lifx #" + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level) + ", Color: " + str(Color))
        if (Command == 'On'):
            setLIFX("power_on", [MACADDR])
            UpdateDevice(Unit, 10, Devices[Unit].sValue)
        elif (Command == 'Off'):
            setLIFX("power_off", [MACADDR])
            UpdateDevice(Unit, 0, Devices[Unit].sValue)
        elif (Command == 'Set Level'):
            myResult = queryLIFX(Params=MACADDR)
            h, s, b, k = myResult[0]["hsbk"]
            b=Level/100
            setLIFX("set_light_from_hsbk", [MACADDR, h,s,b,k,0])
            UpdateDevice(Unit, 15, str(Level))
        elif (Command == 'Set Color'):
            myResult = queryLIFX(Params=MACADDR)
            h, s, b, k = myResult[0]["hsbk"]
            ColorJ=json.loads(Color)
            Domoticz.Debug("Get Color HSB Lifx #" + str(Unit) + ">>"  + str(h) + ":"+ str(s) + ":"+ str(b)+ ":"+ str(k))
            red=ColorJ["r"]/255
            green=ColorJ["g"]/255
            blue=ColorJ["b"]/255
            mmode=ColorJ["m"]
            t=ColorJ["t"]
            v=0
            if (mmode==2): # set temp
                h=0
                s=0
                v=Level/100
                k=translate(t,255,0,2500,9000)
            elif (mmode==3): # set color
                h, s, v = rgb_to_hsv(red, green, blue)
            setLIFX("set_light_from_hsbk", [MACADDR, h,s,b,k,0])
            UpdateDevice2(Unit, 15, str(Level), str(Color))          
            Domoticz.Debug("Set Color RGB Lifx #" + str(Unit) + ">>" + str(red) + ":"+ str(green) + ":"+ str(blue) + " mode:" + str(mmode)+ " temp:" + str(t))
            Domoticz.Debug("Set Color HSB Lifx #" + str(Unit) + ">>"  + str(h) + ":"+ str(s) + ":"+ str(v) + ":"+ str(k))
    def onNotification(self, Data):
        Domoticz.Debug("onNotification: " + str(Data))

    def onDisconnect(self):
        Domoticz.Debug("onDisconnect called")

    def onHeartbeat(self):
        if(self.HBpass==0):
            myResult = queryLIFX()
            ColorStr='';
            for i in range(len(myResult)):
                MACADDR=str(myResult[i]["_lifx"]["addr"].replace(":",""))
                myPower=10 if (myResult[i]["power"]) else 0
                h, s, b, k = myResult[i]["hsbk"]
                myLevel=str(int(b*100))
                if (s==0):
                    t = translate(k,2500,9000,255,0)
                    ColorStr='{"m":2,"r":0,"g":0,"b":0,"t":'+ str(t) +',"ww":0,"cw":0}'
                else:
                    red, green, blue = hsv_to_rgb(h, s, 1)
                    ColorStr='{"m":3,"r":' + str(red) + ',"g":' + str(green) + ',"b":' + str(blue) + ',"t":0,"cw":0,"ww":0}'
                try:
                    myDevice=int(self.inv_mydevices[MACADDR])
                    UpdateDevice2(myDevice, myPower, myLevel, ColorStr)
                    Domoticz.Debug(">>Lifx #" + str(myDevice) + " ColorStr " + ColorStr)
                    Domoticz.Debug(">>Lifx #" + str(myDevice) + " power " + str(myPower) + " Level " + str(myLevel))
                    Domoticz.Debug(">>Lifx #" + str(myDevice) + " hsbk " + str(myResult[i]["hsbk"]))
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

def UpdateDevice2(Unit, nValue, sValue, Color):
    # Make sure that the Domoticz device still exists (they can be deleted) before updating it 
    if (Unit in Devices):
        Domoticz.Debug (">>>>>>>>>>Color: " + "' ("+Devices[Unit].Name+") " + Devices[Unit].Color)
        if (Devices[Unit].nValue != nValue) or (Devices[Unit].sValue != sValue):
            Devices[Unit].Update(nValue=nValue, sValue=str(sValue), Color=Color)
            Domoticz.Debug("LIFX Update "+str(nValue)+":'"+str(sValue)+"' ("+Devices[Unit].Name+")" + " Color " + Color)
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
    Domoticz.Debug("request: " + str(request))
    _plugin.lightsd_socket.sendall(request) 
    return

def rgb_to_hsv(r, g, b):
    r = float(r)
    g = float(g)
    b = float(b)
    high = max(r, g, b)
    low = min(r, g, b)
    h, s, v = high, high, high
    d = high - low
    s = 0 if high == 0 else d/high
    if high == low:
        h = 0.0
    else:
        h = {r: (g - b) / d + (6 if g < b else 0), g: (b - r) / d + 2, b: (r - g) / d + 4,}[high]
        h /= 6
    h = int (h*360)
    return h, s, v

def hsv_to_rgb(h, s, v):
    h /= 360
    i = math.floor(h*6)
    f = h*6 - i
    p = v * (1-s)
    q = v * (1-f*s)
    t = v * (1-(1-f)*s)
    r, g, b = [(v, t, p),(q, v, p),(p, v, t),(p, q, v),(t, p, v),(v, p, q),][int(i%6)]
    r *=255
    g *=255
    b *=255
    return int(r), int(g), int(b)

def translate(value, leftMin, leftMax, rightMin, rightMax):
    leftSpan = leftMax - leftMin
    rightSpan = rightMax - rightMin
    valueScaled = float(value - leftMin) / float(leftSpan)
    return int(rightMin + (valueScaled * rightSpan))