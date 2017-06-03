import subprocess


class NircmdError(Exception):
    pass

NIRCMD_WIN_MAXVOLUME = 65535
NIRCMD_WIN_MINVOLUME = 0


class NircmdWin(object):
    """
    Driver for Nirsoft's Nircmd Windows Utility
    http://www.nirsoft.net/utils/nircmd.html
    """
    def __init__(self, station_config, operator_interface):
        self._operator_interface = operator_interface
        self._path_to_nircmd = station_config.NIRCMD_BIN

    def _generate_nircmd_call(self, command, *args):
        command_string = self._path_to_nircmd + ' ' + command
        for arg in args:
            command_string = command_string + ' ' + str(arg)
        self._operator_interface.print_to_console("NIRCMD command: " + command_string + "\n")

        try:
            write_process = subprocess.Popen(command_string,
                                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False,
                                             creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
            (nircmd_stdout_data, nircmd_stderr_data) = write_process.communicate()
            if write_process.wait() != 0:
                self._operator_interface.print_to_console('ERROR: Unable to execute nircmd!\n')
                raise NircmdError
            else:
                if nircmd_stderr_data is not None:
                    self._operator_interface.print_to_console("NIRCMD STDERR: '" +
                                                              str(nircmd_stderr_data) + "'\n")
                if nircmd_stdout_data is not None:
                    self._operator_interface.print_to_console("NIRCMD STDOUT:\n" + nircmd_stdout_data + "\n")
        except OSError as the_error:
            self._operator_interface.print_to_console("ERROR: Unable to launch nircmd: \n" + str(the_error))
            raise NircmdError

    def set_output_volume(self, volume):
        if volume <= NIRCMD_WIN_MAXVOLUME and volume >= NIRCMD_WIN_MINVOLUME:
            self._generate_nircmd_call('setsysvolume', volume, 'speakers')
        else:
            self._operator_interface.print_to_console("volume must be between {0} and {1}".format(NIRCMD_WIN_MINVOLUME,
                                                      NIRCMD_WIN_MAXVOLUME))
            raise NircmdError

    def set_mic_volume(self, volume):
        if volume <= NIRCMD_WIN_MAXVOLUME and volume >= NIRCMD_WIN_MINVOLUME:
            self._generate_nircmd_call('setsysvolume', volume, 'microphone')
            self._generate_nircmd_call('setsysvolume', volume, 'line-in')
        else:
            self._operator_interface.print_to_console("volume must be between {0} and {1}".format(NIRCMD_WIN_MINVOLUME,
                                                      NIRCMD_WIN_MAXVOLUME))
            raise NircmdError
