#!/usr/bin/python

import sys, serial, time, tcp_server_cb, anslut_proto

# Get command line arguments
TCP_PORT = 1342
if (len(sys.argv) == 2) or (len(sys.argv) == 3):
	SER_PORT = sys.argv[1]
	if (len(sys.argv) == 3):
		TCP_PORT = sys.argv[2]
else:
	print "Usage: anslut_gw.py <serial port (mandatory)> <TCP port>"
	sys.exit(0)

anslut = anslut_proto.anslut(SER_PORT)
tcp = tcp_server_cb.tcp_server("0.0.0.0", TCP_PORT)

anslut.set_callback(tcp.send)
tcp.set_callback(anslut.parse_cmd)

while(1):
	anslut.tick()
	tcp.poll()
	time.sleep(0.05)

