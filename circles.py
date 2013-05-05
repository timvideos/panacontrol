#!/usr/bin/python

import fcntl
import struct
import sys
import termios
import time
import math

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
    self.tty = open(self.tty_name, 'rb+', 0)
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


class CameraProtocol(object):
  STX = '\x02'
  ETX = '\x03'
  ACK = '\x06'
  CR = '\r'

  def DisplayCameraCommand(self, input_buffer):
    assert input_buffer[0] == self.STX
    assert input_buffer[-1] == self.ETX

    if input_buffer[1] == 'O':
      if ':' in input_buffer:
        print 'Camera Operation: %s' % (input_buffer[1:-1],)
      else:
        print 'Camera Operation (no data): %s' % (input_buffer[1:-1],)
    elif input_buffer[1:5] == ['X', 'S', 'F', ':']:
      print 'Camera Scene Selection: %s' % (input_buffer[1:-1],)
    elif input_buffer[1] == 'D':
      print 'Camera Monitoring: %s' % (input_buffer[1:-1],)
    elif input_buffer[1:5] == ['O', 'S', 'D', ':']:
      print 'Camera Menus: %s' % (input_buffer[1:-1],)
    elif input_buffer[1] == 'Q':
      print 'Camera Question: %s' % (input_buffer[1:-1],)
    elif input_buffer[1] == 'H':
      print 'Camera Contact Command: %s' % (input_buffer[1:-1],)
    else:
      print 'Unknown Camera Command: %s' % (input_buffer[1:-1],)

    return []

  def DisplayPTCommand(self, input_buffer):
    assert input_buffer[0] == '#'
    assert input_buffer[-1] == self.CR

    if input_buffer[1] == 'O':
      print 'PT Power: %s' % (input_buffer[1:-1],)
    elif input_buffer[1] == 'P':
      print 'PT Pan Speed: %s' % (input_buffer[1:-1],)
    elif input_buffer[1] == 'T':
      print 'PT Tilt Speed: %s' % (input_buffer[1:-1],)
    elif input_buffer[1] == 'U':
      print 'PT Pan Tilt Position Control: %s' % (input_buffer[1:-1],)
    elif input_buffer[1] == 'Z':
      print 'PT Zoom Control: %s' % (input_buffer[1:-1],)
    elif input_buffer[1:4] == ['A', 'X', 'Z']:
      print 'PT Zoom Position Control: %s' % (input_buffer[1:-1],)
    elif input_buffer[1:4] == ['A', 'Y', 'Z']:
      print 'PT Zoom Position Control: %s' % (input_buffer[1:-1],)
    elif input_buffer[1] == 'F':
      print 'PT Focus Speed Control: %s' % (input_buffer[1:-1],)
    elif input_buffer[1:4] == ['A', 'X', 'F']:
      print 'PT Focus Position Control: %s' % (input_buffer[1:-1],)
    elif input_buffer[1:4] == ['A', 'Y', 'F']:
      print 'PT Focus Position Control: %s' % (input_buffer[1:-1],)
    elif input_buffer[1:3] == ['R', 'O']:
      print 'PT Roll Speed Control: %s' % (input_buffer[1:-1],)
    elif input_buffer[1] == 'I':
      print 'PT Iris Speed Control: %s' % (input_buffer[1:-1],)
    elif input_buffer[1:4] == ['A', 'X', 'I']:
      print 'PT Iris Position Control: %s' % (input_buffer[1:-1],)
    elif input_buffer[1:4] == ['A', 'Y', 'I']:
      print 'PT Iris Position Control: %s' % (input_buffer[1:-1],)
    else:
      print 'Unknown Pan/Tile Command: %s' % (input_buffer[1:-1],)

    return []

  def DisplayCommands(self, input_buffer):
    frame_start = 0
    while input_buffer:
      if input_buffer[0] == self.ACK:
        input_buffer.pop(0)
        print 'ACK'
        continue
      if input_buffer[0] == self.STX:
        if input_buffer[-1] == self.ETX:
          input_buffer = self.DisplayCameraCommand(input_buffer)
        break
      if input_buffer[0] == '#':
        if input_buffer[-1] == self.CR:
          input_buffer = self.DisplayPTCommand(input_buffer)
        break

      discard = input_buffer.pop(0)
      print 'Discarding input byte 0x%02X %s' % (struct.unpack('B', discard)[0],
                                                 discard)

    return input_buffer


def main():
  input_buffer = []

  try:
    tty_name = sys.argv[1]
  except IndexError:
    tty_name = '/dev/ttyS0'

  port = SerialPort(tty_name)

  granularity = 500
  prev_dx = 0
  prev_dy = 0
  try:
    for loop in range(4):
      for rad in range(granularity):
        try:
          dx = math.sin((math.pi * 2) / (float(rad) / float(granularity)))
        except ZeroDivisionError:
          dx = prev_dx
        try:
          dy = math.cos((math.pi * 2) / (float(rad) / float(granularity)))
        except ZeroDivisionError:
          dy = prev_dy
        prev_dx = dx
        prev_dy = dy
        scaled_dx = 50 + (50 * dx)
        scaled_dy = 50 + (50 * dy)
        pan = '#P%02d' % scaled_dx
        tilt = '#T%02d' % scaled_dy
        print '%s %s' % (pan, tilt)
        for i in (pan):
          port.WriteByte(i)
        port.WriteByte('\r')
        for i in (tilt):
          port.WriteByte(i)
        port.WriteByte('\r')

        time.sleep(0.1)
  except KeyboardInterrupt:
    pass

  pan = '#P%02d' % 50
  tilt = '#T%02d' % 50
  for i in (pan):
    port.WriteByte(i)
  port.WriteByte('\r')
  for i in (tilt):
    port.WriteByte(i)
  port.WriteByte('\r')


if __name__ == '__main__':
  main()

