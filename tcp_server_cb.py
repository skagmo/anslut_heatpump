import socket, select, Queue

class tcp_server:
	def __init__(self, host, port):
		self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.server.setblocking(0)
		self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.server.bind((host, port))
		self.server.listen(10)

		self.receivers = [ self.server ]
		self.transmitters = []
		self.tx_queues = {}
		self.received_packets = []

		self.cmd_buf = ""
		self.callback = False

	def set_callback(self, function):
		self.callback = function

	def close(self):
		self.server.close()

	def __del__(self):
		self.close()

	def remove_skt(self, s):
		if s in self.transmitters:
			self.transmitters.remove(s)
		self.receivers.remove(s)
		s.close()
		del self.tx_queues[s]

	def poll(self):
		# Get the list sockets which are ready to be read through select
		readable,writable,exceptional = select.select(
			self.receivers,
			self.transmitters,
			self.receivers,
			0) # Zero timeout

		for s in readable:
			# New connection
			if s == self.server:
				sockfd, addr = self.server.accept()
				sockfd.setblocking(0)
				self.receivers.append(sockfd)
				self.tx_queues[sockfd] = Queue.Queue()
				print ("Client (%s, %s) connected" % addr)

			# Data from client
			else:
				try:
					data = s.recv(4096)
					if data:
						for c in data:
							if c == '\n':
								self.callback(self.cmd_buf)
								self.cmd_buf = ""
							else:
								self.cmd_buf += c

					# If null packet, disconnect client
					else:
						print ("Client disconnected")
						self.remove_skt(s)
				except socket.error, e:
					print("Socket error", e)
					self.remove_skt(s)
					
		for s in writable:
		    try:
		        next_msg = self.tx_queues[s].get_nowait()
		    except Queue.Empty:
		        self.transmitters.remove(s)
		    except KeyError:
				if s in self.transmitters:
					self.transmitters.remove(s)
		    else:
		        s.send(next_msg)

		for s in exceptional:
		    self.remove_skt(s)

	def send(self, data):
		for k in self.receivers:
			if not (k == self.server):
				self.tx_queues[k].put(data)
				if k not in self.transmitters:
					self.transmitters.append(k)

	def waiting(self):
		return len(self.received_packets)

	def get(self):
		return self.received_packets.pop()


