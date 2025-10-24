# This file is executed on every boot (including wake-boot from deepsleep)


import network
sta_if = network.WLAN(network.WLAN.IF_STA); sta_if.active(True)
sta_if.scan()                             # Scan for available access points
sta_if.connect("GTI-AP314", "carsled100") # Connect to an AP
sta_if.isconnected()                      # Check for successful connection

import esp
esp.osdebug(None)
import webrepl
webrepl.start()

print("ola")