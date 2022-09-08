# CCInfo
# - class to store information about a CC control (channel,is_cc14,cc_no)
#
# Part of ElectraOne.
#
# Ableton Live MIDI Remote Script for the Electra One
#
# Author: Jaap-henk Hoepman (info@xot.nl)
#
# Distributed under the MIT License, see LICENSE

# dummy CC parameter value to indicate an unmapped CC
UNMAPPED_CC = -1

IS_CC7 = False
IS_CC14 = True

class CCInfo:
    """Class storing the channel and parameter number of a CC mapping, and
       whether the associated controller on the E1 is 14bit (or not, in
       which case it is 7bit).
    """

    def __init__(self, v):
        """Initialise with a tuple (MIDI_channel, is_cc14?, CC_parameter_no).
           Where is_cc14? is IS_CC7 when the parameter is 7bit, IS_CC14 if 14bit.
           Constructing from a tuple instead of a list of parameters, to allow
           Devices.py to contain plain tuples in the cc_map.
        """
        assert type(v) is tuple, f'{v} should be tuple but is {type(v)}'
        (self._midi_channel, self._is_cc14, self._cc_no) = v
        assert self._midi_channel in range(1,17), f'MIDI channel {self._midi_channel} out of range.'
        assert self._is_cc14 in [IS_CC7,IS_CC14], f'CC14 flag {self._is_cc14} out of range.'
        assert self._cc_no in range(-1,128), f'MIDI channel {self._cc_no} out of range.'
        
    def __repr__(self):
        return f'({self._midi_channel},{self._is_cc14},{self._cc_no})'
        
    def get_midi_channel(self):
        """Return the MIDI channel this object is mapped to (undefined if not mapped)
           - result: channel; int (1..16)
        """
        return self._midi_channel

    def is_cc14(self):
        """Return whether the object represents a 7 or 14 bit CC parameter 
           (undefiend when not mapped).
           - result: IC_CC14/True if 14 bit; ID_CC7/False if 7 bit;  bool
        """
        return self._is_cc14

    def get_cc_no(self):
        """Return the CC parameter number of this object.
           - result: the CC parameter number (-1 if not mapped); int (-1..127)
        """
        return self._cc_no

    def is_mapped(self):
        """Return whether object is mapped to a CC parameter at all.
           - result: whether mapped or not ; bool
        """
        return self._cc_no != UNMAPPED_CC
    


