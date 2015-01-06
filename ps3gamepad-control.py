#!/usr/bin/python

# Joystick (PS3/Xbox) controller for Panasonic HE100E Camera
# Ryan Verner <ryan.verner@gmail.com>
#
# Allows camera(s) to be controlled with PS3 controller.  Implements:
#
# * Pan (analog sensitive)
# * Tilt (analog sensitive)
# * Zoom (analog sensitive)
# * Focus (digital up/down buttons)
# * O Button to toggle Auto Focus
# * X Button to change sensitivity of pan/tilt (fast, medium, slow)
#
# Will need to pair PS3 controller to PC, or use USB cable (not covered here).
#
# Command line arguments (optional):
#
# python joystick-control.py <device> <joystickdevice>
#  <serial>: serial device camera controller is on, default /dev/ttyUSB0
#  <joystick>: joystick number if multiple, default 0 

import fcntl
import struct
import sys
import termios
import time
import os
import pygame
from numpy import interp

class SerialPort(object):
    def __init__(self, tty_name):
        self.tty_name = tty_name
    self.tty = None
    self.old_termios = None
    self.InitTTY()

    def __del__(self):
        if self.tty and self.old_termios:
            fd = self.tty.fileno()
            termios.tcsetattr(fd, termios.TCSAFLUSH, self.old_termios)

            def InitTTY(self):
                ttyfd = os.open(self.tty_name, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
    fcntl.fcntl(ttyfd, fcntl.F_SETFL, 0)
    self.tty = os.fdopen(ttyfd, 'rb+', 0)

    fd = self.tty.fileno()

    self.old_termios = termios.tcgetattr(fd)
    new_termios = [termios.IGNPAR,                 # iflag
                   0,                              # oflag
                   termios.B9600 | termios.CS8 |
                   termios.CLOCAL | termios.CREAD, # cflag
                   0,                              # lflag
                   termios.B9600,                  # ispeed
                   termios.B9600,                  # ospeed
                   self.old_termios[6]             # special characters
                   ]
    termios.tcsetattr(fd, termios.TCSANOW, new_termios)

    control = fcntl.ioctl(fd, termios.TIOCMGET, struct.pack('I', 0))
    print '%04X' % struct.unpack('I',control)[0]
    fcntl.ioctl(fd, termios.TIOCMBIC, struct.pack('I', termios.TIOCM_RTS))
    fcntl.ioctl(fd, termios.TIOCMBIC, struct.pack('I', termios.TIOCM_DTR))
    control = fcntl.ioctl(fd, termios.TIOCMGET, struct.pack('I', 0))
    print '%04X' % struct.unpack('I',control)[0]

def main():
    input_buffer = []

    try:
        tty_name = sys.argv[1]
    except IndexError:
        tty_name = '/dev/ttyUSB0'

        try:
            joystickno = int(sys.argv[2])
        except IndexError:
            joystickno = 0

            port = SerialPort(tty_name)

            pygame.init()                                                                   
            pygame.joystick.init()                                                          
            joystick = pygame.joystick.Joystick(joystickno)                                          
            joystick.init() 

            panno = 50 
            tiltno = 50
            zoomno = 50
            focusno = 50 # TODO: implement reading current focus, particularly after autofocus enabled
            pantiltscale = 1
            manualfocus = 0

            while True:

                pan = '#P%02d' % panno
                tilt = '#T%02d' % tiltno
                zoom = '#Z%02d' % zoomno
                focus = '#AYF%03d' % focusno
                focustoggle = '#D1%01d' % manualfocus

                for i in (pan, tilt, zoom):
                    port.WriteByte(i)
                    port.WriteByte('\r')

                if manualfocus == 1:
                    port.WriteByte(focus)
                port.WriteByte('\r')

                time.sleep(0.1)
                pygame.event.pump()

                def ConvRange(value, reverse=False, scale=1):
                    if reverse == True:
                        camerarange = [99, 1]
                    else:
                        camerarange = [1, 99]
                        joystickrange = [-1, 1]
                        return interp(value*scale, joystickrange, camerarange)

                panno = ConvRange(joystick.get_axis(0), scale=pantiltscale)
                tiltno = ConvRange(joystick.get_axis(1), reverse=True, scale=0.75*pantiltscale)  
                zoomno = ConvRange(joystick.get_axis(3), reverse=True)

                if joystick.get_button(14):
                    if pantiltscale == 1:
                        pantiltscale = 0.65
                    elif pantiltscale == 0.65:
                        pantiltscale = 0.35
                    elif pantiltscale == 0.35:
                        pantiltscale = 1 
                        while joystick.get_button(14) == 1: 
                            pygame.event.pump()
                            pass

                if joystick.get_button(13):
                    if manualfocus == 1:
                        manualfocus = 0
                    else:
                        manualfocus = 1
                    port.WriteByte(focustoggle)
                    port.WriteByte('\r')
                    while joystick.get_button(13) == 1:
                        pygame.event.pump()
                        pass

                if joystick.get_button(4):
                    if not focusno > 999:
                        focusno = focusno + 10 

                if joystick.get_button(6):
                    if not focusno < 1:
                        focusno = focusno - 10

                print pan, tilt, zoom, focus, manualfocus

if __name__ == '__main__':
    main()

