# ElectraOneBase
# - Base class with common functions and interface to Live
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

# --- MIDI CC handling

# CC status nibble
CC_STATUS = 0xB0

def _get_cc_statusbyte(channel):
    """Return the MIDI byte signalling a CC message on the specified channel.
       - channel: MIDI channel; int (1..16)
       - result: statusbyte; int (0..127)
    """
    # status byte encodes midi channel (-1!) in the least significant nibble
    return CC_STATUS + channel - 1

def is_cc_statusbyte(statusbyte):
    """Return whether the MIDI statusbyte encodes a MIDI CC message
       - statusbyte; int (0..127)
       - result: boolean
    """
    return (statusbyte & 0xF0) == CC_STATUS

def get_cc_midichannel(statusbyte):
    """Return the MIDI channel encoded in a CC status byte
       - statusbyte; int (0..127)
       - result: MIDI channel; int (1..16)
    """
    return statusbyte - CC_STATUS + 1

def cc_value_for_item_idx(idx, items):
    """Return the MIDI CC control value corresponding to the idx-th item
       in a list of items.
       - idx: index in the list of items; int
       - items: the list of items; any list
       - result: control value; int (0..127)
    """
    # quantized parameters have a list of values. For such a list with
    # n items, item i (staring at 0) has MIDI CC control value
    # round(i * 127/(n-1)) 
    return round( idx * (127 / (len(items)-1) ) )

def cc_value(p, max):
    """Convert the value of a parameter to its corresponding CC value
       (in the range 0..max)
       - p: Ableton Live parameter; Live.DeviceParameter.DeviceParameter
       - max: maximum value (127 or 16383), range is [0..max]; int
       - result: CC value; int
    """
    return round(max * ((p.value - p.min) / (p.max - p.min)))

def hexify(message):
    """Convert the sequence of (MIDI) bytes into a hexadecimal string
       - message: sequence; (byte)
       - result: str
    """
    mstr = [ f'0x{e:02X}' for e in message ]
    return " ".join(mstr)

# --- main class

