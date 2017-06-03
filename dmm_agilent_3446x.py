import visa_instrument

# pylint: disable=R0904
# >20 Public methods for a DMM seems reasonable.

ERROR_BIT = 0b10000000


class DMMError(Exception):
    pass
    #should this raise the general error somehow?


class Agilent34461DMM(visa_instrument.VisaInstrument):
    #  Here this would extend a generic power supply class
    #  How do I implement different limits for a family? Perhaps:
    #  generic power supply class defines functions a supply
    #  must have, implementation by family. Dictionary for limits for each
    #  model within family? Writing for only 3640,
    #  so changing class name to reflect this
    #  Discovery of instruments is possible, but probably out of scope
    #  since we will often have two.

    # Possible dmm measurement functions
    CAPACITANCE = "CAPacitance"
    CONTINUITY = "CONTinuity"
    CURRENT_AC = "CURRent:AC"
    CURRENT_DC = "CURRent:DC"
    DIODE = "DIODe"
    FREQUENCY = "FREQuency"
    FRESISTANCE = "FRESistance"
    PERIOD = "PERiod"
    RESISTANCE = "RESistance"
    TEMPERATURE = "TEMPerature"
    VOLTAGE_AC = "VOLTage:AC"
    VOLTAGE_DC = "VOLTage:DC"

    def __init__(self, resourceName, do_selftest=True):
        visa_instrument.VisaInstrument.__init__(self, resourceName, do_selftest=do_selftest)
        self._no_error_string = "+0,\"No error\"\n"

    @classmethod
    def _check_channel(cls, channel):
        if (channel not in [None, 1]):
            raise DMMError("Unsupported Channel")

    def measure_current(self, channel=None):
        self._check_channel(channel)
        return self.ask_for_value("MEAS:CURR?")

    def measure_voltage(self, channel=None):
        self._check_channel(channel)
        return self.ask_for_value("MEAS:VOLT?")

    def set_range(self, desired_range):
        self.send_command_and_check_error("VOLT:RANG " + str(desired_range))

    def set_current_range(self, desired_range):
        self.send_command_and_check_error("CURR:RANG " + str(desired_range))    # Define current range

    def set_measurement_func(self, measurement_function):
        self.send_command_and_check_error("FUNC \"" + measurement_function + "\"")  # Set the measurement function

    def start_logging(self, trigger_delay, sample_count, sample_interval):
        self.send_command_and_check_error("DATA:DEL NVMEM")                     # Clear data from non-volatile memory
        self.send_command_and_check_error("TRIG:DEL " + str(trigger_delay))     # Set trigger delay
        self.send_command_and_check_error("SAMP:COUN " + str(sample_count))     # Set the number sameples
        self.send_command_and_check_error("SAMP:SOUR TIM")                      # Set source of sample trigger as timer
        self.send_command_and_check_error("SAMP:TIM " + str(sample_interval))   # Set timer trigger interval
        self.send_command_and_check_error("INIT")                               # Start measurement

    def fetch_data_points_and_clear(self):
        data_point_count = self.ask_for_value("DATA:POIN?")               # Get the number of data points avaiable
        return self.ask_for_values("DATA:REM? " + str(data_point_count))  # Fetch all data points and remove

    def abort(self):
        self.send_command_and_check_error("ABOR")                               # Abort previous operation
