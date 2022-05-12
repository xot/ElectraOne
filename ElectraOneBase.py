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

# Python imports
import time
import sys

# Local imports
from .config import *

def _get_cc_statusbyte(channel):
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

    # flag activating or deactivationg the ElectraOne interface: set when
    # upload thread is started; unset when upload thread finished
    preset_uploading = None

    # flag to inform thread the SysEx ACK message was received
    ack_received = False
    
    def __init__(self, c_instance):
        # c_instance is/should be the object passed by Live when
        # initialising the remote script (see __init.py__). Through
        # c_instance we have access to Live: the log file, the midi map
        # the current song (and through that all devices and mixers)
        self._c_instance = c_instance
        
    # --- helper functions

    def get_c_instance(self):
        """Return a reference to the c_instance passed by Live to
           the remote script.
        """
        return self._c_instance
    
    def song(self):
        """Return a reference to the current song.
        """
        return self._c_instance.song()

    def request_rebuild_midi_map(self):
        """Request that the MIDI map is rebuilt.
           (The old mapping is (apparently) destroyed.)
        """
        self._c_instance.request_rebuild_midi_map()
        
    # --- Sending/writing debug/log messages ---
        
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

    # --- MIDI handling ---
    
    def send_midi(self,message):
        self.debug(3,f'Sending MIDI message (first 10) { message[:10] }')
        self.debug(5,f'Sending MIDI message { message }.') 
        self._c_instance.send_midi(message)

    def send_midi_cc7(self, channel, cc_no, value):
        """Send a 7bit MIDI CC message.
        """
        assert channel in range(1,17), f'CC channel { channel } out of range.'
        assert cc_no in range(128), f'CC no { cc_no } out of range.'
        assert value in range(128), f'CC value { value } out of range.'
        message = (_get_cc_statusbyte(channel), cc_no, value )
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
        message1 = (_get_cc_statusbyte(channel), cc_no, msb)
        message2 = (_get_cc_statusbyte(channel), 0x20 + cc_no, lsb)
        self.send_midi(message1)
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

    # TODO see https://docs.electra.one/developers/midiimplementation.html
    def _select_preset_slot(self,slot):
        self.debug(1,f'Selecting slot {slot}.')
        (bankidx, presetidx) = slot
        assert bankidx in range(6), 'Bank index out of range.'
        assert presetidx in range(12), 'Preset index out of range.'
        sysex_header = (0xF0, 0x00, 0x21, 0x45, 0x09, 0x08)
        sysex_select = (bankidx, presetidx)
        sysex_close = (0xF7, )
        self.send_midi(sysex_header + sysex_select + sysex_close)
  
    # see https://docs.electra.one/developers/midiimplementation.html#upload-a-preset
    def _upload_preset_to_current_slot(self,preset):
        self.debug(1,'Uploading preset.')
        sysex_header = (0xF0, 0x00, 0x21, 0x45, 0x01, 0x01)
        sysex_preset = tuple([ ord(c) for c in preset ])
        sysex_close = (0xF7, )
        if not DUMP: # no need to write this to the log if the same thing is dumped
            self.debug(4,f'Preset = { preset }')
        self.send_midi(sysex_header + sysex_preset + sysex_close)
        
    # preset is the json preset as a string
    def upload_preset(self,slot,preset):
        """To be called as a thread. Select a slot and upload a preset. In both
           cases wait (within a timeout) for confirmation from the E1.
           Reactivate the interface when done.
           (self is a reference to the calling EffectController object)
        """
        # should anything happen inside this thread, make sure we write to debug
        try:
            # first select slot and wait for ACK
            ElectraOneBase.ack_received = False
            self._select_preset_slot(slot)
            # wait until _do_ack() called or timeout after 1 second
            timeout = 10
            self.debug(3,f'Upload thread setting slot selection timeout {timeout} (pu: {ElectraOneBase.preset_uploading}).')
            while (not ElectraOneBase.ack_received) and (timeout > 0):
                time.sleep(0.1)
                self.debug(5,f'Upload thread waiting for ACK, timeout {timeout}.')
                timeout -= 1
            self.debug(3,f'Upload thread: slot selection finished after timeout {timeout} (pu: {ElectraOneBase.preset_uploading}).')
            if timeout > 0:
                # slot selected, now upload preset and wait for ACK
                ElectraOneBase.ack_received = False
                self._upload_preset_to_current_slot(preset)
                # wait until _do_ack() called or timeout (depending on patch complexity)
                timeout = int(len(preset)/100)
                self.debug(3,f'Upload thread setting upload timeout { timeout } seconds. (pu: {ElectraOneBase.preset_uploading})')
                while (not ElectraOneBase.ack_received) and (timeout > 0):
                    time.sleep(0.1)
                    self.debug(5,f'Upload thread waiting for ACK, timeout {timeout}.')
                    timeout -= 1
                self.debug(3,f'Upload thread: preset upload finished after timeout {timeout}. (pu: {ElectraOneBase.preset_uploading})')
                # re-open the interface
                ElectraOneBase.preset_uploading = False
                # rebuild midi map (will also refresh state) (this is why interface needs to be reactivated first ;-)
                self.debug(2,'Upload thread requesting MIDI map to be rebuilt.')
                self.request_rebuild_midi_map()                
                self.debug(2,'Upload thread done.')
        except:
            ElectraOneBase.preset_uploading = False
            self.debug(1,f'Exception occured {sys.exc_info()}')
        
