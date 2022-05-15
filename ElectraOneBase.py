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
import threading
import time
import sys
import os

# Local imports
from .config import *

DEFAULT_LUASCRIPT = 'function patch.onRequest (device) \n print ("Patch Request pressed"); \n midi.sendSysex(PORT_1, {0x00, 0x21, 0x45, 0x7E, 0x02, 5, 10}) \n end'

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

    # flag activating or deactivating the ElectraOne interface: set when
    # upload thread is started; unset when upload thread finished. Checked
    # by _is_ready()
    preset_uploading = None

    # flag to inform the upload thread that a SysEx ACK message was received
    ack_received = False

    # slot currently visibile on the E1; used to prevent unneccessary
    # refresh_state for invisible presets
    current_visible_slot = (0,0)
    
    def __init__(self, c_instance):
        # c_instance is/should be the object passed by Live when
        # initialising the remote script (see __init.py__). Through
        # c_instance we have access to Live: the log file, the midi map
        # the current song (and through that all devices and mixers)
        self._c_instance = c_instance
        # find sendmidi, and test if it works
        self._sendmidi_cmd = self._find_in_libdir(SENDMIDI_CMD)
        if self._sendmidi_cmd:
            self._sysex_fast = USE_FAST_SYSEX_UPLOAD  and self._test_sendmidi()
        else:
            self._sysex_fast = False
        if self._sysex_fast:
            self.debug(1,'Fast uploading of presets supported. Great, using that!')
        else:
            self.debug(1,'Fast uploading of presets not supported, reverting to slow method.')
        
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

    def _find_libdir(self,path):
        """ Determine library path based on LIBDIR. Either ~/LIBDIR or LIBDIR
            followed by path, or ~, the first of these that exist.
        """
        home = os.path.expanduser('~')
        test =  f'{ home }/{ LOCALDIR }{ path }'
        self.debug(4,f'Testing library path {test}')
        if not os.path.exists(test):                                        # try LOCALDIR as absolute directory
            test =  f'{ LOCALDIR }{ path }'
            self.debug(4,f'Testing library path {test}')
            if not os.path.exists(test):                                        # default is HOME
                test = home
        return test
        
    def _find_in_libdir(self,path):
        """Find path in library path and return it if found,
           else return None
        """
        root = self._find_libdir('')
        test = f'{ root }/{ path }'
        if not os.path.exists(test):
            self.debug(4,f'Path { test } not found')
            return None
        else:
            self.debug(4,f'Returning path {test}')
            return test
        
    # --- Sending/writing debug/log messages ---
        
    def debug(self,level,m):
        """Write a debug message to the log, if level < DEBUG.
        """
        if level <= DEBUG:
            self._c_instance.log_message(f'E1 (debug): {m}')

    def log_message(self,m):
        self._c_instance.log_message(f'E1 (log): {m}')

    def show_message(self,m):
        """Show a message in the Live message line (lower left corner).
        """
        self._c_instance.show_message(m)

    # --- Fast MIDI sysex upload handling

    def _run_command(self,command):
        self.debug(4,f'Running external command {command}')
        return os.system(command)

    def _test_sendmidi(self):
        # test the sendmidi command and return whether it is properly installed
        testcommand = f"{self._sendmidi_cmd} dev '{E1_CTRL_PORT}'"
        return (self._run_command(testcommand) == 0)

    def _send_sysex_fast(self,preset_as_bytes):
        # convert bytes to their string representation.
        # strip first and last byte of SysEx command in preset_as_bytes
        # because sendmidi syx adds them again
        bytestr = ' '.join(str(b) for b in preset_as_bytes[1:-1])
        command = f"{self._sendmidi_cmd} dev '{E1_CTRL_PORT}' syx { bytestr }"
        error = self._run_command(command)
        if error:
            self.debug(1,'Fast SysEx upload command returned with error.')
    
    # --- MIDI handling ---

    def send_midi(self,message):
        self.debug(3,f'Sending MIDI message (first 10) { message[:10] }')
        self.debug(5,f'Sending MIDI message { message }.')
        time.sleep(0.005) # don't overwhelm the E1!
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

    # TODO see https://docs.electra.one/developers/luaext.html
    def _send_lua_command(self,command):
        self.debug(3,f'Sending LUA command {command}.')
        sysex_header = (0xF0, 0x00, 0x21, 0x45, 0x08, 0x0D)
        sysex_command = tuple([ ord(c) for c in command ])
        sysex_close = (0xF7, )
        self.send_midi(sysex_header + sysex_command + sysex_close)

    # TODO see https://docs.electra.one/developers/midiimplementation.html
    def _select_preset_slot(self,slot):
        self.debug(3,f'Selecting slot {slot}.')
        (bankidx, presetidx) = slot
        assert bankidx in range(6), 'Bank index out of range.'
        assert presetidx in range(12), 'Preset index out of range.'
        sysex_header = (0xF0, 0x00, 0x21, 0x45, 0x09, 0x08)
        sysex_select = (bankidx, presetidx)
        sysex_close = (0xF7, )
        self.send_midi(sysex_header + sysex_select + sysex_close)
        # Note: The E1 will in response send a preset changed message (7E 02)
        # (followed by an ack (7E 01)); when received by the remote script
        # WHEN READY, this will initiate a refresh_state that will update the
        # values displayed on the E1
        ElectraOneBase.current_visible_slot = slot

    # see https://docs.electra.one/developers/midiimplementation.html#upload-a-lua-script        
    def _upload_lua_script_to_current_slot(self,script):
        self.debug(3,f'Uploading LUA script {script}.')
        sysex_header = (0xF0, 0x00, 0x21, 0x45, 0x01, 0x0C)
        sysex_script = tuple([ ord(c) for c in script ])
        sysex_close = (0xF7, )
        if self._sysex_fast:
            self._send_sysex_fast(sysex_header + sysex_script + sysex_close)
        else:
            self.send_midi(sysex_header + sysex_script + sysex_close)

    # see https://docs.electra.one/developers/midiimplementation.html#upload-a-preset
    def _upload_preset_to_current_slot(self,preset):
        self.debug(3,f'Uploading preset (size {len(preset)} bytes).')
        sysex_header = (0xF0, 0x00, 0x21, 0x45, 0x01, 0x01)
        sysex_preset = tuple([ ord(c) for c in preset ])
        sysex_close = (0xF7, )
        if not DUMP: # no need to write this to the log if the same thing is dumped
            self.debug(6,f'Preset = { preset }')
        if self._sysex_fast:
            self._send_sysex_fast(sysex_header + sysex_preset + sysex_close)
        else:
            self.send_midi(sysex_header + sysex_preset + sysex_close)

    def _wait_for_ack_or_timeout(self,timeout):
        """Wait for the reception of an ACK message from the E1, or
           the timeout, whichever is sooner. Return whether ACK received.
        """
        self.debug(3,f'Upload thread setting timeout {timeout} (pu: {ElectraOneBase.preset_uploading}).')
        while (not ElectraOneBase.ack_received) and (timeout > 0):
            time.sleep(0.1)
            self.debug(5,f'Upload thread waiting for ACK, timeout {timeout}.')
            timeout -= 1
        if not ElectraOneBase.ack_received:
            self.debug(3,f'Upload thread: ACK received within timeout {timeout} (pu: {ElectraOneBase.preset_uploading}).')
        else:
            self.debug(3,f'Upload thread: ACK not received, operation may have failed (pu: {ElectraOneBase.preset_uploading}).')
        return ElectraOneBase.ack_received
    
    # preset is the json preset as a string
    def _upload_preset_thread(self,slot,preset):
        """To be called as a thread. Select a slot and upload a preset. In both
           cases wait (within a timeout) for confirmation from the E1.
           Reactivate the interface when done.
           (self is a reference to the calling EffectController object)
        """
        # should anything happen inside this thread, make sure we write to debug
        try:
            self.debug(2,'Upload thread starting...')
            # first select slot and wait for ACK
            ElectraOneBase.ack_received = False
            self._select_preset_slot(slot)
            if self._wait_for_ack_or_timeout(10): # timeout 1 second
                # slot selected, now upload preset and wait for ACK
                ElectraOneBase.ack_received = False
                self._upload_preset_to_current_slot(preset)
                # timeout depends on patch complexity
                if self._wait_for_ack_or_timeout( int(len(preset)/100) ):
                    # preset uploaded, now upload lua script and wait for ACK
                    ElectraOneBase.ack_received = False
                    self._upload_lua_script_to_current_slot(DEFAULT_LUASCRIPT)
                    if not self._wait_for_ack_or_timeout(10):
                        self.debug(3,'Upload thread: lua script upload may have failed.')                        
                else:
                    self.debug(3,'Upload thread: preset upload may have failed.')
                ElectraOneBase.preset_uploading = False
                # rebuild midi map (will also refresh state) (this is why interface needs to be reactivated first ;-)
                self.debug(2,'Upload thread requesting MIDI map to be rebuilt.')
                self.request_rebuild_midi_map()                
                self.debug(2,'Upload thread done.')
            else:
                # slot selection timed out; reopen interface
                ElectraOneBase.preset_uploading = False
                self.debug(2,'Upload thread failed to select slot. Aborted.')
        except:
            ElectraOneBase.preset_uploading = False
            self.debug(1,f'Exception occured in upload thread {sys.exc_info()}')
        
    def upload_preset(self,slot,preset):
        """Select a slot and upload a preset. Returns immediately, but closes
           interface until preset fully loaded in the background.
        """
        # 'close' the interface until preset uploaded.
        ElectraOneBase.preset_uploading = True  # do this outside thread because thread may not even execute first statement before finishing
        # thread also requests to rebuild MIDI map at the end, and calls refresh state
        self._upload_thread = threading.Thread(target=self._upload_preset_thread,args=(slot,preset))
        self._upload_thread.start()
