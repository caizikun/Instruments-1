import pyvisa.visa
import re

# pylint: disable = R0904
# SCPI instruments have lots of methods.... This might be a good global disable for this repo.

DO_DEBUG_PRINT = False

TST_RE = re.compile(r"\+([01]{1})")


class VisaError(Exception):
    pass


class VisaInstrument(object):
    # Class to implement the basics of an instrument.
    # This entails: VISA initialization basics
    # Partial implementation of SCPI core commands.
    # Questions: are no errors the same for all things? Probably can override this with a self._no_error_string, if not
    # Hoisting error checking out of here beyond basic, "did we get a response," until I answer the above
    # There's actually a huge amount we can do here to implement global error checking:
    # http://g2pc1.bu.edu/~qzpeng/gpib/manual/GpibProgTut.pdf page 14.
    # Basically keeping this to sending the core commands and returning the raw response for now.
    # using write/query here instead of write/read since query is used in the SCPI standard.

    def __init__(self, resource_name, term_chars="\n", do_selftest=True, timeout_arg = 5):
        self._instrument = pyvisa.visa.instrument(resource_name, term_chars=term_chars, timeout = timeout_arg)
        # term_chars note:
        #   USB 34972 wants '\n'.  Is NOT happy if left to default of '\r\n'
        #   I put this in here as our default, but we may need to make it a bus-by-bus setting.
        #   (In particular, I read somewhere that serial instruments want \r only...)

        self._no_error_string = "+0,\"No error\"\n"

        if do_selftest:
            if (self.self_test() == "1"):
                raise VisaError("self_test failed")

        # member variables will get filled in when we run IDN.
        self.idn_info = {}
        self.identification_query()

        if DO_DEBUG_PRINT:
            print "IDN"
            print self.idn_info

    ##########################################################################################
    # PYVISA INSTRUMENT INTERFACE
    #
    # Since we can't inherit directly from visa.instrument, we need to re-implement the entire interface.
    #   (Or at least what we care about.)
    # Otherwise, we end up with weird usage where callers sometimes use
    #       visa_instrument.read()
    #  but other times use
    #       visa_instrument._instrument.read_raw()
    #
    # Even internal to our visa_instrument file, these functions should be the only time we
    # reference self._instrument!
    ##########################################################################################
    def read(self):
        try:
            reply = self._instrument.read()
        except pyvisa.visa.VisaIOError as visa_error:
            print "Hit VISA IO Error: {}".format(str(visa_error))
            print "Continuing anyway..."
            reply = ""

        if (reply == ""):
            raise VisaError("No response from instrument")
        return reply

    def write(self, message):
        return self._instrument.write(message)

    def read_raw(self):
        return self._instrument.read_raw()

    def read_values(self):
        return self._instrument.read_values()

    def read_value(self):
        return self._instrument.read_values()[0]

    def ask(self, message):
        return self._instrument.ask(message)

    def ask_for_values(self, message):
        return self._instrument.ask_for_values(message)

    def ask_for_value(self, message):
        return self._instrument.ask_for_values(message)[0]

    def send_command_and_check_error(self, command):
        # method to check for errors after sending command. WILL NOT WORK WITH QUERIES!
        self.write(command)
        result = self.event_status_register_query()
        if result:
            raise VisaError("Error in command:" + command + " error: " + str(result))
        return result

    def clear_status(self):
        return self.send_command_and_check_error("*CLS")

    def clear_error_stack(self):
        error_code = -1
        while error_code < 0:
            error_code, message = self.error_query()
            if DO_DEBUG_PRINT:
                print ("Error: {0} - {1}".format(error_code, message))

    def error_query(self):
        self.write("SYST:ERR?")
        error_message = self.read()
        error_tuple = error_message.split(',')
        return (int(error_tuple[0]), error_tuple[1])

    def event_status_enable_command(self, command=None):
        return self.send_command_and_check_error("*ESE" + command)

    def event_status_enable_query(self):
        self.write("*ESE?")
        return self.read()

    def event_status_register_query(self):
        self.write("*ESR?")
        return int(self.read())

    def identification_query(self):
        self.write("*IDN?")
        raw_idn_response = self.read()

        # IDN reply is comma-separated fields.  Just split on comma.
        idn_fields = raw_idn_response.split(',')
        # member function of the class.  Might as well write directly into our member variables.
        self.idn_info['raw_response'] = raw_idn_response
        self.idn_info['manufacturer'] = idn_fields[0]
        self.idn_info['model'] = idn_fields[1]
        self.idn_info['serial_number'] = idn_fields[2]
        self.idn_info['firmware'] = idn_fields[3]

        return raw_idn_response

    def operation_complete_command(self):
        return self.send_command_and_check_error("*OPC")

    def operation_complete_query(self):
        # reads operation complete bit, set to 1 after OPC is issued and all commands complete.
        # most commands should use this, see linmot for a "query every Xs until complete"
        self.write("*OPC?")
        return self.read()

    def reset(self):
        return self.send_command_and_check_error("*RST")

    def request_enable_command(self):
        # don't totally understand what this register does.
        return self.send_command_and_check_error("*SRE")

    def request_enable_query(self):
        self.write("*SRE?")
        return self.read()

    def status_byte_query(self):
        self.write("*STB?")
        return self.read()

    def self_test(self):
        self.write("*TST?")
        test_return = self.read()
        if DO_DEBUG_PRINT:
            print "test_return: " + test_return
        result = TST_RE.search(test_return).group(1)
        return result

    def wait(self):
        return self.send_command_and_check_error("*WAI")
