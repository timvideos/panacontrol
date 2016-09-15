#!/usr/bin/python

import fcntl
import struct
import sys
import termios
import time
import math
import os

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
    #self.tty = open(self.tty_name, 'rb+', 0)

    #fd = open("/dev/ttyUSB0", O_RDWR | O_NOCTTY | O_NONBLOCK);
    #fcntl(fd, F_SETFL, 0);
    ttyfd = os.open(self.tty_name, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
    fcntl.fcntl(ttyfd, fcntl.F_SETFL, 0)
    self.tty = os.fdopen(ttyfd, 'rb+', 0)

    fd = self.tty.fileno()

    self.old_termios = termios.tcgetattr(fd)
    new_termios = [termios.IGNPAR,                 # iflag
                   0,                              # oflag
                   termios.B115200 | termios.CS8 |
                   termios.CLOCAL | termios.CREAD, # cflag
                   0,                              # lflag
                   termios.B115200,                  # ispeed
                   termios.B115200,                  # ospeed
                   self.old_termios[6]             # special characters
                  ]
    termios.tcsetattr(fd, termios.TCSANOW, new_termios)

    #fcntl.ioctl(self.fd, termios.TIOCMBIS, TIOCM_RTS_str)
    #control = fcntl.ioctl(fd, termios.TIOCMGET, struct.pack('I', 0))
    #print '%04X' % struct.unpack('I',control)[0]
    #fcntl.ioctl(fd, termios.TIOCMBIC, struct.pack('I', termios.TIOCM_RTS))
    #fcntl.ioctl(fd, termios.TIOCMBIC, struct.pack('I', termios.TIOCM_DTR))
    #control = fcntl.ioctl(fd, termios.TIOCMGET, struct.pack('I', 0))
    #print '%04X' % struct.unpack('I',control)[0]

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

  for i in "\r\r\r":
    port.WriteByte(i)

  for s in ["#FRAME 8\r","#OUTPUT 8\r"]: #LIST\r",]: #"#DEVTYPE\r","#DEVERSION\r",'#LIST\r',"#OUTPUT_8\r",]:
    for i in s:
      port.WriteByte(i)
  
    print "Wrote %r\nWaiting for response!" % (s,)
  
    response = False
    while True:
      r = ['']
      while r[-1] != '\r':
        r.append(port.ReadByte())
        #sys.stdout.write(repr(r[-1]))
        #sys.stdout.flush()
      if "".join(r).strip() != "":
        print "Response %r" % ("".join(r),)
        response = True
        break
      else:
        print "Empty"
        if response:
          break


if __name__ == '__main__':
  main()

