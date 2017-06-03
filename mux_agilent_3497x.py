import visa_instrument

# pylint: disable = R0904
# mux's do lots of things

# pylint: disable = C0103
# Temporarily disabling for wip code.

# Placeholders for later.  Maybe we can search list of visa instruments for USB0::0x0957::0x2007...
USB_VID = '0x0957'
USB_PID = '0x2007'


# should these be class member constants?
# Range always also accepts "MIN", "MAX", "DEF", and "AUTO", but we probably don't want to use these.  Keep it explicit.

MEASUREMENT_CONFIGURATIONS = {
    'current': {
        'scpi_mnemonic': "CURR",
        'valid_range_strings': ("0.01", "0.1", "1"),
        'valid_measurement_subtypes': ('DC', 'AC')
    },
    'voltage': {
        'scpi_mnemonic': "VOLT",
        #Note: documentation on CONF command says basically "pick whatever you want" for VOLT and RES ranges
        # but elsewhere in the doc (specifically SENS:FREQ:VOLT:RANGE), it's listed as being discreet.
        'valid_range_strings': ("0.1", "1", "10", "100", "1000"),
        'valid_measurement_subtypes': ('DC', 'AC')
    },
    'resistance': {
        'scpi_mnemonic': "RES",
        #Note: documentation on CONF command says basically "pick whatever you want" for VOLT and RES ranges
        # but elsewhere in the doc (specifically SENS:FREQ:VOLT:RANGE), it's listed as being discreet.
        'valid_range_strings': ("100", "1000", "10000", "100000", "1000000", "10000000", "100000000"),  # 10E+2 to 10E+8
        'valid_measurement_subtypes': (None)
    },
    'frequency': {
        'scpi_mnemonic': "FREQ",
        'valid_range_strings': ("3", "30", "300", "3000", "30000", "300000"),  # 3Hz to 300 kHz
        #VALID_PERIOD_RANGE_STRINGS= # per documentation: 1/VALID_HZ_RANGE_STRING
        'valid_measurement_subtypes': (None)
    }
    # later: 4-wire resistance FRES, temperature TEMP, period PER, digital:byte DIG:BYTE, totalize TOT
}

# General 3497x useage notes:
# Does this belong in this driver? a readme.md for this driver? the global readme.md? (I'm happy it exists!)
#
#   Fully discreet measurement sequence:
#       CONF:[...]      setup certain channels for the type of measurement you want to do.
#                       Note: CONF resets all measurement config params to default, so do this before a SENS.
#       (SENS:[...]     (optional) more granular config control over how measurements are performed.)
#       ROUT:SCAN       select list of channels to be included in the scan
#       (TRIG:[...]     (optional) Configure to run scan more than once, specify delay between scans, etc)
#       INIT            wait-for-trigger, scan once (or as specified by TRIG), load into memory
#       FETC?           pull from memory into IO buffer
#
#   Shortcuts:
#       READ?
#       -> is same as:
#           (TRIG is forced to defaults: only one scan, no delay)
#           INIT
#           FETC?
#       MEAS:[...]?
#       -> is same as:
#           CONF:[...]
#           (scan list is set to list you passed in)
#           READ?
#
# RANGES:
#   DO NOT USE AUTORANGING IN MFG TEST.  EVER!
#
#   voltage, frequency, period and resistance can all be any value ("enter your expected value")
#   BUT... make sure it's greater than your measurement:
#   If the measurement goes over your range, you'll get an
#       OVLD (on the display) or an
#       +/-9.9E+37 (on the remote interface).


class MuxError(Exception):
    pass
    #should this raise the general error somehow?


class InvalidArgException(ValueError):
    pass


DO_DEBUG_PRINT = True
DO_SELFTEST = True


