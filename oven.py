import sys
import serial
import crc16


class OvenException(Exception):
    pass


class Oven(object):
    def __init__(self, oven_serial_port_path):
        port = serial.Serial(oven_serial_port_path)
        port.setBaudrate(9600)
        port.setTimeout(5)
        port.setRtsCts(False)
        port.setXonXoff(False)
        port.flush()
        self._oven_serial_port = port
        self._oven_serial_port_path = oven_serial_port_path

    def __del__(self):
        self.close()

    def close(self):
        if hasattr(self, '_oven_serial_port') and self._oven_serial_port:
            self._oven_serial_port.close()
            self._oven_serial_port = None

    def read_temperature(self):
        if not self._oven_serial_port:
            raise OvenException('No serial connection to oven (%s)' % self._oven_serial_port_path)

        request = b'\x01\x03\x00\x64\x00\x01\xC5\xD5'
        self._oven_serial_port.write(request)
        self._oven_serial_port.flush()

        response = self._oven_serial_port.read(7)
        if len(response) == 0:
            raise OvenException('Oven did not respond to temperature request.')
        if len(response) < 7:
            raise OvenException('Oven did not respond correctly to temperature request.\nResponse: ' + str(response))

        temperature = int(response[3:5].encode('hex'), 16) / 10.0
        return temperature

    def set_temperature(self, desired_temperature):
        if not self._oven_serial_port:
            raise OvenException('No serial connection to oven (%s)' % self._oven_serial_port_path)

        temp = int(desired_temperature * 10.0)
        temp_low_byte = _get_low_byte(temp)
        temp_high_byte = _get_high_byte(temp)

        request = b'\x01\x06\x01\x2C' + chr(temp_high_byte) + chr(temp_low_byte)

        crc = crc16.calculate_string(request)
        crc_low_byte = _get_low_byte(crc)
        crc_high_byte = _get_high_byte(crc)

        request += chr(crc_low_byte) + chr(crc_high_byte)
        self._oven_serial_port.write(request)
        self._oven_serial_port.flush()

        response = self._oven_serial_port.read(8)
        self._oven_serial_port.flush()

        if len(response) == 0:
            raise OvenException('Oven did not respond to set temperature command.')
        if len(response) < 8:
            raise OvenException('Oven gave bad response to set temperature command.\nResponse: ' + str(response))


def _get_low_byte(u16):
    return u16 & 0xFF


def _get_high_byte(u16):
    return (u16 >> 8) & 0xFF


def _print_usage():
    print('Usage: %s oven-path [-r] [-s temp]' % sys.argv[0])
    print('  oven-path: path to the RS232 serial port that connects to the oven')
    print('  -r:        read and print oven temperature (in celsius)')
    print('  -s:        set oven temperature (in celsius')


def main():
    if len(sys.argv) < 2 or len(sys.argv) > 4:
        _print_usage()
        return 1

    oven_port = sys.argv[1]
    command = sys.argv[2][-1].lower()

    if (command != 's') and (command != 'r'):
        _print_usage()
        print
        print('Command must be -r or -s.')
        return 1

    if command == 's':
        if len(sys.argv) > 3:
            desired_temp = float(sys.argv[3])
        else:
            _print_usage()
            print
            print('-s flag requires temperature argument')
            return 1

    print('Config:')
    print('  Oven device path: %s' % oven_port)
    print('  Command: ' + ('read' if command == 'r' else 'set') + ' temperature')
    if command == 's':
        print(u'  Oven temperature: %f \N{degree sign}C' % desired_temp)
    print

    oven_device = Oven(oven_port)
    try:
        if command == 'r':
            print(u'Oven temperature: %f \N{degree sign}C' % oven_device.read_temperature())
            return 0

        if command == 's':
            oven_device.set_temperature(desired_temp)
            print(u'Oven temperature set to %f \N{degree sign}C' % desired_temp)
            return 0
    finally:
        oven_device.close()

if __name__ == '__main__':
    sys.exit(main())
