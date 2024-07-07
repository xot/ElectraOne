# E1Midi
# - E1 Midi definitions and functions
#
# Part of ElectraOne
#
# Ableton Live MIDI Remote Script for the Electra One
#
# Author: Jaap-henk Hoepman (info@xot.nl)
#
# Distributed under the MIT License, see LICENSE
#

# CC status nibble
CC_STATUS = 0xB0

# All SysEx commands start with E1_SYSEX_PREFIX
# and are terminated by SYSEX_TERMINATE
E1_SYSEX_PREFIX = (0xF0, 0x00, 0x21, 0x45)
SYSEX_TERMINATE = (0xF7, )

# SysEx incoming commands (as defined by the E1 firmware)
E1_SYSEX_LOGMESSAGE = (0x7F, 0x00) # followed by json data 
E1_SYSEX_PRESET_CHANGED = (0x7E, 0x02)  # followed by bank-number slot-number
E1_SYSEX_ACK = (0x7E, 0x01) # followed by two zero's (reserved) 
E1_SYSEX_NACK = (0x7E, 0x00) # followed by two zero's (reserved)
E1_SYSEX_REQUEST_RESPONSE = (0x01, 0x7F) # followed by json data 
E1_SYSEX_PRESET_LIST_CHANGE = (0x7E, 0x05)

# SysEx incomming command when the PATCH REQUEST button on the E1 has been pressed 
# (User-defined in effect patch LUA script, see DEFAULT_LUASCRIPT in EffectController.py)
E1_SYSEX_PATCH_REQUEST_PRESSED = (0x7E, 0x7E) # no data

# --- General

def hexify(midimsg):
    """Convert the sequence of (MIDI) bytes into a hexadecimal string
       - midimsg: sequence; (byte)
       - result: str
    """
    bytes_as_str = [ f'0x{b:02X}' for b in midimsg ]
    return " ".join(bytes_as_str)

# --- SysEx

def is_E1_sysex(midimsg):
    """Test whether MIDI message is a E1 SysEx.
    - midimsg: MIDI message; (byte)
    - result: bool
    """ 
    return midimsg[0:4] == E1_SYSEX_PREFIX

def parse_E1_sysex(midimsg):
    """Return command and data from a E1 SysEx message.
    - midimsg: MIDI message; (byte)
    - result: tuple (command, data)
    """ 
    assert is_E1_sysex(midimsg), f'Error: {midimsg} is not an E1 SysEx'
    return ( midimsg[4:6], midimsg[6:-1] ) # all bytes after the command, except the terminator byte 

def make_E1_sysex(command, data):
    """Create a E1 SysEx for command and its data.
    - command: sequence of command bytes (each < 128); (byte)
    - data: sequence of command data (each < 128); (byte)
    - return: SysEx message; sequence of bytes
    """
    assert len(command) == 2, f'SysEx command {command} has wrong length'
    # we do not test bytes in command and data; we let Ableton detect and
    # report any issues (there shouldn't be any)
    return E1_SYSEX_PREFIX + command + data + SYSEX_TERMINATE

# --- CC

def is_cc(midimsg):
    """Test whether MIDI message is a CC message.
    - midimsg: MIDI message; (byte)
    - result: bool
    """
    return (len(midimsg) == 3) and ((midimsg[0] & 0xF0) == CC_STATUS)
    
def parse_cc(midimsg):
    """Return channel, cc_no and value from a CC message.
    - midimsg: MIDI message; (byte)
    - result: typle (channel, cc_no, cc_value)
    """ 
    assert is_cc(midimsg), f'Error: {midimsg} is not a CC'
    channel = (midimsg[0] & 0x0F) + 1 # we number MIDI channels 1..16
    assert channel in range(1,17), f'MIDI channel {channel} out of range.'
    return (channel, midimsg[1], midimsg[2])
    
def make_cc(channel, cc_no, cc_value):
    """Create a CC message on a channel for command and its data.
    - channel: byte
    - cc_no: byte
    - cc_value: byte
    - return: CC message; sequence of 3 bytes
    """
    assert channel in range(1,17), f'MIDI channel {channel} out of range.'
    assert cc_no in range(128), f'CC no { cc_no } out of range.'
    assert cc_value in range(128), f'CC value { cc_value } out of range.'
    return ( CC_STATUS + channel - 1 , cc_no, cc_value )

def cc_value(v,ccmax,vmin,vmax):
    """Return the CC encoding of the value v known to be in the
       range (vmin,vmax) in the CC range (0,ccmax).
    - v: value, float
    - ccmax: max CC value, int (127 or 16383)
    - vmin,vmax: range for v, both floats
    - return: int (0..ccmax)
    """
    assert (v >= vmin) and (v <= vmax), f'Value {v} our of range {vmin}..{vmax}'
    return round( ccmax * ((v - vmin) / (vmax - vmin)))

def cc7_value(v,vmin,vmax):
    """Return the 7bit CC encoding of the value v known to be in the
       range (vmin,vmax).
    - v: value, float
    - vmin,vmax: range for v, both floats
    - return: int (0..127)
    """
    return cc_value(v,127,vmin,vmax)

def cc7_value_for_item_idx(idx,items):
    """Return the 7bit CC encoding of the index in a list of items
    - idx: index in the list of items; int
    - items: list of items; list
    - return: int (0..127)
    """
    return cc7_value(idx,0,len(items)-1)

def cc7_value_for_par(p):
    """Return the 7bit CC encoding of the value for a parameter.
    - p: Ableton Live parameter; Live.DeviceParameter.DeviceParameter
    - return: int (0..127)
    """
    return cc7_value(p.value,p.min,p.max)

def cc14_value(v,vmin,vmax):
    """Return the 14bit CC encoding of the value v known to be in the
       range (vmin,vmax).
    - v: value, float
    - vmin,vmax: range for v, both floats
    - return: int (0..16383)
    """
    return cc_value(v,16383,vmin,vmax)

def cc14_value_for_par(p):
    """Return the 14bit CC encoding of the value for a parameter.
    - p: Ableton Live parameter; Live.DeviceParameter.DeviceParameter
    - return: int (0..16383)
    """
    return cc14_value(p.value,p.min,p.max)