class Agilent34970Mux(visa_instrument.VisaInstrument):

    def __init__(self, resourceName):
        if DO_SELFTEST:
            visa_instrument.VisaInstrument.__init__(self, resourceName, do_selftest=True, timeout_arg=18)
        else:
            visa_instrument.VisaInstrument.__init__(self, resourceName, do_selftest=False)
        #make dmm chassis aware of which cards it has in which slots.
        self._card_info = {}
        for slot in ("100", "200", "300"):
            self._card_info[slot] = self.query_card_type(slot)
            if DO_DEBUG_PRINT:
                print "\nSlot {0}:".format(slot)
                print self._card_info[slot]

    #####################################################################
    # Utility functions
    #####################################################################

    @classmethod
    def _validate_measurement_parameters(cls, measurement_type, measurement_range_string, measurement_subtype):
        '''Use this for CONF and MEAS.  Logic is the same.
        '''
        if measurement_type not in MEASUREMENT_CONFIGURATIONS:
            raise MuxError("{0} is not a valid mesurement type.".format(measurement_type))
        if measurement_range_string not in MEASUREMENT_CONFIGURATIONS[measurement_type]['valid_range_strings']:
            raise MuxError("{0} is not a valid range for this measurement type.".format(measurement_range_string))
        if measurement_subtype not in MEASUREMENT_CONFIGURATIONS[measurement_type]['valid_measurement_subtypes']:
            raise MuxError("{0} is not a valid subtype for {1} measurements.".format(measurement_subtype, measurement_type))

    # Channel list handling: Start Small with just a raw python list of channels.
    # Maybe later get smart about ranges and other fancy-ness that the instrument allows.
    @classmethod
    def convert_python_list_to_channel_list_string(cls, channels_list):
        liststring = ','.join(channels_list)
        return "(@{0})".format(liststring)

    # Take in string or numeric slot number, either 1 or 100.
    # Return the string-ified version of the hundreds.  (This is the convention Agilent uses in their docs.)
    @classmethod
    def _normalize_slot_num(cls, slot_num):
        numeric_slot_num = int(slot_num)
        if numeric_slot_num not in (1, 2, 3, 100, 200, 300):
            raise InvalidArgException("Slot [{0}] is not a valid slot number.".format(slot_num))
        if numeric_slot_num in (1, 2, 3):
            numeric_slot_num *= 100
        return str(numeric_slot_num)

    def query_card_type(self, slot_num):
        raw_card_info = self.ask("SYST:CTYP? {0}".format(self._normalize_slot_num(slot_num)))
        card_info_fields = raw_card_info.split(',')
        #<Company Name>,<Card Model Number>,<Serial Number>,<Firmware Rev>
        card_info = {}
        card_info["manufacturer"] = card_info_fields[0]
        card_info["model"] = card_info_fields[1]
        card_info["serial_number"] = card_info_fields[2]
        card_info["firmware_rev"] = card_info_fields[3]
        card_info["raw_info_string"] = raw_card_info
        return card_info

    #####################################################################
    # MEAS is a standard flow for taking a straightforward mesurement on one or more channels.
    # Should apply to 99% of our needs.
    #####################################################################

    def measure(self, measurement_type, channel_list_string, measurement_range_string, measurement_subtype=None):

        self._validate_measurement_parameters(measurement_type, measurement_range_string, measurement_subtype)

        # base string
        scpi_command_string = ("MEAS:{0}".format(MEASUREMENT_CONFIGURATIONS[measurement_type]['scpi_mnemonic']))
        # subtype may or may not be needed, depending on measurement_type
        if measurement_subtype is not None:
            scpi_command_string = scpi_command_string + ":{0}".format(measurement_subtype)
        scpi_command_string = scpi_command_string + '?'  # unlike CONF, MEAS needs the question mark before the args.
        # range is optional according to instrument, but not optional for mfg test!
        scpi_command_string = scpi_command_string + " {0}".format(measurement_range_string)  # leading space is important!
        # omitted resolution means fall back to default for your measurement type.
        # NOTE for future reference: if adding the resolution, need comma before and after:   range,RES, (@channels)
        scpi_command_string = scpi_command_string + " " + channel_list_string

        # remember that this is a list.
        return self.ask_for_values(scpi_command_string)

    #####################################################################
    # Functions to enable more-granular control of the measurement.
    #####################################################################

    # DO NOT ALLOW range TO HAVE A DEFAULT OR None VALUE.  Force callers to think about it.
    # Also note: intentionally omitting resolution paramater for now.  Always use default.
    #   Once we have a good reason to use it, we can add it in with a default value of 'default' to keep the interface
    #   backwards-compatible
    def configure_measurement(self, measurement_type, channel_list_string, measurement_range_string, measurement_subtype=None):

        self._validate_measurement_parameters(measurement_type, measurement_range_string, measurement_subtype)

        # base string
        scpi_command_string = ("CONF:{0}".format(MEASUREMENT_CONFIGURATIONS[measurement_type]['scpi_mnemonic']))
        # subtype may or may not be needed, depending on measurement_type
        if measurement_subtype is not None:
            scpi_command_string = scpi_command_string + ":{0}".format(measurement_subtype)
        # range is optional according to instrument, but not optional for mfg test!
        scpi_command_string = scpi_command_string + " {0}".format(measurement_range_string)  # leading space is important!
        # omitted resolution means fall back to default for your measurement type.
        # NOTE for future reference: if adding the resolution, need comma before and after:   range,RES, (@channels)
        scpi_command_string = scpi_command_string + ",DEF,(@" + channel_list_string + ")"

        return self.write(scpi_command_string)

    def set_scan_list(self, channel_list_string):
        return self.write("ROUT:SCAN (@{0})".format(channel_list_string))

    def read_readings(self):  # read() and read_values() already in use.  fetch_readings() implies the "FETCH?" query.
        return self.ask_for_values("READ?")

    def read_one_reading(self):
        self.write("READ?")
        reading = self.read()
        float_reading = float(reading)
        return float_reading
    

def main():
    id = 'MUX'
    instr = Agilent34970Mux(id)
    print instr.identification_query()
    
    measurement_type = 'voltage'
    measurement_range_string = '10'
    measurement_subtype = 'DC'
    channel_list_string = '214'
    instr.configure_measurement(measurement_type, channel_list_string, measurement_range_string, measurement_subtype)
    instr.set_scan_list(channel_list_string)
    voltage = instr.read_one_reading()
    print type(voltage)
    print voltage

    measurement_type = 'current'
    measurement_range_string = '0.1'
    measurement_subtype = 'DC'
    channel_list_string = '121'
    instr.configure_measurement(measurement_type, channel_list_string, measurement_range_string, measurement_subtype)
    instr.set_scan_list(channel_list_string)
    current = instr.read_one_reading()
    print type(current)
    print current

if __name__ == '__main__':
    main()
