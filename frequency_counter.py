#!/usr/bin/env python

'''Python wrapper around the basic frequency counter exe.

VC_DigFreq_LowFreq1Ctr.exe

'''

import os
import subprocess
import json

ENABLE_DEVICE = True


class NIFrequencyCounterException(Exception):
    pass


class NIFrequencyCounterTimeoutException(Exception):
    def __init__(self, value=None):
        value = "Frequency measurement timed out.  (Too few edges counted.)"
        if value is not None:
            self.value = value
        Exception.__init__()

    def __str__(self):
        return repr(self.value)


class NIFrequencyCounter(object):
    def __init__(self, ni_device_id=1, binary_path="niFreqCtr.exe"):
        self._dev = "Dev%d" % ni_device_id
        self._binary_path = binary_path
        self._is_debug_enabled = False

    def enable_debug(self, enable=True):
        self._is_debug_enabled = enable

    def _debug_print(self, msg):
        if self._is_debug_enabled:
            print ("DEBUG: %s" % msg)

    def change_binary_path(self, path):
        if not os.path.isfile(path):
            raise NIFrequencyCounterException("NiDaq util not found at path %s" % path)
        self._binary_path = path

    def measure_frequency(self):
        call_string = self._binary_path
        (output, exit_code) = self._dispatch(call_string)
        if not exit_code == 0:
            raise NIFrequencyCounterException("Util returned a non-zero value: [%d:%s]" % (exit_code, output))
        frequency = None
        if "FREQ_HZ" in output:
            obj = json.loads(output)
            frequency = obj.get("FREQ_HZ")
        elif "-200474" in output:
            raise NIFrequencyCounterTimeoutException()
        else:
            raise NIFrequencyCounterException("Unexpected console output received from util: [%s]" % output)
        return frequency

    def _dispatch(self, call_string):

        self._debug_print(call_string)

        if ENABLE_DEVICE:
            write_process = subprocess.Popen(call_string, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, std_err_out = write_process.communicate()
            self._debug_print("STDOUT = %s STDERR = %s \n" % (output, std_err_out))
            return_code = write_process.wait()
        else:
            output = "fake stdout string"
            return_code = 0

        self._debug_print("[%d]\n%s" % (return_code, output))
        return (output, return_code)
