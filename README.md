This repository dives into the communication protocol used in Anslut air to water heat pumps (Jula art. nr. 416120 tested). They are normally operated using a control panel, but this project makes it possible to control it from a computer.

In short, you need a hardware interface and a piece of software to be able to control it through e.g. Home Assistant with a user interface like this:

![Home assistant UI](https://raw.githubusercontent.com/skagmo/anslut_heatpump/master/img/anslut_hass.png?raw=true)

# Main protocol

A python class is defined in ```anslut_proto.py```. Run ```anslut_gw.py``` in this repository to get a text based TCP socket interface for reading/writing settings from the heat pump.

## Physical interface

The physical interface is an isolated open collector UART with high voltage levels (12 V), 100 baud, odd parity, MSB first bit order (LSB first is normal). This interface will allow you to communicate with a 3.3 V / 5 V UART.

![Interface schematic](https://raw.githubusercontent.com/skagmo/anslut_heatpump/master/img/schematic.png?raw=true)

## Packet to main PCB

Sent typically once every second.

| File/folder       | Description |
|:-----------       |:----------- |
| documentation/    | More documentation. |

| Index | Description |
|:---   |:---         |
| 0 | Start byte, fixed at 0x39 (0x9c if not flipped LSB to MSB) |
| 1 | Operating mode, 0x10: Cooling (water temperature), 0x24: Heating (water temperature), 0x20: Heating (room/external temperature). |XOR with 0x01 to actually enable the selected mode. |
| 2 | Room temperature |
| 3 | Temperature setpoint |
| 4 | (Always zero) |
| 5 | Check sum. 0x100 minus sum of bytes 1-4. |

Example packet when heating water: ```0x39 0x25 0x1c 0x23 0x00 0x9c```

## Packet from main PCB

Sent typically every 5 second, but only when requests are sent to the main PCB.

| Index | Description |
|:---   |:---         |
| 0 | Start byte, fixed at 0x39 |
| 1 | 0x00: Inactive. 0x01: Active. 0x03: Deicing. |
| 2 | Return water temperature |
| 3 | Power level (0-85 decimal, where 85 is maximum power) |
| 4 | Unknown. Typically 0x11 when idle and 0x00 when running. Error codes/status? |
| 5 | Checksum. Same as above. |

# Expansion PCB protocol

This is based on standard RS-485.

I didin't dive as much into this protocol as it doesn't give the same low level access, but see ```expansion_protocol.txt``` and ```anslut_proto_expansion.py``` if you are interested.

# About the protocols

The newer Jula 416120 heat pump has three main components that are connected together. Two PCBs and an "advanced" control panel. Earlier versions of this pump (Jula articles 416086 and 416107) only had one PCB in the indoor unit and a more simple control panel.

![PCBs](https://raw.githubusercontent.com/skagmo/anslut_heatpump/master/img/pcbs-text.jpg?raw=true)

## Main PCB

This does the important work. Controls the outdoor unit based on temperature reading and desired setpoint. Connects to:
* Circulation pump
* Outdoor unit (with another PCB controlling the compressor and fan)
* Temperature sensors on evaporator and water outlet/inlet
* A communication device, which could be either the extra PCB or the old control panel.

## Expansion PCB

This is an additional PCB that was added for more advanced control:
* Up to 6 temperature sensors that can be placed in external accumulator tanks, outside temperature etc.
* Allows outdoor temperature compensation, controlling 3-way shunt for hot water heating etc.
* Connects to the main PCB and control panel
* "Pretends" to be an old control panel for the main PCB

## Control panel

The older system had a control panel with an integrated temperature sensor. The system could be controlled by the room temperature of where this was placed. The newer pumps have a more advanced control panel for setting all features in the expansion PCB (outdoor temperature compensation etc.), but the panel itself has no built in temperature sensor.

