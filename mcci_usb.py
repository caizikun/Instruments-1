import subprocess
import os.path


class McciError(Exception):
    pass


class McciConnExerciser(object):
    def __init__(self, stationConfig, operatorInterface):
        self._operator_interface = operatorInterface
        self._path_to_mcci_bin = stationConfig.MCCI_BIN
        self._mcci_sn = stationConfig.MCCI_SN

    def execute_cmd(self, cmd):
        string = "{0} -{1} -sn {2} -v".format(os.path.join(os.getcwd(), 'bin', self._path_to_mcci_bin), cmd, self._mcci_sn)
        #print (string)
        write_process = subprocess.Popen(string, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        (stdout_data, stderr_data) = write_process.communicate()
        exit_code = write_process.wait()
        if exit_code != 0:
            self._operator_interface.print_to_console('STDERR:\n{0}\n'.format(stderr_data))
            self._operator_interface.print_to_console('STDOUT\n{0}\n'.format(stdout_data))
            self._operator_interface.print_to_console('EXIT_CODE\n{0}\n'.format(exit_code))
            raise  McciError

    def connect_dut(self):
        self._operator_interface.print_to_console ("Connecting DUT")
        self.execute_cmd("ssattach")

    def disconnect_dut(self):
        self._operator_interface.print_to_console ("Disconnecting DUT")
        self.execute_cmd("detach")