#!/usr/bin/python

import re


class CameraFrame(object):
  STX = ''
  ETX = ''

  _PCT_C_RE = re.compile(r'%(\d*)c')
  _PCT_D_RE = re.compile(r'%(\d*)d')
  _PCT_S_RE = re.compile(r'%s')

  def __init__(self, desc, confirm_format, control_format, reply_format,
               checksum=False):
    self.desc = desc
    self.confirm_format = confirm_format
    self.control_format = control_format
    self.reply_format = reply_format
    self.checksum = checksum
    self.confirm_re = self._FormatToRE(confirm_format, checksum)
    self.control_re = self._FormatToRE(control_format, checksum)
    self.reply_re = self._FormatToRE(reply_format, checksum)

  def _Checksum(self, cmd):
    cksum = sum([ord(x) for x in cmd]) % 0x100
    if cksum == 0:
      cksum = 1
    if cksum == 0x0D:
      cksum = 0x0E
    return cksum

  def EncodeConfirmation(self, args):
    cmd = self.confirm_format % args
    if self.checksum:
      cksum = self._Checksum(cmd)
      cksum = ('%02X' % cksum).decode('hex')
      cmd = cmd + cksum
    return self.STX + cmd + self.ETX

  def EncodeControl(self, args):
    cmd = self.control_format % args
    if self.checksum:
      cksum = self._Checksum(cmd)
      cksum = ('%02X' % cksum).decode('hex')
      cmd = cmd + cksum
    return self.STX + cmd + self.ETX

  def DecodeReply(self, cmd):
    """Attempt to decode cmd and return values, failure raises ValueError."""
    if self.STX:
      if cmd[0] != self.STX:
        raise ValueError('Incorrect framing')
      cmd = cmd[1:]
    if self.ETX:
      if cmd[-1] != self.ETX:
        raise ValueError('Incorrect framing')
      cmd = cmd[:-1]

    result = self.reply_re.match(cmd)
    if result is None:
      raise ValueError('No match')

    # Replies don't have checksums.
    #if self.checksum:
    #  cksum = self._Checksum(cmd[:-1])
    #  if cksum != ord(cmd[-1]):
    #    raise ValueError('Checksum mismatch (%02X/%02X)' %
    #                     (cksum, ord(cmd[-1])))

    return result

  def _FormatToRE(self, fmt, checksum):
    """Convert a printf style format string into a regular expression."""
    if not fmt:
      return

    if checksum:
      fmt = fmt + '%c'

    def percent_c_repl(match):
      count = match.group(1)
      if count:
        return r'(.{%s})' % count
      return r'(.)'
    fmt = self._PCT_C_RE.sub(percent_c_repl, fmt)

    def percent_d_repl(match):
      count = match.group(1)
      if count:
        return r'(\d{%s})' % count.lstrip('0')
      return r'(\d)'
    fmt = self._PCT_D_RE.sub(percent_d_repl, fmt)

    def percent_s_repl(match):
      return r'(.*)'
    fmt = self._PCT_S_RE.sub(percent_s_repl, fmt)

    return re.compile(fmt)


class CCP(CameraFrame):
  STX = '\x02'
  ETX = '\x03'


class PT(CameraFrame):
  STX=''
  ETX='\r'


