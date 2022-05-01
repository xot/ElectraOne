# ElectraOneBase
# - Base class with common functions
#
# Part of ElectraOne
#
# Ableton Live MIDI Remote Script for the Electra One
#
# Author: Jaap-henk Hoepman (info@xot.nl)
#
# Distributed under the MIT License, see LICENSE
#

# Local imports
from .config import *

def get_cc_statusbyte(channel):
    # status byte encodes midi channel (-1!) in the least significant nibble
    CC_STATUS = 176
    return CC_STATUS + channel - 1

# quantized parameters have a list of values. For such a list with
# n items, item i (staring at 0) has MIDI CC control value
# round(i * 127/(n-1)) 
def cc_value_for_item_idx(idx,items):
    return round( idx * (127 / (len(items)-1) ) )

class ElectraOneBase:
    """E1 base class with common functions
       (interfacing with Live through c_instance).
    """

    def __init__(self, c_instance):
        # c_instance is/should be the object passed by Live when
        # initialising the remote script (see __init.py__). Through
        # c_instance we have access to Live: the log file, the midi map
        # the current song (and through that all devices and mixers)
        self._c_instance = c_instance

    def debug(self,level,m):
        """Write a debug message to the log, if level < DEBUG.
        """
        if level < DEBUG:
            self._c_instance.log_message(f'E1 (debug): {m}')

    def log_message(self,m):
        self._c_instance.log_message(f'E1 (log): {m}')

    def show_message(self,m):
        """Show a message in the Live message line (lower left corner).
        """
        self._c_instance.show_message(m)

    def send_midi(self,message):
        self._c_instance.send_midi(message)

    def send_midi_cc7(self, channel, cc_no, value):
        """Send a 7bit MIDI CC message.
        """
        assert channel in range(1,17), f'CC channel { channel } out of range.'
        assert cc_no in range(128), f'CC no { cc_no } out of range.'
        assert value in range(128), f'CC value { value } out of range.'
        message = (get_cc_statusbyte(channel), cc_no, value )
        self.debug(4,f'MIDI message {message}.')
        self.send_midi(message)

    def send_midi_cc14(self, channel, cc_no, value):
        """Send a 14bit MIDI CC message.
        """
        assert channel in range(1,17), f'CC channel { channel } out of range.'
        assert cc_no in range(128), f'CC no { cc_no } out of range.'
        assert value in range(16384), f'CC value { value } out of range.'
        lsb = value % 128
        msb = value // 128
        # a 14bit MIDI CC message is actually split into two messages:
        # one for the MSB and another for the LSB; the second uses cc_no+32
        message1 = (get_cc_statusbyte(channel), cc_no, msb)
        message2 = (get_cc_statusbyte(channel), 0x20 + cc_no, lsb)
        self.debug(4,f'MIDI message {message1}.')
        self.send_midi(message1)
        self.debug(4,f'MIDI message {message2}.')
        self.send_midi(message2)

    def send_parameter_as_cc14(self, p, channel, cc_no):
        """Send the value of a Live parameter as a 14bit MIDI CC message.
        """
        self.debug(4,f'Sending value for {p.original_name} over MIDI channel {channel} as CC parameter {cc_no} in 14bit.')
        value = int(16383 * ((p.value - p.min) / (p.max - p.min)))
        self.send_midi_cc14(channel, cc_no, value)

    def send_parameter_as_cc7(self, p, channel, cc_no):
        """Send the value of a Live parameter as a 7bit MIDI CC message.
        """
        self.debug(4,f'Sending value for {p.original_name} over MIDI channel {channel} as CC parameter {cc_no} in 7bit.')
        if p.is_quantized:
            idx = int(p.value)
            value = cc_value_for_item_idx(idx,p.value_items)
        else:
            value = int(127 * ((p.value - p.min) / (p.max - p.min)))
        self.send_midi_cc7(channel, cc_no, value)

    def send_parameter_using_ccinfo(self, p, ccinfo):
        """Send the value of Live a parameter as a MIDI CC message
           (using CC info to determine where and how).
        """
        self.debug(3,f'Sending value for {p.original_name} over {ccinfo}.')
        channel = ccinfo.get_midi_channel()
        cc_no = ccinfo.get_cc_no()
        if ccinfo.is_cc14():
            self.send_parameter_as_cc14(p, channel, cc_no)
        else:
            self.send_parameter_as_cc7(p, channel, cc_no)                
        
    def song(self):
        """Return a reference to the current song.
        """
        return self._c_instance.song()

    def request_rebuild_midi_map(self):
        """Request that the MIDI map is rebuilt.
           (The old mapping is (apparently) destroyed.)
        """
        self._c_instance.request_rebuild_midi_map()

