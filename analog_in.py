#!/usr/bin/env python

'''Python wrapper around the basic recordSwipe exe.

'''

import os
import subprocess
import csv

ENABLE_DEVICE = True


class NIAnalogInException(Exception):
    pass


class NIAnalogIn(object):
    def __init__(self, ni_device_id=1, binary_path="niFreqCtr.exe", channel="AI0", sample_frequency=48000,
                 tempfile="temp.csv"):
        self._dev = "Dev%d" % ni_device_id
        self._channel = channel
        self._sample_frequency = sample_frequency
        self._binary_path = binary_path
        self._is_debug_enabled = False
        self._tempfile = tempfile
        if not os.path.isfile(binary_path):
            raise NIAnalogInException("Binary path does not exist.")

    def enable_debug(self, enable=True):
        self._is_debug_enabled = enable

    def _debug_print(self, msg):
        if self._is_debug_enabled:
            print ("DEBUG: %s" % msg)

    def change_binary_path(self, path):
        if not os.path.isfile(path):
            raise NIAnalogInException("NiDaq util not found at path %s" % path)
        self._binary_path = path

    def acquire_samples(self, sample_time=1):
        if os.path.isfile(self._tempfile):
            os.remove(self._tempfile)
        call_string = (self._binary_path + " -f " + self._tempfile + " -x " + self._dev + "/" + self._channel + " -r " +
                       str(self._sample_frequency) + " -a " + str(sample_time))
        (output, exit_code) = self._dispatch(call_string)
        if not exit_code == 0:
            raise NIAnalogInException("Util returned a non-zero value: [%d:%s]" % (exit_code, output))
        elif not os.path.isfile(self._tempfile):
            raise NIAnalogInException("Output File does not exist")
        else:
            return 0

    def find_duty(self, high_voltage=5.0):
        sample_data = []
        with open(self._tempfile, 'r') as samplefile:
            sample_reader = csv.reader(samplefile, delimiter=',')
            sample_reader.next()
            for row in sample_reader:
                sample_data.append([float(row[0]), float(row[1])])
        value_array = [row[1] for row in sample_data]
        dc_offset = min(value_array)
        maximum_voltage = max(value_array) - dc_offset
        if maximum_voltage < 0.9 * high_voltage:
            raise NIAnalogInException("No high periods detected")
        else:
            return sum(value_array) / (len(value_array) * maximum_voltage)

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
