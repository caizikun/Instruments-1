from .serial import Serial
from time import sleep
import collections

# todo:
# convert the returned list from strings to numbers
# fix voltage conversion

# pylint: disable= W0141, W0110

# provide some enums for callers to use in setRelayState().
KTA_RELAY_STATE_OFF = 'connect_normal_closed'
KTA_RELAY_STATE_ON = 'connect_normal_open'
VOLTS_PER_COUNT = 0.0048875


class KTA223Error(Exception):
    pass


def _cook_output_string(raw_output):
    print(" raw: %s\n" % raw_output)
    tokens = raw_output.split()
    if len(tokens) == 0:
        return ""

    tokens.pop(0)  # just throw away the first token for now.
    if len(tokens) == 1:
        return tokens[0]
    else:
        return tokens


def _state_to_numeric(state):
    if state == KTA_RELAY_STATE_OFF:
        return 0
    if state == KTA_RELAY_STATE_ON:
        return 1
    raise KTA223Error("KTA driver: invalid state sent to stateToNumeric()")


class KTA223(object):
    def __init__(self, port, relay_addresses=None):
        serial_session = None
        if port == "FAKE":
            serial_session = FakeSerial()
        else:
            serial_session = Serial(port, 9600, timeout=0, parity='N', stopbits=1, xonxoff=0, rtscts=0)
            serial_session.timeout = None  # Remove timeout
        self._port = port   # keep this around mostly for telling whether we're in FAKE mode.
        self._serial_session = serial_session
        self._addr = 00  # need to add a setter if we ever want to plug in more than one board to a PC (via USB)
        self._return_raw_string = False    # do we leave the #00 on the lead of every return string?
        self._relay_addresses = relay_addresses  # used for RS-485 addressing over one serial port
        # After a certain point, KTAs started
        sleep(1)
        self._serial_session.flushInput()
        self._show_debug_messages = True

    def enable_debug(self):
        self._show_debug_messages = True

    def debug_print(self, msg):
        if self._show_debug_messages:
            print (msg)

    def send(self, data):
        self.flush_input()
        self._serial_session.write(data)

    def close(self):
        self._serial_session.close()

    def flush_input(self):
        self._serial_session.flushInput()

    # def receive(self, numbytes):
        # ret = bytearray()
        # while len(ret) < numbytes:
            # ret.append(self._ser.read(1))
        # return ret

    def readline(self):
        return self._serial_session.readline()

    def send_command(self, command, parameter, address=None):
        if self._relay_addresses is None:
            data = b'@ %02d %s %d\r' % (self._addr, command, parameter)
        else:
            if address is not None and address in self._relay_addresses:
                data = b'@ %02d %s %d\r' % (address, command, parameter)
            else:
                raise KTA223Error("Sending command to invalid address {0}".format(address))

        self.debug_print("\nSending command [%s" % data)
        self.send(data)
        return self.readline()

    ########################################################
    # High-level commands                                  #
    # These will return the value expected (i.e. 0 or 1 for a digital input channel) #
    ########################################################

    def set_relay_state(self, relay_id, state=KTA_RELAY_STATE_OFF, address=None):
        """
        relayID parameter is channel (1-8) or 'all'
        """
        kta_state_string = 'OF'

        if state == KTA_RELAY_STATE_ON:
            kta_state_string = 'ON'
        return _cook_output_string(self.send_command(kta_state_string, int(relay_id), address))

    def turn_relay_on(self, relay_id, address=None):
        return self.set_relay_state(relay_id, state=KTA_RELAY_STATE_ON, address=address)

    def turn_relay_off(self, relay_id, address=None):
        return self.set_relay_state(relay_id, state=KTA_RELAY_STATE_OFF, address=address)

    def set_relays_as_byte(self, byte, address=None):
        """
        set all relays at once, according to the value of the bit (i.e if bit0 = 0, turn off relay 1.)
        :param byte:
        :param address:
        :return:
        """
        if (byte < 0) or (byte > 255):
            print "Invalid relay value %d" % byte
            return "Error, %s is not a valid byte value." % byte
        # note to future self: noticed on 3/2013 that this isn't wrapped in cookOutputString.
        # I don't think this was intentional, so adding it now.  If you have problems
        # with this function, that may be it.
        #return _cook_output_string(self.send_command('WR', byte, address))
        return self.send_command('WR', byte, address)

    def get_relay_status_byte(self, address=None):
        """returns an integer number between 0 and 255"""
        return _cook_output_string(self.send_command('RS', 0, address))

    def get_relay_status(self, relay_id, address=None):
        return _cook_output_string(self.send_command('RS', int(relay_id), address))

    def get_digital_in_status(self, input_id, address=None):
        """
        returns an integer number between 0 and 15 (only 4 digital inputs)
        """
        if input_id is 'all':
            input_id = 0
        if self._port != "FAKE":
            return _cook_output_string(self.send_command('IS', input_id, address))
        else:
            return ['0', '0', '0', '0']

    def get_analogin_val_count(self, analog_channel, address=None):
        """
        returns the raw value (0-1023) of the A-D converter on a channel
        or a space-separated sequence of values if 'all' channels are desired.
        """
        if analog_channel is 'all':
            analog_channel = 0
        return _cook_output_string(self.send_command('AI', analog_channel, address))

    def get_analogin_val_volts(self, analog_channel, address=None):
        """
        returns the A-D converter (in volts) on a channel
        or a space-separated sequence of values if 'all' channels are desired.
        """
        if analog_channel is 'all':
            analog_channel = 0

        # NOTE: output of cookOutputString comes out here, so
        # make sure to update the parsing/conversion here if that changes.
        value_list = self.get_analogin_val_count(analog_channel, address)
        self.debug_print("INCOMING: %s" % value_list)
        if "FAKE" in value_list:
            return -1.0

        if type(value_list) is str:
            return float(value_list) * VOLTS_PER_COUNT
        else:
            voltslist = []
            for val in value_list:
                voltslist.append(float(val) * VOLTS_PER_COUNT)
            return voltslist

    # Take in a dictionary of (channel_num = "state_string") pairs.
    # Squash that into the current relay state and switch them all at once.
    # Sample dict:
    #   {   1 : KTA_RELAY_STATE_ON,
    #       6 : KTA_RELAY_STATE_OFF,
    #       7 : KTA_RELAY_STATE_OFF }
    # NOTES:
    #   channels are 1-based (not 0-based)
    #   if a channel is not in the dict, it is left at its initial state.
    def set_multiple_relay_values(self, channel_state_dict, address=None):
        byte_val = int(self.get_relay_status_byte())

        for channel_num in channel_state_dict:
            if channel_state_dict[channel_num] is KTA_RELAY_STATE_ON:
                byte_val |= (1 << (channel_num - 1))
            elif channel_state_dict[channel_num] is KTA_RELAY_STATE_OFF:
                byte_val &= (~(1 << (channel_num - 1)))

        #set the relays
        print "Setting relays to %s" % byte_val
        return self.set_relays_as_byte(byte_val, address)

    def set_timed_relay(self, relay_id, time_seconds, address=None):
        """
        turns relay_id ON for time_seconds in resolution of 0.1s
        maximum timer is 25.5 seconds
        :param relay_id:
        :param time_seconds:
        :param address:
        :return:
        """
        if time_seconds > 25.5:
            raise KTA223Error("Cannot set timed relay for longer than 25.5s")
        time_tenths_seconds_string = time_seconds * 10
        # practically duplicating send_command here because of the %03d needed below
        if self._relay_addresses is None:
            data = b'@ %02d %s %d %03d\r' % (self._addr, 'TR', int(relay_id), time_tenths_seconds_string)
        else:
            if address is not None and address in self._relay_addresses:
                data = b'@ %02d %s %d %03d\r' % (address, 'TR', int(relay_id), time_tenths_seconds_string)
            else:
                raise KTA223Error("Sending command to invalid address {0}".format(address))

        self.debug_print("\nSending command [%s" % data)
        self.send(data)
        return self.readline()

    def set_relay_states_from_list(self, state_list, sequential=True):
        """
        :param state_list: list of relay state dictionaries.  dictionary must at least have keys 'address',
         'relay', and 'state'.  If 'state' is 'timed', there is another key 'time_seconds' which contains the time in
         seconds
        :param sequential: if True, the list is executed sequentially.  If false the list is executed in parallel
        :return:
        """
        if sequential is True:
            for state in state_list:
                if state['state'] == 'on':
                    self.turn_relay_on(state['relay'], address=state['address'])
                elif state['state'] == 'off':
                    self.turn_relay_off(state['relay'], address=state['address'])
                elif state['state'] == 'timed':
                    self.set_timed_relay(state['relay'], state['time_seconds'], address=state['address'])
                else:
                    raise KTA223Error("Unknown relay state")
        else:
            relay_states_by_address = collections.defaultdict(list)
            for state in state_list:
                relay_states_by_address[state['address']].append(state)
            for address in relay_states_by_address.keys():
                # Right now this is broken, see pivotal story.
                state_dict = dict(map(lambda x: (x['relay'], KTA_RELAY_STATE_ON) if x['state'] == 'on'
                                      else (x['relay'], KTA_RELAY_STATE_OFF), relay_states_by_address[address]))
                self.set_multiple_relay_values(state_dict, address=address)


