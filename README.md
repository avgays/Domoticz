# Domoticz
Domoticz python Plugins

## LIFX

The lights daemon documentation: 

http://lightsd.readthedocs.io/en/latest/index.html

Build instructions 

http://lightsd.readthedocs.io/en/latest/installation.html#build-instructions-for-debian-based-systems-ubuntu-raspbian

Enable lightsd at boot: 

>$ sudo systemctl enable lightsd

Enable network interface (not nessesary, only if you installs daemon on other machine):

>$ sudo nano /usr/lib/systemd/system/lightsd.service

add "-l 0.0.0.0:32069" to listen on all interfaces configured with an IPv4 address on your system and on port 32069

>$ sudo systemctl daemon-reload;

>$ sudo systemctl restart lightsd


Check lightsd status:
>$ sudo systemctl status lightsd

>$ sudo systemctl status lightsd

● lightsd.service - LIFX WiFi smart bulbs control service

   Loaded: loaded (/usr/lib/systemd/system/lightsd.service; enabled)
   
   Active: active (running) since Sun 2015-12-06 01:45:48 UTC; 1h 59min ago
   
 Main PID: 19060 (lightsd)
 
   CGroup: /system.slice/lightsd.service
   
           └─19060 lightsd: listening_on([::]:1234, /run/lightsd/socket); command_pipes(/run/lightsd/pipe); lifx_gateways(found=2); bulbs(found=4,...
>$

install python plugin https://github.com/avgays/Domoticz/blob/master/plugins/Lifx/plugin.py in "/domoticz/plugins/Lifx"


