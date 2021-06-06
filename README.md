# hm305_ctrl

Python scripts for controlling electronics test equipment.

They have been tested with Ubuntu and MacOS but they should work on any platform
with pySerial.

[hm305.py](hm305.py) controls eTommens eTM-xxxxP series of power supplies, in this case the HM305P from Hanmatek.  These supplies are USB controllable, but they just show as an CH341 serial port.  The protocol is described by http://nightflyerfireworks.com/home/fun-with-cheap-programable-power-supplies