class FakeSerial(object):

    def flushInput(self):  # pylint: disable= C0103, R0201
        return 0

    def write(self, data):  # pylint: disable= C0103, R0201
        print "FAKE_KTA: Sending %s" % data

    def readline(self):  # pylint: disable= C0103, R0201
        return "@ FAKE FAKE FAKE"

    def close(self):  # pylint: disable= C0103, R0201
        print "FAKE_KTA: session closed."


if __name__ == '__main__':
    import time
    import sys
    try:
        SESSION = KTA223("FAKE")
        SESSION.enable_debug()
        print ("Relay Status: [%s]" % SESSION.get_relay_status_byte())
        print ("Digital Inputs: [%s]" % SESSION.get_digital_in_status('all'))
        print ("Analog Values: [%s]" % SESSION.get_analogin_val_count('all'))
        print ("Analog Voltages: [%s]" % SESSION.get_analogin_val_volts('all'))
        print ("Single Analog Voltage: [%s]" % SESSION.get_analogin_val_volts(2))
        print ("Single Digital Channel: [%s]" % SESSION.get_digital_in_status(1))

        print SESSION.set_relay_state(1, KTA_RELAY_STATE_ON)
        print SESSION.set_relay_state(1, KTA_RELAY_STATE_OFF)
        print SESSION.turn_relay_on(1)
        print SESSION.turn_relay_off(1)

        print SESSION.set_relays_as_byte(ord('a'))
        print SESSION.set_relays_as_byte(ord('5'))

        time.sleep(1)
        print ("Relay Status: [%s]" % SESSION.get_relay_status_byte())
        print ("Digital Inputs: [%s]" % SESSION.get_digital_in_status('all'))
        print ("Single Digital Input: [%s]" % SESSION.get_digital_in_status(1))
        print ("Analog Values: [%s]" % SESSION.get_analogin_val_count('all'))
        print ("Analog Voltages: [%s]" % SESSION.get_analogin_val_volts('all'))

        # test above, but with Addressing
        EXAMPLE_ADDRESSES = [1, 2]
        SESSION2 = KTA223("FAKE", relay_addresses=EXAMPLE_ADDRESSES)
        SESSION2.enable_debug()

        print ("Relay Status: [%s]" % SESSION2.get_relay_status_byte(address=2))
        print ("Digital Inputs: [%s]" % SESSION2.get_digital_in_status('all', address=2))
        print ("Analog Values: [%s]" % SESSION2.get_analogin_val_count('all', address=2))
        print ("Analog Voltages: [%s]" % SESSION2.get_analogin_val_volts('all', address=2))
        print ("Single Analog Voltage: [%s]" % SESSION2.get_analogin_val_volts(2, address=2))
        print ("Single Digital Channel: [%s]" % SESSION2.get_digital_in_status(1, address=2))

        print SESSION2.set_relay_state(1, KTA_RELAY_STATE_ON, address=2)
        print SESSION2.set_relay_state(1, KTA_RELAY_STATE_OFF, address=2)
        print SESSION2.turn_relay_on(1, address=2)
        print SESSION2.turn_relay_off(1, address=2)
        print SESSION2.set_timed_relay(1, 0.2, address=2)
        print SESSION.set_timed_relay(1, 10)

        print SESSION2.set_relays_as_byte(ord('a'), address=2)
        print SESSION2.set_relays_as_byte(ord('5'), address=2)

        time.sleep(1)
        print ("Relay Status: [%s]" % SESSION2.get_relay_status_byte(address=2))
        print ("Digital Inputs: [%s]" % SESSION2.get_digital_in_status('all', address=2))
        print ("Single Digital Input: [%s]" % SESSION2.get_digital_in_status(1, address=2))
        print ("Analog Values: [%s]" % SESSION2.get_analogin_val_count('all', address=2))
        print ("Analog Voltages: [%s]" % SESSION2.get_analogin_val_volts('all', address=2))
        SESSION2.close()

        #test out polling
        IS_LID_CLOSED = eval(SESSION.get_digital_in_status(1)[0])
        print "Lid status: [%d]" % IS_LID_CLOSED
        while IS_LID_CLOSED == 0:
            time.sleep(1)
            IS_LID_CLOSED = eval(SESSION.get_digital_in_status(1)[0])
            print "Lid status: [%s]" % str(IS_LID_CLOSED)
        SESSION.set_relays_as_byte(00)

        SESSION.close()

    except KeyboardInterrupt as the_exception:
        if SESSION is not None:
            SESSION.close()
        print("Exiting...\n")
        sys.exit(0)
