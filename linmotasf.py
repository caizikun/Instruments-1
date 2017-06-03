import time
import serial
import array
import struct
import csv
import contextlib

import webpower

_HOMING_TIMEOUT = 30
_POLL_DELAY = 0.5
_MOVE_TIMEOUT = 30
_ERROR_DECEL = 1  # m/s/s

_REQUEST_DEFAULT_RESPONSE_COMMAND = [0x01, 0x00, 0x03, 0x02, 0x01, 0x00, 0x04]
_CLEAR_LOCK_STATE_COMMAND = [0x01, 0x00, 0x05, 0x02, 0x00, 0x01, 0x00, 0x00, 0x04]
_HOME_COMMAND = [0x01, 0x00, 0x05, 0x02, 0x00, 0x01, 0x3F, 0x08, 0x04]
_STOP_COMMAND = [0x01, 0x00, 0x05, 0x02, 0x00, 0x01, 0x07, 0x02, 0x04]
_ENABLE_OPERATION_COMMAND = [0x01, 0x00, 0x05, 0x02, 0x00, 0x01, 0x3F, 0x00, 0x04]

_HOMING_STATE = 0x09
_HARDWARE_TEST_STATE = 0x05
_OPERATION_ENABLED_STATE = 0x08
_HOMING_FINISHED = 0x0F

_POSITION_MASK = 0b01000000
_COUNT_MASK = 0b00001111

_TELEGRAM_GUARANTEED_BYTES = 3

_SUBSTATE_OFFSET_IN_RESPONSE = 9
_STATE_OFFSET_IN_RESPONSE = 10
_LOCATION_OFFSET_IN_RESPONSE = 11

_ACCELERATION_CORRECTION = 100000
_POSITION_CORRECTION = 10000
_VELOCITY_CORRECTION = 1000000


class LinmotAsfException(Exception):
    pass


@contextlib.contextmanager
def make_linmot_asf(linmot_asf_port, web_power_url, web_power_outlet, verbose=False):
    asf = LinmotAsf(linmot_asf_port, web_power_url, web_power_outlet, verbose)
    try:
        yield asf
    finally:
        if asf:
            asf.close()


