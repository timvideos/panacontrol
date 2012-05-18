
Library
==============================================================================

Library for controlling Panasonic Pan Tilt Zoom (PTZ) camera's such as the
HE100.

Interface
==============================================================================

Panasonic Camera's use two different formats for sending commands to PTZ camera's. 

The first consists of a "Start Stream" byte (0x02), then a command instruction
then a "End Stream" byte (0x03). We call these "CCP" commands.

The second consists of no start byte, ASCII command instruction followed by a
carriage return. We call these "PT" commands.


Hardware Interface
==============================================================================

The control interface on the AW-HE100 is a RS422 serial port over Cat5 UTP
cable. 

We use a budget RS422<->USB interface and a custom cable. The chip is supported under linux by the XXXX driver and appears as /dev/ttyUSB0 

The wiring is:
<pre>
  Pin | Color    | USB Device 
 ---- | -------- | ----------
  8   | Brown    | -
  7   | W/Brown  | -
  6   | Orange   | TX+
  5   | W/Blue   | RX+
  4   | Blue     | RX-
  3   | W/Orange | TX-
  2   | Green    | -   
  1   | W/Green  | Ground
</pre>

Devices
==============================================================================

The library has been tested with the following cameras:

 * Panasonic AW-HE100
 * ...more to come....

The AW-HE100 camera's has quite a comprehensive list of features including;

 * 1/3-inch interline 3CCD (progressive compatible)
 * Power 13x zoom F1.6-2.8 (
	f=4.2 mm to 55 mm, 35 mm equivalent: 32.5 mm to 423 mm)
 * Auto/Manual switchable focus
 * Multiple HD-SDI output formats such as
    * 1080/59.94i
    * 720/59.94p
    * 480/59.94i,
    * 480/29.97p
 * Pan: over ± 175°, tilt: over +210° to -40°

