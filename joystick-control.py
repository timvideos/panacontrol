#!/usr/bin/python

import fcntl
import struct
import sys
import termios
import time
import math
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

    #fcntl.ioctl(self.fd, termios.TIOCMBIS, TIOCM_RTS_str)
    control = fcntl.ioctl(fd, termios.TIOCMGET, struct.pack('I', 0))
    print '%04X' % struct.unpack('I',control)[0]
    fcntl.ioctl(fd, termios.TIOCMBIC, struct.pack('I', termios.TIOCM_RTS))
    fcntl.ioctl(fd, termios.TIOCMBIC, struct.pack('I', termios.TIOCM_DTR))
    control = fcntl.ioctl(fd, termios.TIOCMGET, struct.pack('I', 0))
    print '%04X' % struct.unpack('I',control)[0]

  def ReadByte(self):
    return self.tty.read(1)

  def WriteByte(self, byte):
    return self.tty.write(byte)
    pass

def main():
  input_buffer = []

  try:
    tty_name = sys.argv[1]
  except IndexError:
    tty_name = '/dev/ttyS0'

  port = SerialPort(tty_name)

  pygame.init()                                                                   
  pygame.joystick.init()                                                          
  joystick = pygame.joystick.Joystick(0)                                          
  joystick.init() 

  panno = 50 
  tiltno = 50
  zoomno = 50
  focusno = 50
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
        # joystick -1 to 1, camera 0 to 100
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

