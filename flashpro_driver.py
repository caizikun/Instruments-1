import subprocess
import os.path


class FlashProError(Exception):
    pass


class FlashProProgrammer(object):
    def __init__(self, stationConfig, operatorInterface):
        self._operator_interface = operatorInterface
        self._path_to_flashpro = stationConfig.FLASHPRO_BIN
		
    def do_flash(self, config_file_name, binary_image_file_name):
        return_status = {
            'did_pass': False,
            'return_code':None,
            'Stdout':None,
            'Stderr':None
        }
        if not binary_image_file_name.endswith (".hex"):
			raise Exception("FlashPro-ARM expects .hex code files")
        if not config_file_name.endswith (".cfg"):
			raise Exception("FlashPro-ARM expects .cfg config files")
        script_file = open("script.txt", "w")
        script_commands = ["LOADCFGFILE " + config_file_name + "\n", "LOADCODEFILE " + binary_image_file_name + "\n", "WRITEFLASH \n", "END"]
        script_file.writelines(script_commands)
        script_file.close()
        cmd = "\"" + self._path_to_flashpro + '\"'
        cmd = cmd + ' -rf ' + ' script.txt '
        write_process = subprocess.Popen (cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (stdout_flashpro, stderr_flashpro) = write_process.communicate()
        return_status['Stdout']=stdout_flashpro
        return_status['Stderr']=stderr_flashpro
        self._operator_interface.print_to_console(str(stdout_flashpro) + '\n')
        self._operator_interface.print_to_console(stderr_flashpro + "\n")
        return_status['return_code'] = write_process.wait()
        os.remove("script.txt")
        if "ERROR" in str(stdout_flashpro):
                return_status['did_pass'] =  False
                self._operator_interface.print_to_console('FlashProARM ERROR: Unable to program the part. \n')
        else:
            return_status['did_pass'] =  True
        return return_status