class LinmotAsf(object):
    def __init__(self, linmot_asf_port, web_power_url, web_power_outlet, verbose=False):
        self._serial_port = serial.Serial(linmot_asf_port,
                                          57600,
                                          parity='N',
                                          stopbits=1,
                                          timeout=5,
                                          xonxoff=0,
                                          rtscts=0)
        if not self._serial_port:
            raise LinmotAsfException('Unable to open Linmot ASF serial port ' + linmot_asf_port)

        self._web_power = None if web_power_url is None else webpower.WebPower(web_power_url)
        self._web_power_outlet = web_power_outlet
        self._linmot_asf_port = linmot_asf_port
        self._verbose = verbose
        self._read_error = False

    def __del__(self):
        self.close()

    def close(self):
        if hasattr(self, '_s') and self._serial_port:
            if not self._read_error:
                self.stop()
                self.clear_lock_state()
            self._serial_port.close()
            self._serial_port = None
        if hasattr(self, '_webPower') and self._web_power:
            self._web_power.turn_port_off(self._web_power_outlet)
            self._web_power = None

    def setup_motor(self):
        if self._web_power:
            print('Power cycling Linmot ASF...')
            if self._web_power.get_status(self._web_power_outlet):
                self._web_power.turn_port_off(self._web_power_outlet)
                time.sleep(5)
            self._web_power.turn_port_on(self._web_power_outlet)
            time.sleep(5)

        self.clear_lock_state()
        self._write_serial(_HOME_COMMAND)
        self._read_response()

        homed = False
        now = time.time()
        start = now

        while (now - start) < _HOMING_TIMEOUT:
            self._write_serial(_HOME_COMMAND)
            response_bytes = self._read_response()
            status = struct.unpack('<BBBBBBBBBBBiiB', response_bytes)

            if (status[_STATE_OFFSET_IN_RESPONSE] != _HOMING_STATE) and \
                    (status[_STATE_OFFSET_IN_RESPONSE] != _HARDWARE_TEST_STATE):
                raise LinmotAsfException('State was ' + str(status[_STATE_OFFSET_IN_RESPONSE]) +
                                         ' Expected 0x09 (homing) or 0x05 (hardware test)')

            if status[_SUBSTATE_OFFSET_IN_RESPONSE] == _HOMING_FINISHED:
                homed = True
                break

            time.sleep(_POLL_DELAY)
            now = time.time()

        if not homed:
            raise LinmotAsfException('Took too long to home.')

        self.enable_operation()

    def move_to(self, pos, vel, accel):
        count = self._get_next_count()

        payload = [0x01, 0x00, 0x15, 0x02, 0x00, 0x02]

        for byte in struct.pack('B', count):
            payload.append(ord(byte))

        payload.append(0x01)

        for byte in struct.pack('<i', pos * _POSITION_CORRECTION):
            payload.append(ord(byte))

        for byte in struct.pack('<i', vel * _VELOCITY_CORRECTION):
            payload.append(ord(byte))

        for byte in struct.pack('<i', accel * _ACCELERATION_CORRECTION):
            payload.append(ord(byte))

        for byte in struct.pack('<i', accel * _ACCELERATION_CORRECTION):
            payload.append(ord(byte))

        payload.append(0x04)

        self._write_serial(payload)
        self._read_response()

        start = time.time()
        while (time.time() - start) < _MOVE_TIMEOUT:
            if self._verbose:
                print "polling"
            substate, state = self._get_default_response()
            if self._verbose:
                print "gotdefaultresponse"
            mask = _POSITION_MASK
            moved = mask & substate

            if (state == _OPERATION_ENABLED_STATE) and moved:
                return

            time.sleep(_POLL_DELAY)

        raise LinmotAsfException('Took too long to move.')

    def stop(self):
        self._write_serial(_STOP_COMMAND)
        self._read_response()

    def clear_lock_state(self):
        self._write_serial(_CLEAR_LOCK_STATE_COMMAND)
        self._read_response()

    def enable_operation(self):
        self._write_serial(_ENABLE_OPERATION_COMMAND)
        self._read_response()
        time.sleep(2)

    def _write_serial(self, input_bytes):
        byte_string = array.array('B', input_bytes).tostring()

        if self._verbose:
            print('writing: ' + _string_from_bytes(byte_string))

        bytes_written = self._serial_port.write(byte_string)
        if self._verbose:
            print "wrote, flushing"
        self._serial_port.flush()
        if self._verbose:
            print "flushed"
        return bytes_written

    def _read_response(self):
        if self._verbose:
            print "initiating read"
        response_bytes = self._serial_port.read(_TELEGRAM_GUARANTEED_BYTES)
        if self._verbose:
            print "read finished read " + str(len(response_bytes)) + " bytes"
        if len(response_bytes) != _TELEGRAM_GUARANTEED_BYTES:
            self._read_error = True
            raise LinmotAsfException('Serial read error')

        if response_bytes:
            if self._verbose:
                print "read " + response_bytes
            data = struct.unpack('BBB', response_bytes)
            expected_length = int(data[2]) + 1
            new_bytes = self._serial_port.read(expected_length)

            if len(new_bytes) != expected_length:
                self._read_error = True
                print "read error"
                raise LinmotAsfException('Serial read error')

            if new_bytes:
                response_bytes += new_bytes

        if self._verbose:
            print('received: ' + _string_from_bytes(response_bytes))
        return response_bytes

    def _get_next_count(self):
        substate, state = self._get_default_response()

        if state != _OPERATION_ENABLED_STATE:
            raise LinmotAsfException('mainState was ' + str(state) + ', expected 0x08')

        old_count = _COUNT_MASK & substate
        count = (old_count + 1) % 16
        if self._verbose:
            print('Count:' + str(count))
            print('MainState = ' + str(state))

        return count

    def _get_default_response(self):
        self._write_serial(_REQUEST_DEFAULT_RESPONSE_COMMAND)
        response_bytes = self._read_response()
        status = struct.unpack('<BBBBBBBBBBBiiB', response_bytes)

        if self._verbose:
            print("location: " + str(status[_LOCATION_OFFSET_IN_RESPONSE]))

        substate = status[_SUBSTATE_OFFSET_IN_RESPONSE]
        state = status[_STATE_OFFSET_IN_RESPONSE]
        return substate, state


def _string_from_bytes(input_bytes):
    return ''.join(['%02X ' % ord(b) for b in input_bytes]).strip()


def main():
    tests = []
    with open('test.csv', 'rb') as testfile:
        testfile.readline()  # skip column headers
        test_lines = csv.reader(testfile, delimiter=',')
        for test_line in test_lines:
            tests.append([float(x) for x in test_line[:5]])

    with make_linmot_asf('/dev/cu.usbserial-FTVLVKEI', None, 4, False) as test_asf:
        test_asf.setup_motor()
        test_asf.clear_lock_state()
        raw_input('Please position motor, then press return')
        test_asf.enable_operation()
        time.sleep(0.5)

        for test in tests:
            print test
            from_pos = int(test[1])
            to_pos = int(test[2])
            velocity = float(test[3])
            acceleration = float(test[4])
            for _ in xrange(int(test[0])):
                test_asf.move_to(from_pos, velocity, acceleration)
                raw_input('Please press return to swipe.')
                test_asf.move_to(to_pos, velocity, acceleration)
                raw_input('Please press return to swipe.')
                test_asf.move_to(from_pos, velocity, acceleration)


if __name__ == '__main__':
    import sys
    sys.exit(main())
