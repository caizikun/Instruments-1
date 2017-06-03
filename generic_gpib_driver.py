#!/usr/bin/env python
# pylint: disable=R0903

import os
import subprocess

DEFAULT_GPIBCMD_DIR = "C:/square/factory-test/bin/CmdGpib"
GPIBCMD_BIN = "gpib_cmd.exe"

# Callers need to remember to print with %e to get this accurate.


def convert_scientific_to_float(number_string):
    number_string = number_string.strip("\n\r")  # just \n leaves the carraige return on windows.  Need both
    if number_string == "":
        raise GPIBError("No response from instrument")

    numeric = float(number_string)
    return float(numeric)


def convert_path_to_windows(path):
    return path.replace("/", "\\")


class GPIBError(Exception):
    def __init__(self, value=""):
        self.value = value
        Exception.__init__(self)

    def __str__(self):
        return repr(self.value)


class GpibInstrument(object):
    def __init__(self, visa_descriptor_string, command_files_directory=None, binary_directory=None, debug_mode=False):
        self.__visa_address = visa_descriptor_string
        self.__command_file_root = None
        if command_files_directory is not None:
            self.__command_file_root = command_files_directory

        if binary_directory is None:
            self.__binary_directory = DEFAULT_GPIBCMD_DIR
        else:
            self.__binary_directory = binary_directory
        self.__fq_bin = self.__binary_directory + "/" + GPIBCMD_BIN

        self.__debug_mode = debug_mode

    def __massage_command_path(self, filename):
        prefix = ""
        if self.__command_file_root is not None:
            prefix = self.__command_file_root + '/'

        return prefix + filename

    def generate_command_file_from_string(self, command_file_name, command_string):
        cooked_filepath = self.__massage_command_path(command_file_name)
        winpath = convert_path_to_windows(cooked_filepath)
        command_file = open(winpath, 'w')
        command_file.write(command_string)
        command_file.close()


    def send_commands_from_file(self, command_file, expect_nonempty_response=True):
        cooked_filepath = self.__massage_command_path(command_file)
        winpath = convert_path_to_windows(cooked_filepath)
        call_string = ("%s -a%s -f\"%s\"" % (self.__fq_bin, self.__visa_address, winpath))
        print "SENDCMD: {0}".format(call_string)
        output = ""
        num_retries = 1
        max_retries = 3

        # gpib_cmd utility just exits silently if file doesn't exist, so we have to check explictly
        if not os.path.isfile(cooked_filepath):
            if self.__debug_mode:
                print ("target file %s doesn't exist.  Would bail if not debug mode." % cooked_filepath)
            else:
                raise GPIBError("file %s does not exist!" % cooked_filepath)

        if self.__debug_mode:
            print ("command string = %s" % call_string)
        else:

            # FIRST TRY, RUN BY EVERYONE:
            print "GPIB DEBUG: attempt %d" % num_retries
            try:
                writeprocess = subprocess.Popen(call_string, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                output, standard_error = writeprocess.communicate()
                if standard_error is not None:
                    print "stderr: "+standard_error
                writeprocess.wait()

            except OSError as the_exception:
                raise GPIBError("ERROR: Unable to run GPIB command utility: \n" + str(the_exception))

            num_retries += 1

            # Then if we are expecting a response, loop until we get the response.
            while expect_nonempty_response is True and (output == "") and (num_retries <= max_retries):
                print "GPIB DEBUG: attempt %d" % num_retries
                try:
                    writeprocess = subprocess.Popen(call_string, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    #I'm only interested in stdout,not stderr -- but I need to catch both because of subprocess
                    # Lint/PEP8 can bite me.
                    output, standard_error = writeprocess.communicate()
                    if standard_error is not None:
                        print "stderr: "+standard_error
                    writeprocess.wait()

                except OSError as the_exception:
                    raise GPIBError("ERROR: Unable to run GPIB command utility: \n" + str(the_exception))

                num_retries += 1

        return output


if __name__ == '__main__':
    POWER_SUPPLY = GpibInstrument("PS", command_files_directory="c:/square/factory-test/data", debug_mode=False)
    print (POWER_SUPPLY.send_commands_from_file("OutputOn.txt"))

    MUX = GpibInstrument("MUX", command_files_directory="c:/square/factory-test/data", debug_mode=False)
    TEST_RESULT = MUX.send_commands_from_file("TakeSingleMeasurement_ISupply.txt")
    print ("conversion test: %e" % convert_scientific_to_float(TEST_RESULT))
