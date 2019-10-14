import sys
import serial
from serial.tools import list_ports


# Connected serial port detecting and port number selecting
def serial_ports():
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    else:
        raise EnvironmentError('Unsupported platform')

    available_ports = []

    for port in ports:
        try:
            serial_port = serial.Serial(port)
            serial_port.close()
            available_ports.append(port)
        except (OSError, serial.SerialException):
            pass
    return available_ports


def search_dplay_port():
    dplay_ports = []

    try:
        com_port_name = str(next(list_ports.grep("Silicon")))
        # Adding connected DPLAY
        dplay_ports.append(com_port_name[0:4])

        return dplay_ports[0]
    except StopIteration:
        print "No device found"

serial_ports()
