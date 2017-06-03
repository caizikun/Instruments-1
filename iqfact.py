# The iqfact will be the parser log only.
import sys
import os

from factory_test_common.test_station.test_log import test_log
from factory_test_common.test_station.test_log import TestResult

class Iqfact(object):
    def parse_iq_log(self, test_log, url = r'C:\Litepoint\IQfact_plus\IQfact+_NXP_PN547_3.2.6\bin\Log\logOutput.txt'):
        if os.path.isfile(url):
            f = open(url)
            lines = f.readlines();            
            temp_result = ''
            for line in lines:
                if ":" in line and "[" in line: # parametric line with test attibutes as well as limits in [ ]
                    name = line.split(":")[0].strip();
                    value = line.split(":")[1].strip().split()[0]; # search in between : and [. then remove units.
                    low_limit = line[(line.index('[')+len('[')):line.index(',')].strip();
                    high_limit = line[(line.index(',')+len(',')):line.index(']')].strip();
                    temp_result = TestResult(name, low_limit, high_limit, unique_id = 1, force_notest=True)
                    temp_result.set_measured_value(value);
                    test_log.add_result(temp_result);              
                elif ":" in line and "[" not in line: # Test result line with test attributes but no limits. (like tester version number)
                    name = line.split(":")[0].strip();
                    value =line.split(":")[1].strip(); # search in between : and [. then remove units.
                    temp_result = TestResult(name);
                    temp_result.set_measured_value(value);
                    test_log.add_result(temp_result);
                else:
                    continue
        else:
            print("DEBUG: IQ does not generate last run result.\n")
        return test_log
    



#NFCC1;PORT:RES TR, XCVR
#NFCC1;CAPT:TIME 0.005
#NFCC1;PROT:LEV:FSTR 6
#NFCC1;INIT:PROT
#NFC
#calc:fstr 0, 1 ##Performs a magnetic field strength measurement
#calc:txq 0, 1 ## Performs a TX quality measurement


def main():
    
    IQ_SESSION = Iqfact()
    IQ_SESSION.parse_iq_log(test_log)


if __name__ == '__main__':
    sys.exit(main())