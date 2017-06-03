import subprocess
import os.path
#pylint: disable=R0903


class JlinkError(Exception):
    pass


class JlinkProgrammer(object):
    """
    Driver for Segger/Jlink JTAG SWD Programmer
    """
    def __init__(self, stationConfig, operatorInterface):
        self._operator_interface = operatorInterface
        self._path_to_jflash = stationConfig.JLINK_BIN
        self._path_to_jlink = stationConfig.JLINK_EXE_BIN

    def do_jflash(self, project_file_name, binary_image_file_name, offset="0x0"):
        """
        generic call for when you have:
        a project file, a binary file, [offset] (and no other special options)
        :param project_file_name:
        :param binary_image_file_name:
        :return:
        """
        try:
            #the "start /min /wait" part runs the process minimized in the background so the giant JFlash GUI
            # doesn't eat your screen
            # shell=True is needed because "start" is a system command, see subprocess.Popen() docs for details
            jflash_command = ('"' + self._path_to_jflash + '" -openprj\"' + project_file_name
                              + '\" -open\"' + binary_image_file_name + '\",' + offset + ' -connect -auto -exit')
            write_process = subprocess.Popen(jflash_command, shell=True,
                                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            (stdout_jlink, stderr_jlink) = write_process.communicate()
            self._operator_interface.print_to_console(str(stdout_jlink) + '\n')
            self._operator_interface.print_to_console(stderr_jlink + "\n")
            return_code = write_process.wait()
            self._operator_interface.print_to_console('Jlink: Return Code {0}\n'.format(return_code))
            if return_code != 0:
                self._operator_interface.print_to_console('ERROR: Unable to program the part. \n' +
                                                          'Check JFlashARM.log for detailed error report.\n')
                jflash_err_log_dir = os.path.dirname(project_file_name)
                jflash_err_log_filename = os.path.join(jflash_err_log_dir, "JflashArm.log")
                if os.path.exists(jflash_err_log_filename):
                    jflash_err_log_contents = ''.join(open(jflash_err_log_filename, 'r').readlines())
                    self._operator_interface.print_to_console('********** JflashArm.log **********\n')
                    self._operator_interface.print_to_console(jflash_err_log_contents + '\n')
                return False
            else:
                return True
        except OSError as err:
            self._operator_interface.print_to_console('ERROR: Unable to launch JFlash: \n' + str(err) + '\n')
            raise JlinkError

    def do_jlink_K21_512k_erase(self, jlink_id = None):
        self._operator_interface.print_to_console("JLink ID {0}\n".format(jlink_id))
        device = "MK21FX512xxx12"
        commandlist = ['halt','erase','r']
        jlinkscriptfn = self._make_jlinkscript('commanderscript', commandlist)
        return self._run_jlink_against_commander_script(jlinkscriptfn,device,'SWD', '0', jlink_id)            
            
    def do_jlink_K21_512k_unlock(self, jlink_id = None):
        self._operator_interface.print_to_console("JLink ID {0}\n".format(jlink_id))
        device = "MK21FX512xxx12"
        commandlist = ['sleep 100','power on','unlock kinetis']
        jlinkscriptfn = self._make_jlinkscript('commanderscript', commandlist)
        return self._run_jlink_against_commander_script(jlinkscriptfn,device,'SWD', '0', jlink_id)
    
    def do_jlink_K21_512k_loadbin(self, binary_image, jlink_id = None):
        device = "MK21FX512xxx12"
        commandlist = ['halt','erase','loadbin %s 0' % binary_image, 'r']
        jlinkscriptfn = self._make_jlinkscript('commanderscript', commandlist)
        return self._run_jlink_against_commander_script(jlinkscriptfn,device,'SWD', '0', jlink_id)
    
        
    def do_jlink_K21_512k_reset(self, jlink_id = None):
        device = "MK21FX512xxx12"
        commandlist = ['r']
        jlinkscriptfn = self._make_jlinkscript('commanderscript', commandlist)
        return self._run_jlink_against_commander_script(jlinkscriptfn,device,'SWD', '0', jlink_id)
    
    def do_jlink_ticc2640_loadfile(self, binary_image, jlink_id = None):
        if not binary_image.endswith (".hex"):
            raise Exception("JLinkExe loadfile command expects .hex files")
        device = "CC2640F128"
        commandlist = ['loadfile %s' % binary_image]
        jlinkscriptfn = self._make_jlinkscript('commanderscript', commandlist)
        return self._run_jlink_against_commander_script(jlinkscriptfn,device,'JTAG', '0', jlink_id)

    def do_jlink_ticc2640_loadbin(self, binary_image, offset="0x0000", jlink_id = None):
        device = "CC2640F128"
        commandlist = [('loadbin %s' % binary_image) + ',' + offset]
        jlinkscriptfn = self._make_jlinkscript('commanderscript', commandlist)
        return self._run_jlink_against_commander_script(jlinkscriptfn,device,'JTAG', '0', jlink_id) 

    def do_jlink_ticc2640_loadbin_double(self, binary_image_1, offset_1, binary_image_2, offset_2, jlink_id = None):
        device = "CC2640F128"
        commandlist = [('loadbin %s' % binary_image_1) + ',' + offset_1, ('loadbin %s' % binary_image_2) + ',' + offset_2]
        jlinkscriptfn = self._make_jlinkscript('commanderscript', commandlist)
        return self._run_jlink_against_commander_script(jlinkscriptfn,device,'JTAG', '0', jlink_id)  		
		
    def _run_jlink_against_commander_script(self, jlinkscriptfn, target_device, interface, speed, jlink_id = None):
        return_status = {
            'did_pass': False,
            'return_code':None,
            'Stdout':None,
            'Stderr':None
        }
        if not os.path.isfile(self._path_to_jlink):
            raise Exception('ERROR: No J-Link application found')
            
        cmd = "\"" + self._path_to_jlink + '\"'
        if jlink_id is not None:
            cmd = cmd + ' -SelectEmuBySN ' + str(jlink_id)
            
        cmd = cmd + ' -if ' + interface + ' -speed ' + str(speed) + ' -device ' + target_device + ' -CommanderScript ' + jlinkscriptfn
        self._operator_interface.print_to_console("jlink.exe command: \n" + cmd + "\n")     
        
        write_process = subprocess.Popen (cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (stdout_jlink, stderr_jlink) = write_process.communicate()
        return_status['Stdout']=stdout_jlink
        return_status['Stderr']=stderr_jlink
        self._operator_interface.print_to_console(str(stdout_jlink) + '\n')
        self._operator_interface.print_to_console(stderr_jlink + "\n")
        return_status['return_code'] = write_process.wait()
        
        #self._operator_interface.print_to_console('JlinkExe: Return Code {0}\n'.format(return_status['return_code']))
        
        #if return_status['return_code'] == 0:
        #if "Flash programming performed for" in str(stdout_jlink) or "Flash contents already match" in str(stdout_jlink):
        if "O.K." in str(stdout_jlink):
                return_status['did_pass'] =  True
        else:
            self._operator_interface.print_to_console('JLinkExe ERROR: Unable to program the part. \n')
        return return_status
        
    def do_jlink_ticc2640_erase(self, jlink_id = None):
        device = "CC2640F128"
        commandlist = ['erase']
        jlinkscriptfn = self._make_jlinkscript('commanderscript', commandlist)
        return self._run_jlink_against_commander_erase_script(jlinkscriptfn,device,'JTAG', '0', jlink_id)

    def _run_jlink_against_commander_erase_script(self, jlinkscriptfn, target_device, interface, speed, jlink_id = None):
        return_status = {
            'did_pass': False,
            'return_code':None,
            'Stdout':None,
            'Stderr':None
        }
        if not os.path.isfile(self._path_to_jlink):
            raise Exception('ERROR: No J-Link application found')
            
        cmd = "\"" + self._path_to_jlink + '\"'
        if jlink_id is not None:
            cmd = cmd + ' -SelectEmuBySN ' + str(jlink_id)
            
        cmd = cmd + ' -if ' + interface + ' -speed ' + str(speed) + ' -device ' + target_device + ' -CommanderScript ' + jlinkscriptfn
        self._operator_interface.print_to_console("jlink.exe command: \n" + cmd + "\n")     
        
        write_process = subprocess.Popen (cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (stdout_jlink, stderr_jlink) = write_process.communicate()
        return_status['Stdout']=stdout_jlink
        return_status['Stderr']=stderr_jlink
        self._operator_interface.print_to_console(str(stdout_jlink) + '\n')
        self._operator_interface.print_to_console(stderr_jlink + "\n")
        return_status['return_code'] = write_process.wait()
        
        #self._operator_interface.print_to_console('JlinkExe: Return Code {0}\n'.format(return_status['return_code']))
        
        #if return_status['return_code'] == 0:
        #if "Flash programming performed for" in str(stdout_jlink) or "Flash contents already match" in str(stdout_jlink):
        if "Erasing done." in str(stdout_jlink):
                return_status['did_pass'] =  True
        else:
            self._operator_interface.print_to_console('JLinkExe ERROR: Unable to program the part. \n')
        return return_status
    

    def _make_jlinkscript(self, name, cmds):
        filename = "%s.jlinkscript" % name
        f = open(filename, 'w')
        f.write("\n".join(cmds+['qc\n']))
        f.close()
        return filename



