import visa_instrument

class PowerSensorError(Exception):
    pass

class KeysightU2001aPowerSensor(visa_instrument.VisaInstrument):

    def __init__(self, resource_name, io_timeout_ms=20000):
        # Keysight U2001a self test takes 40s(!)
        # also it's very slow to respond to some commands (CAL:ALL? being one) so we need a decent timeout
        visa_instrument.VisaInstrument.__init__(self, resource_name, do_selftest=False)
        self._no_error_string = "+0,\"No error\"\n"
        self._instrument.timeout = io_timeout_ms

    def zero_sensor(self, internal_zero=True, auto_cal=False):
        """
        zero the sensor.
        if internal_zero is True, then use internal zeroing, otherwise use external
        if auto_cal is set to True, use the automagic zeroing (can only be used with internal zeroing set to True):
         - if a 5deg C temperature change is detected
         - upon connection to power sensor
         - every 24hours
        """
        if auto_cal and not internal_zero:
            raise PowerSensorError("Auto Calibration must use internal zeroing")
        if not internal_zero:
            self.send_command_and_check_error("CAL:ZERO:TYPE EXT")
        if auto_cal:
            self.send_command_and_check_error("CAL:ZERO:AUTO ON")
        else:
            self.send_command_and_check_error("CAL:ZERO:AUTO ONCE")
        self.write("CAL:ALL?")
        return self.read()

    def trigger_free_run(self):
        """ 
            set the triggering of the power sensor to free run
        """
        self.send_command_and_check_error("INIT:CONT ON")

    def measure_query(self, expected_power=None):
        """
            send measure query SCPI command: MEAS?
        """
        if expected_power is None:
            self.write("MEAS?")
        else:
            self.write("MEAS? {0}".format(expected_power))
        result = self.read()
        return float(result)

