import visa_instrument

# pylint: disable=R0904
# >20 Public methods for a Power Supply seems reasonable.


class PowerSupplyError(Exception):
    pass

# Note: all 364x power supplies have 2 ranges.
# Either of those ranges can be applied to all of each models's output channels.
MODEL_DEFINITIONS = {
    'e3640a': {
        'num_output_channels': 1,
        'ranges': {
            'P8V': {    # Range names come from the SCPI command.
                'max_volts': 8,
                'max_amps': 3
            },
            'P20V': {
                'max_volts': 20,
                'max_amps': 1.5
            }
        }
    },
    'e3646a': {
        'num_output_channels': 2,
        'ranges': {
            'P8V': {
                'max_volts': 8,
                'max_amps': 3
            },
            'P20V': {
                'max_volts': 20,
                'max_amps': 1.5
            }
        }
    },
    'e3648a': {
        'num_output_channels': 2,
        'ranges': {
            'P8V': {
                'max_volts': 8,
                'max_amps': 5
            },
            'P20V': {
                'max_volts': 20,
                'max_amps': 2.5
            }
        }
    },
    'e3633a': {  # Note: 3633a supports same basic commands as 364x.
                 # Has an extra CURRent:PROTection command family.
                 # Does not support the communicate:gpib... commands.
        'num_output_channels': 1,
        'ranges': {
            'P8V': {    # Range names come from the SCPI command.
                'max_volts': 8,
                'max_amps': 20
            },
            'P20V': {
                'max_volts': 20,
                'max_amps': 10
            }
        }
    }
}


class AgilentE36xxPowerSupply(visa_instrument.VisaInstrument):
    # So far, e36xx family seems to support same basic (VOLT/CURR/OUTP/MEAS) commands.
    # [based on e3646, e3640, e3633]
    # Some model-to-model variation in more-advanced functions.

    def __init__(self, resourceName, model='e3640a', do_selftest=True):
        if model.lower() not in MODEL_DEFINITIONS:
            raise PowerSupplyError("Unsupported model [{0}]".format(model))
        visa_instrument.VisaInstrument.__init__(self, resourceName, do_selftest=do_selftest)
        self._no_error_string = "+0,\"No error\"\n"
        self._model = model
        self._num_output_channels = MODEL_DEFINITIONS[model]['num_output_channels']
        self._ranges = MODEL_DEFINITIONS[model]['ranges']

    # enable callers to ask us what we're initialized to.
    def get_model(self):
        return self._model

    def select_output_channel(self, channel=1):
        # Is this a valid channel for our model?
        if channel < 1 or channel > self._num_output_channels:
            raise PowerSupplyError("Channel {0} is not supported by this model.".format(channel))

        # Does our model even have more than one channel?  (Skip the SCPI command if not.)
        if self._num_output_channels > 1:
            self.send_command_and_check_error("INST:SEL OUT" + str(channel))

    def set_voltage(self, voltage):
        self.send_command_and_check_error("VOLT " + str(voltage))

    def set_current_limit(self, current_limit):
        if current_limit is not None:
            self.send_command_and_check_error("CURR " + str(current_limit))

    def output_on(self):
        self.send_command_and_check_error("OUTP ON")

    def output_off(self):
        self.send_command_and_check_error("OUTP OFF")

    def set_range(self, desired_range="DEFAULT"):
        if desired_range not in self._ranges and desired_range not in ['DEFAULT', 'LOW', 'HIGH']:
            raise PowerSupplyError("Range {0} is not supported by this model.".format(desired_range))
        self.send_command_and_check_error("SOUR:VOLT:RANG " + str(desired_range))

    def measure_current(self):
        return self.ask_for_value("MEAS:CURR?")

    def measure_voltage(self):
        return self.ask_for_value("MEAS:VOLT?")

    def display_off(self):
        self.send_command_and_check_error("DISP:STAT OFF")

    def display_on(self):
        self.send_command_and_check_error("DISP:STAT ON")

    def beep(self):
        self.send_command_and_check_error("SYST:BEEP:IMM")

    def configure_and_enable_output(self, voltage, current_limit=None, channel=1):
        '''Equivalent to OutputOnAt#v#.txt and Agilent3646_ChX_OutputOnAt#V#.txt
        '''
        self.select_output_channel(channel)
        self.set_current_limit(current_limit)
        self.set_voltage(voltage)
        self.output_on()
        return self.measure_voltage()
