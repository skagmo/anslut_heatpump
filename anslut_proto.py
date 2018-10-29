# Class for communicating with Anslut heat pump
# skagmo.com, 2018

import serial, time

PREAMBLE = 0
DATA = 1

PREAMBLE_BYTE = 0x39

# Used in request
OPMODE_bm = 0xfe
ENABLED_bm = 0x01
OPMODES = {0x10: 'cool', 0x20: 'heat', 0x24: 'heat_water'}
OPMODE_COOL = 0x10
OPMODE_HEAT = 0x20
OPMODE_HEAT_WATER = 0x24
OPMODE_AND_EN_REV = {'off': 0x20, 'cool': 0x11, 'heat': 0x21, 'heat_water': 0x25}
SEND_INTERVAL = 2
# Room temperature needs to be set more often than every 10 minutes
# If not, water temperature will be used
TEMP_TIMEOUT = 600 

# Used in response
PUMP_STATES = {0x00: 'idle', 0x01: 'active', 0x03: 'defrost'}

def flip(c):
	return int('{:08b}'.format(c)[::-1], 2)

class anslut:
	def __init__(self, port):
		self.port = port
		self.state = PREAMBLE
		self.data = []
		self.send_ts = time.time()
		self.callback = False

		self.req_opmode_and_en = OPMODE_HEAT|ENABLED_bm
		self.req_roomtemp = 25
		self.req_setpoint = 31
		self.watertemp = 25
		self.roomtemp_timestamp = 0
		self.open_serial()

	def open_serial(self):
		self.ser = serial.Serial(
			self.port,
			100, 
			stopbits=serial.STOPBITS_ONE,
			timeout=0,
			parity=serial.PARITY_ODD)
		
	def set_callback(self, function):
		self.callback = function

	def checksum(self, d):
		# Calculate checksum
		ck = 0
		for i in d[1:5]:
			ck = (ck + i) % 0xff
		ck = 0x100 - ck
		return ck

	def send_request(self, enabled, opmode, temp, set_temp):
		buf = [PREAMBLE_BYTE, (opmode|int(enabled)), temp, set_temp, 0]
		buf.append(self.checksum(buf))
		self.handle_request(buf)
		string = ""
		for i in range(0, len(buf)):
			string += chr(flip(buf[i]))
		self.ser.write(string)

	def handle_request(self, pkt):
		opmode = pkt[1] & OPMODE_bm
		enabled = pkt[1] & ENABLED_bm
		#print "request " + ":".join("%02x" % (c) for c in pkt)

		if not (self.checksum(pkt) == pkt[-1]):
			print ("Request: Checksum error")
		if (opmode in OPMODES):
			if enabled:
				opmode_string = OPMODES[opmode]
			else:
				opmode_string = "off"
			
			self.callback("opmode=%s roomtemp=%u setpoint=%u\n" %
				(opmode_string, pkt[2], pkt[3]))
		else:
			print ("Request: Invalid packet")

	def handle_response(self, pkt):
		if pkt[1] in PUMP_STATES:
			pump_state = PUMP_STATES[pkt[1]]
		else:
			pump_state = "%02x" % pkt[1]

		# Value 85 is maximum power, scale to percent
		power = int(round(pkt[3]*100.0/85.0))

		# Store watertemp for sending back as roomtemp in case of timeout
		self.watertemp = pkt[2]

		self.callback("state=%s watertemp=%u power=%u unknown=%02x\n" %
			(pump_state, pkt[2], power, pkt[4]))

	def tick(self):
		# Attempt to parse incoming data
		try:
			while (self.ser.inWaiting()):
				self.parse(ord(self.ser.read(1)))
		except IOError:
			print("Serial port error, fixing")
			try:
				self.ser.close()
				time.sleep(5)
				self.open_serial()
			except serial.serialutil.SerialException:
				print("Failed")

		# Send request packet regularly
		ts = time.time()
		if (ts - self.send_ts) > SEND_INTERVAL:
			self.send_ts = ts

			# Use water temperature as room temperature if timeout
			if (ts-self.roomtemp_timestamp) > TEMP_TIMEOUT:
				self.req_roomtemp = self.watertemp
				
			self.send_request(
				self.req_opmode_and_en & ENABLED_bm,
				self.req_opmode_and_en & OPMODE_bm,
				self.req_roomtemp,
				self.req_setpoint)

	def parse(self, c):
		c = flip(c)

		if self.state == PREAMBLE:
			if c == PREAMBLE_BYTE:
				self.state = DATA
				self.data = [c]

		elif self.state == DATA:
			self.data.append(c)
			if (len(self.data) == 6):
				self.state = PREAMBLE
				if (self.checksum(self.data) == self.data[-1]):
					#self.handle_request(self.data)
					self.handle_response(self.data)
				else:
					print "Checksum failed"

			if (len(self.data) > 20):
				self.state = PREAMBLE		
				print "Invalid packet"

	def set_opmode(self, mode):
		if mode in OPMODE_AND_EN_REV:
			self.req_opmode_and_en = OPMODE_AND_EN_REV[mode]
	
	def set_roomtemp(self, temp):
		self.req_roomtemp = temp
		self.roomtemp_timestamp = time.time()

	def set_setpoint(self, temp):
		self.req_setpoint = temp

	# Text command
	def parse_cmd(self, s):
		try:
			[cmd, value] = s.split('=')
			if (cmd == "opmode"):
				self.set_opmode(value)
			elif (cmd == "roomtemp"):
				self.set_roomtemp(int(value))
			elif (cmd == "setpoint"):
				self.set_setpoint(int(value))
			elif (cmd == "watertemp_target"):
				self.use_watertemp_as_roomtemp(int(value))
		except ValueError:
			print "Wrong number of arguments"