class HE100(object):
  commands = (CCP('model number', 'QID', None, 'OID:%2c'),
              CCP('software version', 'QSV', None, 'OSV:%s'), # Unsure of rlen
              CCP('AWC/AWB', None, 'OWS', 'OWS'),
              CCP('ABC/ABB', None, 'OAS', 'OAS'),
              CCP('AWC mode', 'QAW', 'OAW:%c', 'OAW:%c'),
              CCP('detail', 'QDT', 'ODT:%c', 'ODT:%c'),
              CCP('gain up', 'QGU', 'OGU:%c', 'OGU:%c'),
              CCP('shutter', 'QSH', 'OSH:%c', 'OSH:%c'),
              CCP('synchro scan', 'QMS', 'OMS:%3c', 'OMS:%3c'), # Unsure of fmt
              CCP('field/frame', 'QFF', None, 'OFF:%c'),
              CCP('v.resolution', None, 'OFR:%c', 'OFR:%c'),
              CCP('iris auto/manual', 'QRS', 'ORS:%c', 'ORS:%c'),
              CCP('manual iris volume', 'QRV', 'ORV:%3c', 'ORV:%3c'), # fmt?
              CCP('picture level', 'QSD:48', 'OSD:48:%2c', 'OSD:48:%2c'), # fmt?
              CCP('light peak/avg', 'QPA', None, 'OPA:%2c'), # fmt?
              CCP('light peak/avg', None, 'OPV:%2c', 'OPV:%2c'), # fmt?
              CCP('light area', 'QAR', None, 'OAR:%c'),
              CCP('light area', None, 'ORA:%c', 'ORA:%c'),
              CCP('nega/posi', 'QNP', 'ONP:%c', 'ONP:%c'),
              CCP('r pedestal', 'QRD', 'ORD:%2c', 'ORD:%2c'), # fmt?
              CCP('b pedestal', 'QBD', 'OBD:%2c', 'OBD:%2c'), # fmt?
              CCP('r gain', 'QGR', 'OGR:%2c', 'OGR:%2c'), # typo? fmt?
              CCP('b gain', 'QGB', 'OGB:%2c', 'OGB:%2c'), # typo? fmt?
              CCP('t pedestal', 'QTD', 'OTD:%2c', 'OTD:%2c'), # fmt?
              CCP('h phase', 'QHP', 'OHP:%3c', 'OHP:%3c'), # fmt?
              CCP('sc coarse', 'QSC', 'OSC:%c', 'OSC:%c'),
              CCP('sc fine', 'QSN', 'OSN:%3c', 'OSN:%3c'), # fmt?
              CCP('chroma level', 'QCG', 'OCG:%2c', 'OCG:%2c'),
              CCP('scene file', 'QSF', 'OSF:%c', 'OSF:%c'),
              CCP('scene file', None, 'XSF:%c', 'XSF:%c'),
              CCP('gamma', 'QSD:00', 'OSD:00:%2c', 'OSD:00:%2c'), # fmt?...
              CCP('knee point', 'QSD:08', 'OSD:08:%2c', 'OSD:08:%2c'),
              CCP('white clip', 'QSD:09', 'OSD:09:%2c', 'OSD:09:%2c'),
              CCP('h.dtl level h', 'QSD:0A', 'OSD:0A:%2c', 'OSD:0A:%2c'),
              CCP('v.dtl level h', 'QSD:0E', 'OSD:0E:%2c', 'OSD:0E:%2c'),
              CCP('h.dtl level l', 'QSD:12', 'OSD:12:%2c', 'OSD:12:%2c'),
              CCP('v.dtl level l', 'QSD:16', 'OSD:16:%2c', 'OSD:16:%2c'),
              CCP('detail band', 'QSD:1E', 'OSD:1E:%2c', 'OSD:1E:%2c'),
              CCP('noise suppress', 'QSD:22', 'OSD:22:%2c', 'OSD:22:%2c'),
              CCP('level dependent', 'QSD:26', 'OSD:26:%2c', 'OSD:26:%2c'),
              CCP('chroma detail', 'QSD:2A', 'OSD:2A:%2c', 'OSD:2A:%2c'),
              CCP('dark detail', 'QSD:2E', 'OSD:2E:%2c', 'OSD:2E:%2c'),
              CCP('matrix r-g', 'QSD:2F', 'OSD:2F:%2c', 'OSD:2F:%2c'),
              CCP('matrix r-b', 'QSD:30', 'OSD:30:%2c', 'OSD:30:%2c'),
              CCP('matrix g-r', 'QSD:31', 'OSD:31:%2c', 'OSD:31:%2c'),
              CCP('matrix g-b', 'QSD:32', 'OSD:32:%2c', 'OSD:32:%2c'),
              CCP('matrix b-r', 'QSD:33', 'OSD:33:%2c', 'OSD:33:%2c'),
              CCP('matrix b-g', 'QSD:34', 'OSD:34:%2c', 'OSD:34:%2c'),
              CCP('flare r', 'QSD:35', 'OSD:35:%2c', 'OSD:35:%2c'),
              CCP('flare g', 'QSD:36', 'OSD:36:%2c', 'OSD:36:%2c'),
              CCP('flare b', 'QSD:37', 'OSD:37:%2c', 'OSD:37:%2c'),
              CCP('flare sw', 'QSA:11', 'OSA:11:%2c', 'OSA:11:%2c'),
              CCP('clean dnr', 'QSD:3A', 'OSD:3A:%2c', 'OSD:3A:%2c'),
              CCP('2d lpf', 'QSD:3F', 'OSD:3F:%2c', 'OSD:3F:%2c'),
              CCP('corner detail', 'QSD:43', 'OSD:43:%2c', 'OSD:43:%2c'),
              CCP('precision detail', 'QSD:44', 'OSD:44:%2c', 'OSD:44:%2c'),
              CCP('black stretch', 'QSD:46', 'OSD:46:%2c', 'OSD:46:%2c'),
              CCP('high light chroma', 'QSD:49', 'OSD:49:%2c', 'OSD:49:%2c'),
              CCP('flesh detail', 'QSD:4B', 'OSD:4B:%2c', 'OSD:4B:%2c'),
              CCP('iris follow', 'QSD:4F', None, 'OSD:4F:%2c'),
              CCP('contrast/gamma', 'QSD:50', 'OSD:50:%2c', 'OSD:50:%2c'),
              CCP('flesh tone', 'QSD:52', 'OSD:52:%2c', 'OSD:52:%2c'),
              CCP('detail select', 'QSD:54', 'OSD:54:%2c', 'OSD:54:%2c'),
              CCP('noise suppress', 'QSD:55', 'OSD:55:%2c', 'OSD:55:%2c'),
              CCP('flesh noise suppress', 'QSD:56', 'OSD:56:%2c', 'OSD:56:%2c'),
              CCP('zebra indicator', 'QSD:60', 'OSD:60:%2c', 'OSD:60:%2c'),
              CCP('zebra 1 level', 'QSD:61', 'OSD:61:%2c', 'OSD:61:%2c'),
              CCP('zebra 2 level', 'QSD:62', 'OSD:62:%2c', 'OSD:62:%2c'),
              CCP('safety zone', 'QSD:63', 'OSD:63:%2c', 'OSD:63:%2c'),
              CCP('evf output', 'QSD:64', 'OSD:64:%2c', 'OSD:64:%2c'),
              CCP('output select', 'QSD:65', 'OSD:65:%2c', 'OSD:65:%2c'),
              CCP('charge time', 'QSD:68', 'OSD:68:%2c', 'OSD:68:%2c'),
              CCP('agc max', 'QSD:69', 'OSD:69:%2c', 'OSD:69:%2c'),
              CCP('aspect ratio', 'QSD:70', 'OSD:70:%2c', 'OSD:70:%2c'),
              CCP('fan', 'QSD:71', 'OSD:71:%2c', 'OSD:71:%2c'),
              CCP('atw speed', 'QSD:72', 'OSD:72:%2c', 'OSD:72:%2c'),
              CCP('error 3', None, None, 'ER3:%3c'),
              # More CCP to follow...

              # Many of the following confirm patterns are guesses.
              PT('power', '#O', '#O%c', 'p%c'),
              PT('pan speed', '#P', '#P%2c', None),
              PT('tilt speed', '#T', '#T%2c', None),
              PT('pan/tilt position', '#U', '#U%4c%4c', 'u%4c%4c',
                 checksum=True),
              PT('zoom speed', '#Z', '#Z%2c', None),
              PT('zoom position x', '#AXZ', '#AXZ%3c', 'axz%3c'),
              PT('zoom position y', '#AYZ', '#AYZ%4c%4c', 'ayz%3c',
                 checksum=True),
              PT('focus speed', '#F', '#F%2c', None),
              PT('focus position x', '#AXF', '#AXF%3c', 'axf%3c'),
              PT('focus position y', '#AYF', '#AYF%3c', 'ayf%3c'),
              PT('roll speed', '#RO', '#RO%2c', None),
              PT('iris', '#I', '#I%2c', None),
              PT('iris x', '#AXI', '#AXI%3c', 'axi%3c'),
              PT('iris y', '#AYI', '#AYI%3c', 'ayi%3c'), # typo?
              PT('extender/af', '#D1', '#D1%c', 'd1%c'),
              PT('nd', '#D2', '#D2%c', 'd2%c'),
              PT('iris auto/manual', '#D3', '#D3%c', 'd3%c'),
              PT('lamp control', '#D4', '#D4%c', 'd4%c'),
              PT('lamp alarm', '#D5', None, 'd5%c'),
              PT('option sw', '#D6', '#D6%c', 'd6%c'),
              PT('defroster', '#D7', '#D7%c', 'd7%c'),
              PT('wiper', '#D8', '#D8%c', 'd8%c'),
              PT('heater/fan', '#D9', '#D9%c', 'd9%c'),
              PT('tally', '#DA', '#DA%c', 'dA%c'),
              PT('save preset memory', '#S', '#M%2c', 's%2c'),
              PT('recall preset memory', None, '#R%2c', 's%2c'),
              PT('preset complete notification', None, None, 'q%2c'),
              PT('preset mode', None, '#RT%c', 'rt%c'),
              PT('limit', None, '#L%c', 'l%c'),
              PT('landing', None, '#N%c', None),
              PT('request zoom position', '#GZ', None, 'gz%3c'),
              PT('request focus position', '#GF', None, 'gf%3c'),
              PT('request iris position', '#GI', None, 'gi%3c%c'),
              PT('tilt range', None, '#AGL%c', 'aGL%c'),
              PT('software version', '#V?', None, '%s'),
             )


def main():
  he100 = HE100()


if __name__ == '__main__':
  main()
