#!/usr/bin/env python

'''NI USB DIO driver

Use NI-USB-6501 to talk to S1 QuickSwipeTest fixture

'''

import os
import subprocess
import json

ENABLE_DEVICE = True


class NiUsbDioException(Exception):
    def __init__(self, value):
        self.value = value
        Exception.__init__(self)

    def __str__(self):
        return repr(self.value)


class NIUSBDIO(object):
    def __init__(self, ni_device_id=1):  # format
        self._dev = "Dev%d" % ni_device_id
        self._num_ports = 4
        self._util_path = "../bin/niDioUtil.exe"
        self._is_debug_enabled = False

    def enable_debug(self, enable=True):
        self._is_debug_enabled = enable

    def _debug_print(self, msg):
        if self._is_debug_enabled:
            print ("DEBUG: %s" % msg)

    def change_util_path(self, path):
        if not os.path.isfile(path):
            raise NiUsbDioException("NiDaq util not found at path %s" % path)
        self._util_path = path

    def write_byte(self, port_number, byteval):
        port_string = self.make_port_string(port_number)
        self._check_user_byte(byteval)
        callstring = self._util_path + " -d " + self._dev + " -p " + port_string + " -w " + str(byteval)
        self._dispatch(callstring)

    def read_byte(self, port_number):
        port_string = self.make_port_string(port_number)
        call_string = self._util_path + " -d " + self._dev + " -p " + port_string + " -r "
        output, exit_code = self._dispatch(call_string)
        if not exit_code == 0:
            raise NiUsbDioException("NiDaq util returned a non-zero value: [%d:%s]" % (exit_code, output))

        byte_val = None
        obj = json.loads(output)
        if "BYTEVAL" in obj:
            byte_val = obj.get("BYTEVAL")
        else:
            raise NiUsbDioException("Unexpected console output received from dio util: [%s]" % output)

        return int(byte_val, 16)

    @staticmethod
    def _check_user_byte(byteval):
        if type(byteval) is int:
            byte_me = byteval
        elif type(byteval) is str:
            if "0x" in byteval or "0X" in byteval:
                byte_me = int(byteval, 16)
            else:
                byte_me = int(byteval)
        else:
            raise NiUsbDioException("WriteByte: Don't know how to deal with byte %s." % str(byteval))

        if byte_me < 0 or byte_me > 255:
            raise NiUsbDioException("WriteByte: %s is not a valid byte." % str(byteval))

        return

    def make_port_string(self, port_num):
        '''Take in a port number and convert to a string '''
        if port_num < 0 or port_num > (self._num_ports-1):
            raise NiUsbDioException("Port number %d is not valid." % port_num)

        return "port%d" % port_num

    def _dispatch(self, callstring):

        self._debug_print(callstring)

        if ENABLE_DEVICE:
            write_process = subprocess.Popen(callstring, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = write_process.communicate()

            returncode = write_process.wait()
        else:
            output = "fake stdout string"
            returncode = 0

        self._debug_print("[%d]\n%s" % (returncode, output))
        return (output, returncode)


if __name__ == '__main__':
    DEVICE = NIUSBDIO(3)

    try:
        try:
            print "port string is %s" % (DEVICE.make_port_string(0))
            print "port string is %s" % (DEVICE.make_port_string(3))
            print "port string is %s" % (DEVICE.make_port_string(4))
            print "port string is %s" % (DEVICE.make_port_string(-1))

        except NiUsbDioException as dio_exception:
            print ("Bum port number! %s" % str(dio_exception))

        try:
            DEVICE.change_util_path("niDioUtil.exe")
        except NiUsbDioException as dio_exception:
            print ("bad path: %s" % str(dio_exception))

        try:
            print ("polling ports...:")
            CYCLE = 1
            while True:

                CYCLE += 1
                if CYCLE == 1:
                    DEVICE.write_byte(1, 0x10)
                elif CYCLE == 2:
                    DEVICE.write_byte(1, 0x20)
                elif CYCLE == 3:
                    DEVICE.write_byte(1, 0x40)
                    CYCLE = 0

                ZERO = DEVICE.read_byte(0).rstrip()
                TWO = DEVICE.read_byte(2).rstrip()

                print ("[%d] Port 0 value = [%s]\tPort 2 value = [%s]" % (CYCLE, ZERO, TWO))

        except NiUsbDioException as dio_exception:
            print ("read exception %s" % str(dio_exception))
    except KeyboardInterrupt:
        print ("Caught keyboard interrupt.  Exiting...")
        exit()
