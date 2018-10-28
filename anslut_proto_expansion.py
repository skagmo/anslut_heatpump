#!/usr/bin/python

# pip install pymeterbus

import serial, time

PREAMBLE = 0
DATA = 1

sizes = {0x9c: 9, 0xb9: 12, 0xae: 20}

class anslut:
	def __init__(self):
		self.state = PREAMBLE
		self.data = []
	def parse(self, c):
		if self.state == PREAMBLE:
			if c in [0x9c, 0xae, 0xb9]:
				self.state = DATA
				self.data = [c]
				self.chksum = c
			else:
				print "got inv %02x" % c
		elif self.state == DATA:
			self.data.append(c)
			if (len(self.data) == sizes[self.data[0]]):
				if (self.chksum == c):
					print "match " + ":".join("%02x" % (c) for c in self.data)

					if (self.data[0] == 0x9c):
						print "Set temp %u" % (self.data[4])
					if (self.data[0] == 0xb9):
						print "Water temp %u" % (self.data[3])
						print "Confirm set %u" % (self.data[10])
				else:
					print "csumerror " + ":".join("%02x" % (c) for c in self.data)
				self.state = PREAMBLE
			self.chksum = (self.chksum + c) % 256
			if (len(self.data) > 20):
				self.state = PREAMBLE
				print "aborted " + ":".join("%02x" % (c) for c in self.data)
			#print "chk %02x data %02x" % (self.chksum, c)			

			
a = anslut()
			

time_old = time.time()
while(1):
	with serial.Serial(
		'/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A50285BI-if00-port0',
		4800,
		timeout=0) as ser:
		while(1):
			x = ser.read(100)
			for c in x:
				a.parse(ord(c))
			time.sleep(0.05)
			if 0: # (time.time()-time_old) > 0.5:
				time_old = time.time()
				print "sending"
				ser.write("\x9c\x00\x80\x02\x22\x07\x23\x00\x6a")

