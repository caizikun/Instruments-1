#!/usr/bin/env python

'''Python wrapper around the basic recordSwipe exe.

'''

import os
import subprocess
import csv

ENABLE_DEVICE = True
ultrafinn_fullscale_voltage=5
ultrafinn_logic_high_threshold_voltage=3

class NIAnalogInException(Exception):
    pass


class NIAnalogIn(object):

    def __init__(self,
                 ni_device_id=2,  # device id is 2 on LAB PC for NI DAQ 6211: PLEASE CHECK!
                 binary_path="recordSwipe.exe"):  # CHECK path!
        self._dev = "Dev%d" % ni_device_id
        self._binary_path = binary_path
        self._is_debug_enabled = False
        self._tempfile = {'0': "", '1': "", '2': "", '3': ""}
        self.frequency_KHz = {'0': None, '1': None, '2': None, '3': None}
        self.mean_volt = {'0': None, '1': None, '2': None, '3': None}
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

    def get_frequency_KHz(self, ultrafinn=None):
        if ultrafinn==None:
            raise NIAnalogInException("UltraFinn not defined")
        elif ultrafinn<0 or ultrafinn >3:
            raise NIAnalogInException("UltraFinn number must be [0..3]")
        else:
            return self.frequency_KHz[ultrafinn]

    def get_average_squarewave(self, ultrafinn=None):
        if ultrafinn==None:
            raise NIAnalogInException("UltraFinn not defined")
        elif ultrafinn<0 or ultrafinn >3:
            raise NIAnalogInException("UltraFinn number must be [0..3]")
        else:
            return self.mean_volt[ultrafinn]

    def acquire_and_compute(self, channels=None, sample_time=1):
        if channels is None:
            raise NIAnalogInException("At least one channel is required, input as a list")
        for i in channels:
            if i < 0 or i > 15:
                raise NIAnalogInException("Channel value must be [0..15]")
            else:
                self._acquire_samples(sample_time, i, 250000)
                self._compute_freq(i)
                self._average_squarewave(i)

    def _acquire_samples(self, sample_time=1, channel=1, sample_frequency=48000):
        channel_name_str = "AI" % channel
        tempfile = "samples_channel%d.csv" % channel
        if os.path.isfile(tempfile):
            os.remove(tempfile)
        call_string = (self._binary_path +
                       " -f " +
                       tempfile +
                       " -x " +
                       self._dev +
                       "/" +
                       channel_name_str +
                       " -r " +
                       str(sample_frequency) +
                       " -a " +
                       str(sample_time))
        self._tempfile[channel] = tempfile
        (output, exit_code) = self._dispatch(call_string)
        if not exit_code == 0:
            raise NIAnalogInException("Util returned a non-zero value: [%d:%s]" % (exit_code, output))
        elif not os.path.isfile(tempfile):
            raise NIAnalogInException("Output File does not exist")
        else:
            return 0

    # This method assumes that the CSV file has a header row, which is the default for NI DAQs
    def _compute_freq(self, channel):
        signal = []
        with open(self._tempfile[channel], "rb") as csvfile:
            logreader = csv.reader(csvfile, delimiter=',')
            i = 0
            for row in logreader:
                i += 1
                if i == 1:  # skip header row
                    continue
                rownew = row[1][1:]
                signal.append(int(round(float(rownew))))
        q = 1
        no_of_transitions = 0  # from low to high
        for i in signal:
            q += 1
            if q > (signal.__len__() - 1):
                break
            if signal[q] == 0 and signal[q-1] != 0:
                no_of_transitions += 1
        self.frequency_KHz[channel] = (float(no_of_transitions) / 1000)

    def _average_squarewave(self, channel):
        signal = []
        with open(self._tempfile[channel], "rb") as csvfile:
            logreader = csv.reader(csvfile, delimiter=',')
            i = 0
            for row in logreader:
                i += 1
                if i == 1:
                    continue
                rownew = row[1][1:]
                signal.append(int(round(float(rownew))))
        high = 0
        all = 0
        for i in signal:
            all += 1
            if i > ultrafinn_logic_high_threshold_voltage:
                high += 1
        self.mean_volt[channel] = ((float(high) / float(all)) * ultrafinn_fullscale_voltage)

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


def main():
    obj = NIAnalogIn()
    obj.acquire_and_compute([0, 1, 2, 3], 1)
    print("Frequency at Channel 0 : %f KHz" % obj.get_frequency_KHz(0))
    print("Frequency at Channel 1 : %f KHz" % obj.get_frequency_KHz(1))
    print("Frequency at Channel 2 : %f KHz" % obj.get_frequency_KHz(2))
    print("Frequency at Channel 3 : %f KHz" % obj.get_frequency_KHz(3))
    print("Average DC value at Channel 0 : %f Volt" % obj.get_average_squarewave(0))
    print("Average DC value at Channel 1 : %f Volt" % obj.get_average_squarewave(1))
    print("Average DC value at Channel 2 : %f Volt" % obj.get_average_squarewave(2))
    print("Average DC value at Channel 3 : %f Volt" % obj.get_average_squarewave(3))



