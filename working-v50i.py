#!/usr/bin/python
# vim: set ts=4 sw=4 et sts=4 ai:

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
    self.tty = os.fdopen(os.open(self.tty_name, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK), 'rb+')
    fd = self.tty.fileno()

    self.old_termios = termios.tcgetattr(fd)
    print "termios.tcgetattr", repr(self.old_termios)
    new_termios = [
    	termios.IGNPAR,                 # iflag
        0,                              # oflag
        termios.B9600 | termios.CS8 |
        termios.CLOCAL | termios.CREAD, # cflag
        0,                              # lflag
        termios.B9600,                  # ispeed
        termios.B9600,                  # ospeed
        self.old_termios[6]             # special characters
        ]
    new_termios[-1][6] = 1 # set VMIN

    termios.tcsetattr(fd, termios.TCSANOW, new_termios)
    print "termios.tcgetattr", termios.tcgetattr(fd)

    control = fcntl.ioctl(fd, termios.TIOCMGET, struct.pack('I', 0))
    fcntl.ioctl(fd, termios.TIOCMBIC, struct.pack('I', termios.TIOCM_RTS))
    fcntl.ioctl(fd, termios.TIOCMBIC, struct.pack('I', termios.TIOCM_DTR))
    control = fcntl.ioctl(fd, termios.TIOCMGET, struct.pack('I', 0))

    nf = fcntl.fcntl(fd, fcntl.F_GETFL)
    print "fnctl.F_GETFL", repr(nf)
    fcntl.fcntl(fd, fcntl.F_SETFL, nf & ~os.O_NONBLOCK )

  def ReadByte(self):
    return self.tty.read(1)

  def WriteByte(self, byte):
    return self.tty.write(byte)

def assert_bytes(port, s):
  b = ''
  for i, c in enumerate(s):
     b += port.ReadByte()
     assert b[-1] == c, "%s[%i] != %s[-1]" % (list(s), i, list(b))
     print 'Reading:', repr(b[-1])

def write_bytes(port, s):
  for i in s:
    print "Writing:", repr(i)
    port.WriteByte(i)


def main():
  input_buffer = []

  try:
    tty_name = sys.argv[1]
  except IndexError:
    tty_name = '/dev/ttyUSB0'

  print "Opening serial port", tty_name
  port = SerialPort(tty_name)
  print "Start writing"

  print "Probe device chain"
  write_bytes(port, '\xff00\x00\x8f0\xef')
  assert_bytes(port, '\xfe0000\xef')
  write_bytes(port, '\xff00\x00\x8f1\xef')
  assert_bytes(port, '\xfe0100\xef')

  print "Turn off command finish notification"
  write_bytes(port, '\xff01\x00\x940\xef')
  assert_bytes(port, '\xfe0100\xef')

  print "Camera off"
  write_bytes(port, '\xff01\x00\xa00\xef')
  assert_bytes(port, '\xfe0100\xef')
  #assert_bytes(port, '\xfa01\x00\xa00\xef')

  print "Sleeping"
  time.sleep(1)

  print "Camera on"
  write_bytes(port, '\xff01\x00\xa01\xef')
  assert_bytes(port, '\xfe0100\xef')
  #assert_bytes(port, '\xfa01\x00\xa01\xef')

  print "Camera Reset"
  write_bytes(port, '\xff01\x00\xaa\xef')
  assert_bytes(port, '\xfe0100\xef')
  #assert_bytes(port, '\xfa01\x00\xaa\xef')

  print "Turn on command finish notification"
  write_bytes(port, '\xff01\x00\x941\xef')
  assert_bytes(port, '\xfe0100\xef')

  print "Get device info"
  write_bytes(port, '\xff01\x00\x87\xef')
  assert_bytes(port, '\xfe0100C50i \xef')

  print "Center"
  write_bytes(port, '\xff01\x00\x580\xef')
  assert_bytes(port, '\xfe0100\xef')
  assert_bytes(port, '\xfa01\x00\x580\xef')

  print "Set pan speed"
  write_bytes(port, '\xff01\x00\x50150\xef')
  assert_bytes(port, '\xfe0100\xef')

  print "Pan left"
  write_bytes(port, '\xff01\x00\x6020\xef')
  assert_bytes(port, '\xfe0100\xef')

  print "Sleeping"
  time.sleep(1.0)

  print "Pan left stop"
  write_bytes(port, '\xff01\x00\x530\xef')
  assert_bytes(port, '\xfe0100\xef')

  print "Pan right till can't any more"
  write_bytes(port, '\xff01\x00\x6010\xef')

  while True:
    b = port.ReadByte()
    assert len(b) == 1
    print "Reading:", repr(b)
  return



if __name__ == '__main__':
  main()