class ElectraOneBase:
    """E1 base class with common functions
       (interfacing with Live through c_instance).
    """
    # This is the base class for all other classes in this package, and
    # therefore several instances of it are created.

    # -- CLASS variables (exist exactly once, only inside this class)
    
    # Command to use for fast sysex upload (to be set during initialisation
    # using SENDMIDI_CMD and LIBDIR).
    _fast_sysex_cmd = None
    
    # Record whether fast uploading of sysex is supported or not.
    # (Initially None to indicate that support not tested yet)
    _fast_sysex = None

    # flag registering whether a preset is being uploaded. Used together with
    # E1_connected to open/close E1 remote-script interface. See is_ready()
    preset_uploading = None

    # flag registering whether E1 is connected. Used together with preset_uploading
    # to open/close E1 remote-script interface. See is_ready()
    E1_connected = None

    # flag indicating whether the last preset upload was successful
    # TODO: this is not used in rest of script 
    preset_upload_successful = None

    # flag to inform a thread that a SysEx ACK message was received
    # (set by _do_ack() in ElectraOne.py).
    ack_received = False

    # slot currently visibile on the E1; used to prevent unneccessary
    # refresh_state for invisible presets (set by _do_preset_changed()
    # in ElectraOne.py and _select_preset_slot() below).
    current_visible_slot = None

    # delay after sending (to prevent overload when refreshing full state
    # which leads to bursts in updates)
    # Global variables because there are different instances of ElectraOneBase!
    _send_midi_sleep = 0  # 0.005 
    _send_value_update_sleep = 0 # 0.015
    
    # --- LIBDIR handling

    def _get_libdir(self):
        """Determine library path based on LIBDIR.
           Either ~/LIBDIR, /LIBDIR, or the user home directory,
           the first of these that exist.
           Home is assumed to always exist.
           - result: library path that exists ; str
        """
        # sanitise leading and trailing /
        ldir = LIBDIR
        if ldir[0] == '/':
            ldir = ldir[1:]
        if ldir[-1] == '/':
            ldir = ldir[:-1]
        home = os.path.expanduser('~')
        test =  f'{ home }/{ ldir }'
        self.debug(4,f'Testing library path {test}...')
        if not os.path.isdir(test):
            # try LIBDIR as absolute path
            test =  f'/{ ldir }'
            self.debug(4,f'Testing library path {test}...')
            if not os.path.isdir(test):
                # default is HOME
                test = home
        self.debug(4,f'Using library path {test}.')
        return test
    
    def _ensure_in_libdir(self, path):
        """Ensure the specified relative directory exists in the library path
           (ie create it if it doesnt exist).
           - path: relative path to directory; str
           - result: full path in library that exists ; str
        """
        self.debug(4,f'Ensure {path} exists in library.')
        root = self._get_libdir()
        test = f'{ root }/{ path }'
        if not os.path.isdir(test):
            # TODO: what if test exists, but is not a directory
            os.mkdir(test)    
        return test
        
    def _find_in_libdir(self, path):
        """Find path in library path and return it if found, else return None
           - path: path to find; str
           - result: path found, None if not found; str
        """
        self.debug(4,f'Looking for {path} in library.')
        root = self._get_libdir()
        test = f'{ root }/{ path }'
        if not os.path.exists(test):
            self.debug(4,f'Path { test } not found.')
            return None
        else:
            self.debug(4,f'Found as {test}.')
            return test

    # --- INIT
    
    def __init__(self, c_instance):
        """Initialise.
           - c_instance: Live interface object (see __init.py__)
        """
        # c_instance is/should be the object passed by Live when
        # initialising the remote script (see __init.py__). Through
        # c_instance we have access to Live: the log file, the midi map
        # the current song (and through that all devices and mixers)
        self._c_instance = c_instance
        # (main ElectraOne script must request to setup fast sysex,
        # because this can only be done after the E1 is detected)
        #
        
    def is_ready(self):
        """Return whether the remote script is ready to process requests
           or not (ie whether the E1 is connected and no preset upload is
           in progress).
           - result: bool
        """
        return (ElectraOneBase.E1_connected and not ElectraOneBase.preset_uploading)
    
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
        self.debug(4,'Rebuilding MIDI map requested')
        self._c_instance.request_rebuild_midi_map()

    def get_device_name(self,device):
        """Return the (fixed) name of the device (i.e. not the name of the preset)
           - device: the device; Live.Device.Device
           - result: device name; str
        """
        # TODO: adapt to also get an appropriate name for MaxForLive devices
        # (device.name equals the name of the selected preset;
        # device.class_display_name is just a pretyy-printed version of class_name)
        self.debug(5,f'Returning class_name { device.class_name } as device name. Aka name: { device.name } and class_display_name: { device.class_display_name }')
        return device.class_name

    # --- Sending/writing debug/log messages ---
        
    def debug(self, level, m):
        """Write a debug message to the log, if level < DEBUG.
        """
        if level <= DEBUG:
            if level == 0:
                indent = '#'
            else:
                indent = '-' * level
            # write readable log entries also for multi-line messages
            for l in m.splitlines(keepends=True):
                self._c_instance.log_message(f'E1 (debug): {indent} {l}')  

    def log_message(self, m):
        """Write a log message to the log.
        """
        self._c_instance.log_message(f'E1 (log): {m}')

    def show_message(self, m):
        """Show a message in the Live message line (lower left corner).
        """
        self._c_instance.show_message(m)

    # --- Fast MIDI sysex upload handling

    def _run_command(self, command):
        """Run the command in a shell, and return whether successful or not.
           - command: command to run; str
           - result: success?; bool
        """
        self.debug(4,f'Running external command {command}')
        # TODO: return type is different accross platforms
        return_code = os.system(command)
        self.debug(4,f'External command returned {return_code}')        
        return (return_code == 0)

    def setup_fast_sysex(self):
        """Set up fast sysex upload.
        """
        # Do this only once.
        if ElectraOneBase._fast_sysex == None:
            if USE_FAST_SYSEX_UPLOAD:
                # find sendmidi
                self.debug(1,'Testing whether fast uploading of presets is supported.')
                ElectraOneBase._fast_sysex_cmd = self._find_in_libdir(SENDMIDI_CMD)
                if ElectraOneBase._fast_sysex_cmd:
                    # if found test if it works
                    testcommand = f"{ElectraOneBase._fast_sysex_cmd} dev '{E1_CTRL_PORT}'"
                    if self._run_command(testcommand):
                        self.debug(1,'Fast uploading of presets supported. Great, using that!')
                        ElectraOneBase._fast_sysex = True
                    else:
                        self.debug(1,'Fast uploading of presets not supported (command failed), reverting to slow method.')
                        ElectraOneBase._fast_sysex = False
                else:
                    self.debug(1,'Fast uploading of presets not supported (command not found), reverting to slow method.')
                    ElectraOneBase._fast_sysex =  False
            else:
                self.debug(1,'Slow uploading of presets configured.')
                ElectraOneBase._fast_sysex = False
            
    # --- send MIDI ---

    def _midi_burst_on(self):
        """Prepare the script for a burst of updates; set a small delay
           to prevent clogging the E1
        """
        self.debug(5,'MIDI burst on.')
        # TODO: set proper timings
        ElectraOneBase._send_midi_sleep = 0.005
        ElectraOneBase._send_value_update_sleep = 0.035
        
    def _midi_burst_off(self):
        """Reset the delays, because updates are now individual.
        """
        self.debug(5,'MIDI burst off.')
        ElectraOneBase._send_midi_sleep = 0
        ElectraOneBase._send_value_update_sleep = 0 
    
    def send_midi(self, message):
        """Send a MIDI message through Ableton Live (except for longer
           SysEx messages, if fast sending is supported)
           - message: the MIDI message to send; sequence of bytes
        """
        # test whether longer SysEx message, and fast uploading is supported
        if len(message) > 100 and ElectraOneBase._fast_sysex \
           and message[0] == 0xF0 and message[-1] == 0xF7:
            # convert bytes sequence to its string representation.
            # (strip first and last byte of SysEx command in bytes parameter
            # because sendmidi syx adds them again)
            bytestr = ' '.join(str(b) for b in message[1:-1])
            command = f"{ElectraOneBase._fast_sysex_cmd} dev '{E1_CTRL_PORT}' syx { bytestr }"
            if not self._run_command(command):
                self.debug(4,'Sending SysEx failed')
        else:
            self.debug(4,f'Sending MIDI message (first 10): { hexify(message[:10]) }')
            self.debug(5,f'Sending MIDI message: { hexify(message) }.')
            self._c_instance.send_midi(message)
        time.sleep(ElectraOneBase._send_midi_sleep) # don't overwhelm the E1!
        
    # --- MIDI CC handling ---

    def send_midi_cc7(self, channel, cc_no, value):
        """Send a 7bit MIDI CC message (through Ableton Live).
           - channel: MIDI Channel; int (1..16)
           - cc_no: CC parameter number; int (0..127)
           - value: the value to send; int (0..127)
        """
        assert channel in range(1,17), f'CC channel { channel } out of range.'
        assert cc_no in range(128), f'CC no { cc_no } out of range.'
        assert value in range(128), f'CC value { value } out of range.'
        message = (_get_cc_statusbyte(channel), cc_no, value )
        self.send_midi(message)

    def send_midi_cc14(self, channel, cc_no, value):
        """Send a 14bit MIDI CC message (through Ableton Live).
           - channel: MIDI Channel; int (1..16)
           - cc_no: CC parameter number; int (0..127)
           - value: the value to send; int (0..16383)
        """
        assert channel in range(1,17), f'CC channel { channel } out of range.'
        # CC14 controls only allowed in range 0..31
        assert cc_no in range(32), f'CC no { cc_no } out of range.'
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
        """Send the value of a Live parameter as a 14bit MIDI CC message 
           (through Ableton Live).
           - p : Ableton Live parameter; Live.DeviceParameter.DeviceParameter
           - channel: MIDI Channel; int (1..16)
           - cc_no: CC parameter number; int (0..127)
        """
        self.debug(3,f'Sending value for {p.original_name} over MIDI channel {channel} as CC parameter {cc_no} in 14bit.')
        value = cc_value(p,16383)
        self.send_midi_cc14(channel, cc_no, value)

    def send_parameter_as_cc7(self, p, channel, cc_no):
        """Send the value of a Live parameter as a 7bit MIDI CC message 
           (through Ableton Live)
           - p : Ableton Live parameter; Live.DeviceParameter.DeviceParameter
           - channel: MIDI Channel; int (1..16)
           - cc_no: CC parameter number; int (0..127)
        """
        self.debug(3,f'Sending value for {p.original_name} over MIDI channel {channel} as CC parameter {cc_no} in 7bit.')
        if p.is_quantized:
            idx = int(p.value)
            value = cc_value_for_item_idx(idx,p.value_items)
        else:
            value = cc_value(p,127)
        self.send_midi_cc7(channel, cc_no, value)

    def send_parameter_using_ccinfo(self, p, ccinfo):
        """Send the value of Live a parameter as a MIDI CC message 
           (through Ableton Live, using CC info to determine where and how).
           - parameter: Ableton Live parameter; Live.DeviceParameter.DeviceParameter
           - ccinfo: CC information (channel, cc, bits) about the parameter; CCInfo
        """
        self.debug(3,f'Sending value for {p.original_name} over {ccinfo}.')
        channel = ccinfo.get_midi_channel()
        cc_no = ccinfo.get_cc_no()
        if ccinfo.is_cc14():
            self.send_parameter_as_cc14(p, channel, cc_no)
        else:
            self.send_parameter_as_cc7(p, channel, cc_no)                

    # --- MIDI SysEx handling ---

    def _send_lua_command(self, command):
        """Send a LUA command to the E1.
           - command: the command to send; str
        """
        self.debug(3,f'Sending LUA command {command}.')
        # see https://docs.electra.one/developers/luaext.html
        sysex_header = (0xF0, 0x00, 0x21, 0x45, 0x08, 0x0D)
        sysex_command = tuple([ ord(c) for c in command ])
        sysex_close = (0xF7, )
        self.send_midi(sysex_header + sysex_command + sysex_close)

    def update_track_labels(self, idx, label):
        """Update the label for a track on all relevant pages
           in the currently selected mixer preset.
           - idx: index of the track (starting at 0); int
           - label: new text; str
        """
        command = f'utl({idx},"{label}")'
        self._send_lua_command(command)
        
    def update_return_sends_labels(self, returnidx, label):
        """Update the label for a return track and the associated send controls
           in the currently selected mixer preset.
           - returnidx: index of the return track (starting at 0); int
           - label: new text; str
        """
        command = f'ursl({returnidx},"{label}")'
        self._send_lua_command(command)
        
    def set_mixer_visibility(self, tc, rc):
        """Set the visibility of the controls and group labels when
           tc tracks and rc returns are active (and need
           to be visible in the mixer preset, currently selected.
           - tc: track count; int
           - rc: return track count; int
        """
        self.debug(4,f'Setting mixer preset visibility: {tc} tracks and {rc} returns')
        command = f'smv({tc},{rc})'
        self._send_lua_command(command)

    def send_value_update(self, id, valuestr):
        """Send a value update for a control in the currently displayed patch
           on the E1.
           - id: control id in the preset; int
           - valuestr: string representing value to display; str
        """
        command = f'svu({id},"{valuestr}")'
        self._send_lua_command(command)
        time.sleep(ElectraOneBase._send_value_update_sleep) # don't overwhelm the E1!
                          
    def _select_preset_slot(self, slot):
        """Select a slot on the E1.
           - slot: slot to select; tuple of ints (bank: 0..5, preset: 0..1)
        """
        self.debug(3,f'Selecting slot {slot}.')
        (bankidx, presetidx) = slot
        assert bankidx in range(6), f'Bank index {bankidx} out of range.'
        assert presetidx in range(12), f'Preset index {presetifx} out of range.'
        # see https://docs.electra.one/developers/midiimplementation.html
        sysex_header = (0xF0, 0x00, 0x21, 0x45, 0x09, 0x08)
        sysex_select = (bankidx, presetidx)
        sysex_close = (0xF7, )
        self.send_midi(sysex_header + sysex_select + sysex_close)
        # Note: The E1 will in response send a preset changed message (7E 02)
        # (followed by an ack (7E 01)); but this will typically be ignored
        # as the upload thread closes the interface. 
        ElectraOneBase.current_visible_slot = slot

    def _remove_preset_from_slot(self, slot):
        """Remove the current preset from a slot on the E1.
           - slot: slot to delete preset from; (bank: 0..5, preset: 0..1)
        """
        self.debug(3,f'Removing preset from slot {slot}.')
        (bankidx, presetidx) = slot
        assert bankidx in range(6), 'Bank index out of range.'
        assert presetidx in range(12), 'Preset index out of range.'
        # see https://docs.electra.one/developers/midiimplementation.html#preset-remove
        sysex_header = (0xF0, 0x00, 0x21, 0x45, 0x05, 0x01)
        sysex_select = (bankidx, presetidx)
        sysex_close = (0xF7, )
        self.send_midi(sysex_header + sysex_select + sysex_close)
        
    def _upload_lua_script_to_current_slot(self, luascript):
        """Upload the specified LUA script to the currently selected slot on
           the E1 (use _select_preset_slot to select the desired slot)
           - luascript: LUA script to upload; str
        """
        self.debug(3,f'Uploading LUA script {luascript}.')
        # see https://docs.electra.one/developers/midiimplementation.html#upload-a-lua-script        
        sysex_header = (0xF0, 0x00, 0x21, 0x45, 0x01, 0x0C)
        sysex_script = tuple([ ord(c) for c in luascript ])
        sysex_close = (0xF7, )
        self.send_midi(sysex_header + sysex_script + sysex_close)

    def _upload_preset_to_current_slot(self, preset):
        """Upload the specified preset to the currently selected slot on
           the E1 (use _select_preset_slot to select the desired slot)
           - preset: preset to upload; str (JASON, .epr format)
        """
        self.debug(3,f'Uploading preset (size {len(preset)} bytes).')
        # see https://docs.electra.one/developers/midiimplementation.html#upload-a-preset
        sysex_header = (0xF0, 0x00, 0x21, 0x45, 0x01, 0x01)
        sysex_preset = tuple([ ord(c) for c in preset ])
        sysex_close = (0xF7, )
        if not DUMP: # no need to write this to the log if the same thing is dumped
            self.debug(6,f'Preset = { preset }')
        self.send_midi(sysex_header + sysex_preset + sysex_close)

    def _wait_for_ack_or_timeout(self, timeout):
        """Wait for the reception of an ACK message from the E1, or
           the timeout, whichever is sooner. Return whether ACK received.
           - timeout: time to wait in 10ms; int
        """
        self.debug(3,f'Thread setting timeout {timeout} (preset uploading: {ElectraOneBase.preset_uploading}).')
        while (not ElectraOneBase.ack_received) and (timeout > 0):
            self.debug(5,f'Thread waiting for ACK, timeout {timeout}.')
            time.sleep(0.01)
            timeout -= 1
        if ElectraOneBase.ack_received:
            self.debug(3,f'Thread: ACK received within timeout {timeout} (preset uploading: {ElectraOneBase.preset_uploading}).')
        else:
            self.debug(3,f'Thread: ACK not received, operation may have failed (preset uploading: {ElectraOneBase.preset_uploading}).')
        return ElectraOneBase.ack_received
    
    def _upload_preset_thread(self, slot, preset, luascript):
        """To be called as a thread. Select a slot, tehn upload a preset, and
           then upload a lua script for it. In all cases wait (within a timeout) for
           confirmation from the E1. Reactivate the interface when done and
           request to rebuild the midi map.
           - slot: slot to upload to; (bank: 0..5, preset: 0..1)
           - preset: preset to upload; str (JASON, .epr format)
           - luascript: LUA script to upload; str
        """
        # should anything happen inside this thread, make sure we write to debug
        try:
            self.debug(2,'Upload thread starting...')
            # first select slot and wait for ACK
            ElectraOneBase.ack_received = False
            self._select_preset_slot(slot)
            if self._wait_for_ack_or_timeout(100): # timeout 1 second
                # slot selected, now upload preset and wait for ACK
                ElectraOneBase.ack_received = False
                self._upload_preset_to_current_slot(preset)
                # timeout depends on patch complexity
                if self._wait_for_ack_or_timeout( int(len(preset)/10) ):
                    # preset uploaded, now upload lua script and wait for ACK
                    ElectraOneBase.ack_received = False
                    self._upload_lua_script_to_current_slot(luascript)
                    if self._wait_for_ack_or_timeout(100):
                        ElectraOneBase.preset_upload_successful = True
                    else: # lua script upload timeout
                        self.debug(3,'Upload thread: lua script upload failed. Aborted')
                else: # preset upload timeout
                    self.debug(3,'Upload thread: preset upload failed. Aborted')
            else: # slot selection timed out
                self.debug(2,'Upload thread failed to select slot. Aborted.')
            # reopen interface
            ElectraOneBase.preset_uploading = False
            if ElectraOneBase.preset_upload_successful == True:
                # rebuild midi map (will also refresh state) (this is why interface needs to be reactivated first ;-)
                self.debug(2,'Upload thread requesting MIDI map to be rebuilt.')
                self.request_rebuild_midi_map()                
                self.debug(2,'Upload thread done.')
        except:
            ElectraOneBase.preset_uploading = False
            self.debug(1,f'Exception occured in upload thread {sys.exc_info()}')
        
    def upload_preset(self, slot, preset, luascript):
        """Select a slot and upload a preset and associated luascript.
           Returns immediately, but closes interface until preset fully loaded
           in the background. Once upload finished, the thread will request to
           rebuild the midi map.
           - slot: slot to upload to; (bank: 0..5, preset: 0..1)
           - preset: preset to upload; str (JASON, .epr format)
           - luascript: LUA script to upload; str
        """
        # 'close' the interface until preset uploaded.
        ElectraOneBase.preset_uploading = True  # do this outside thread because thread may not even execute first statement before finishing
        ElectraOneBase.preset_upload_successful = False
        # thread also requests to rebuild MIDI map at the end (if successful), and this then calls refresh state
        self._upload_thread = threading.Thread(target=self._upload_preset_thread,args=(slot,preset,luascript))
        self._upload_thread.start()

                
    
        
