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

# Note:
# 
# Functions that start with a double underscore __ shoult only be
# called within a thread.

import Live

# Python imports
from pathlib import Path
import threading
import time
import sys
import os
import string
import inspect

# Local imports
from .config import *
from .Log import Log
from .E1Midi import hexify, cc7_value_for_par, cc14_value_for_par, cc7_value_for_item_idx, make_cc, make_E1_sysex

# possible values for ack_or_nack_received
ACK_RECEIVED = 0
NACK_RECEIVED = 1

# Remote script input/output port number (0: Port 1, 1: Port 2, 2: CTRL)
E1_PORT = 0

class ElectraOneBase(Log):
    """E1 base class with common functions
       (interfacing with Live through c_instance).
    """
    # This is the base class for all other classes in this package, and
    # therefore several instances of it are created.

    # -- CLASS variables (exist exactly once, only inside this class)

    # Path to where this remote script is installed
    REMOTE_SCRIPT_PATH = None
    
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
    preset_upload_successful = None

    # recording which slot is currently visibel on the E1
    current_visible_slot = (0,0)
    
    # count number of acks pending
    acks_pending = 0

    # time at which acks_pending was last incremented
    acks_pending_incremented_time = 0.0
    
    # flag to inform whether an ACK or a NACK was last received
    # (set by _do_ack() / _do_nack() in ElectraOne.py).
    ack_or_nack_received = None

    # delay after sending (to prevent overload when refreshing full state
    # which leads to bursts in updates)
    # Global variables because there are different instances of ElectraOneBase!
    _send_midi_sleep = 0  
    _send_value_update_sleep = 0 
    
    # --- INIT
    
    def __init__(self, c_instance):
        """Initialise.
           - c_instance: Live interface object (see __init.py__)
        """
        # c_instance is/should be the object passed by Live when
        # initialising the remote script (see __init.py__). Through
        # c_instance we have access to Live: the log file, the midi map
        # the current song (and through that all devices and mixers)
        Log.__init__(self, c_instance)
        # get the path to this remote script instance
        if not ElectraOneBase.REMOTE_SCRIPT_PATH:
            ElectraOneBase.REMOTE_SCRIPT_PATH = Path(inspect.getfile(ElectraOneBase)).parent
        
    def is_ready(self):
        """Return whether the remote script is ready to process requests
           or not (ie whether the E1 is connected and no preset upload is
           in progress).
           - result: bool
        """
        return (ElectraOneBase.E1_connected and not ElectraOneBase.preset_uploading)

    # --- standard folders and files

    def dumppath(self):
        """Folder to dump presets in
           - result:  ; Path
        """
        return ElectraOneBase.REMOTE_SCRIPT_PATH / 'dumps'

    def preloadedpath(self):
        """Folder to load predefined presets from
           - result:  ; Path
        """
        return ElectraOneBase.REMOTE_SCRIPT_PATH / 'preloaded'
    
    def luascriptfname(self):
        """Filename to load default LUA script from
           - result:  ; Path
        """
        return ElectraOneBase.REMOTE_SCRIPT_PATH / 'default.lua'
    
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
        self.debug(2,'Rebuilding MIDI map requested')
        self._c_instance.request_rebuild_midi_map()

    def _find_first_rack(self,torc):
        for d in torc.devices:
            self.debug(7,f'Considering {d.name}')
            if type(d) == Live.RackDevice.RackDevice:
                self.debug(6,f'Rack found: {d.name}')
                return d
        return None

    def _visible_chains_for_torc(self,torc):
        """Return the visible chains for this track or chain
        """
        self.debug(6,f'Getting visible torcs for {torc.name}')
        chains = []
        rack = self._find_first_rack(torc)
        # TODO: Racks with only one chain have can_show_chains == False
        # and is_shwoing_chains == False, so this fails for
        # racks with one instrument that actually is unfolded
        if rack and rack.is_showing_chains:
            for chain in rack.chains:
                chains.append(chain)
                chains.extend( self._visible_chains_for_torc(chain) )
        return chains

    def get_visible_torcs(self):
        """Return the currently visible tracks or chains (torcs)
        """
        torcs = []
        for t in self.song().visible_tracks:
            #self.debug(6,f'Visible track {t.name}')
            #self.debug(7,f'Is visible = {t.is_visible}')
            #self.debug(7,f'Is grouped = {t.is_grouped}')                
            #self.debug(7,f'Can show chains = {t.can_show_chains}')
            #self.debug(7,f'Is showing chains = {t.is_showing_chains}')
            #self.debug(7,f'Is foldable = {t.is_foldable}')        
            #if t.is_foldable:
            #    self.debug(7,f'Fold state = {t.fold_state}')        
            torcs.append(t)
            torcs.extend( self._visible_chains_for_torc(t) )
        for torc in torcs:
            self.debug(6,f'Visible torc {torc.name}')
        return torcs

    def get_track_devices_flat(self,track):
        """Return all devices on a track, in a nested list structure following
           the structure of the chains on any rack on the track.
           - track: track to list devices for
           - return: a nested list of devices; [Live.Device.Device]
        """
        devices = []
        for d in track.devices:
            devices.append(d)
            if (type(d) == Live.RackDevice.RackDevice):
                # TODO we assume a rack always has chains; this appears to be the case
                for chain in d.chains:
                    for device in self.get_track_devices_flat(chain):
                        devices.append( device )
        self.debug(6,f'Devices found for track {track.name}:')
        for d in devices:
            self.debug(6,f'{d.name}')
        return devices
    
    def get_device_name(self, device):
        """Return the (fixed) name of the device (i.e. not the name of the preset)
           - device: the device; Live.Device.Device
           - result: device name ('Empty' when None); str
        """
        # For native devices and instruments, device.class_name is the name of
        # the device/instrument, and device.name equals the selected preset
        # (or the device/instrument name).
        #
        # For plugins and max devices however, device.class_name is useless
        # and device.name is returned instead (with spaces removed)
        #
        # To reliably identify preloaded presets by name for such devices
        # as well, embed them into a audio/instrument rack and give that rack
        # the name of the device.
        #
        # For racks themselves, device.class_name is also useless, so use
        # device.name instead
        #
        # To distinguish names for plugins/max devices (for which we derive
        # the name from the enclosing rack) from the name of the enclosing
        # rack itself, append a hash (#) to the name to the rack
        if not device:
            self.debug(7,'Getting name for empty device.')
            return 'Empty'
        self.debug(7,f'Getting name for device with class_name { device.class_name }. Aka name: { device.name } and class_display_name: { device.class_display_name }, (has type { type(device) }).')
        if device.class_name in ('AuPluginDevice', 'PluginDevice', 'MxDeviceMidiEffect', 'MxDeviceInstrument', 'MxDeviceAudioEffect'):
            cp = device.canonical_parent
            if isinstance(cp,Live.Chain.Chain) and (len(cp.devices) == 1):
                cp = cp.canonical_parent
                self.debug(7,'Enclosing rack found, using its name with spaces removed.')
                name = cp.name.replace(' ','')
            else:
                self.debug(7,'No enclosing rack found, using my own name with spaces removed (unreliable).')
                name = device.name.replace(' ','')
        elif device.class_name in ('InstrumentGroupDevice','DrumGroupDevice','MidiEffectGroupDevice','AudioEffectGroupDevice'):
            self.debug(7,'I am a rack, using my own name with spaces removed.')
            name = device.name.replace(' ','')
            name += "#"
        else:
            name = device.class_name
        self.debug(6,f'Device name is { name }.')
        return name
    
    # --- dealing with fimrware and Live versions

    # Live version info as a tuple of integers (major, minor, bugfix).
    LIVE_VERSION = (0,0,0)
    
    # E1 software version info as a tuple of integers (major, minor, sub).
    _E1_sw_version = (0,0,0)

    # E1 hardware version info as a tuple of integers (major, minor).
    _E1_hw_version = (0,0)

    # Record whether attached version of E1 is supported by the remote script
    E1_version_supported = False

    # Record whether E1 supports preloaded presets on the E1 itself
    E1_PRELOADED_PRESETS_SUPPORTED = False

    # Record whether an E1 DAW is attached
    E1_DAW = False

    # Minimum timeout to wait for an ACK (in seconds)
    MIN_TIMEOUT = 1.0

    # Time to sleep between MIDI CC and LUA value update messages in normal mode
    MIDI_SLEEP = 0
    VALUE_UPDATE_SLEEP = 0

    # Time to sleep between MIDI CC and LUA value update messages in burst mode
    BURST_MIDI_SLEEP = 0
    BURST_VALUE_UPDATE_SLEEP = 0 

    # Time to sleep after turning on/off burst mode
    BURST_ON_OFF_SLEEP = 0

    # factor to compute timemout for preset of certain length, in seconds/byte
    # (when fast uploading is enabled)
    PRESET_LENGTH_TIMEOUT_FACTOR = 0.1

    # factor to compute timemout for lua script of certain length, in seconds/byte
    # (when fast uploading is enabled)
    LUA_LENGTH_TIMEOUT_FACTOR = 0.1

    # maximum lenght of the LUA command string in the SysEx call lau command
    SYSEX_LUA_COMMAND_MAX_LENGTH = -1
    
    def _configure_for_version(self, sw_version, hw_version):
        """Configure the remote script depending on the version of E1 attached
        """
        ElectraOneBase._E1_sw_version = sw_version
        ElectraOneBase._E1_hw_version = hw_version
        if sw_version < (3,1,5):
            ElectraOneBase.E1_version_supported = False
            self.debug(0,f'Version {sw_version} older than 3.1.5. Disabling ElectraOne control surface.')
            self.show_message(f'Version {sw_version} older than 3.1.5. Disabling ElectraOne control surface.')
        else:
            ElectraOneBase.E1_version_supported = True
            # TODO: fixme
            ElectraOneBase.E1_DAW = (ElectraOneBase.REMOTE_SCRIPT_PATH.parts[2] == 'jhh')
            self.debug(1,f'E1_DAW = {ElectraOneBase.E1_DAW} ({ElectraOneBase.REMOTE_SCRIPT_PATH})')
            if sw_version < (3,7,0):
                ElectraOneBase.SYSEX_LUA_COMMAND_MAX_LENGTH = -1
            else:
                ElectraOneBase.SYSEX_LUA_COMMAND_MAX_LENGTH = 80
            # set hwardware dependent options
            # TODO: set proper timings
            if hw_version >= (3,0): # mkII
                ElectraOneBase.E1_PRELOADED_PRESETS_SUPPORTED = (sw_version >= (3,4,0))
                ElectraOneBase.MIN_TIMEOUT = 1.0
                ElectraOneBase.MIDI_SLEEP = 0 # 0.1 
                ElectraOneBase.VALUE_UPDATE_SLEEP = 0 
                ElectraOneBase.BURST_MIDI_SLEEP = 0 # 0.1 
                ElectraOneBase.BURST_VALUE_UPDATE_SLEEP = 0
                ElectraOneBase.BURST_ON_OFF_SLEEP = 0.1                 
                ElectraOneBase.PRESET_LENGTH_TIMEOUT_FACTOR = 0.00003
                ElectraOneBase.LUA_LENGTH_TIMEOUT_FACTOR = 0.0001
                self.show_message(f'E1 mk II, with firmware {sw_version} detected.')
            else: # mkI
                ElectraOneBase.E1_PRELOADED_PRESETS_SUPPORTED = False
                ElectraOneBase.MIN_TIMEOUT = 1.0
                ElectraOneBase.MIDI_SLEEP = 0
                ElectraOneBase.VALUE_UPDATE_SLEEP = 0 
                ElectraOneBase.BURST_MIDI_SLEEP = 0
                ElectraOneBase.BURST_VALUE_UPDATE_SLEEP = 0 
                ElectraOneBase.BURST_ON_OFF_SLEEP = 0.01                 
                ElectraOneBase.PRESET_LENGTH_TIMEOUT_FACTOR = 0.00003
                ElectraOneBase.LUA_LENGTH_TIMEOUT_FACTOR = 0.00008
                self.show_message(f'E1 mk I, with firmware {sw_version} detected.')
                
    def set_version(self, sw_versionstr, hw_versionstr):
        """Set the E1 firmware version.
           - sw_versionstr: software version string as returned by request response; int
           - hw_versionstr: hardware version string as returned by request response; str
        """
        # see https://docs.electra.one/developers/midiimplementation.html#get-an-electra-info
        # parse software version string
        # sw_versionstr format "aaabbbcccdd"
        # - aaa is the major (a if 1-9 aa if 10-99 etc.) 
        # - bbb is the minor
        # - ccc is the patch
        # - dd is for markings such as alpha, beta, rc (not used it much)
        self.debug(2,f'Parsing version info: {sw_versionstr}, {hw_versionstr}')
        if type(sw_versionstr) != str:
            sw_versionstr = str(sw_versionstr)
        try:
            majorstr = sw_versionstr[-11:-8]
            minorstr = sw_versionstr[-8:-5]
            substr =  sw_versionstr[-5:-2]    
            sw_version = (int(majorstr),int(minorstr),int(substr))
        except ValueError:
            self.debug(2,f'Failed to parse software version string { sw_versionstr }.')
            sw_version = (0,0,0)
        # parse hardware version string
        # hw_versionstr format "<major>.<minor>": "3.0" = mkII}
        try:
            version_tuple = hw_versionstr.split('.')
            if len(version_tuple) == 2:
                (majorstr,minorstr) = version_tuple
                hw_version = (int(majorstr),int(minorstr))
            else:
                hw_version = (0,0)
        except ValueError:
            self.debug(2,f'Failed to parse hardware version string { hw_versionstr }.')
            hw_version = (0,0)
        self._configure_for_version(sw_version,hw_version)
        self.debug(1,f'E1 firmware version: {sw_version}, hardware version: { hw_version }.') 
       
    # --- Fast MIDI sysex upload handling

    # Unfortunately, Ableton appears not to support subprocess.
    # (Importing subprocess raises the error: No module named '_posixsubprocess')
    def _run_command(self, command):
        """Run the command in a shell, and return whether succesful.
           - command: command to run; str
           - result: return whether succesful; bool
        """
        self.debug(5,f'Running external command {command[:40]}')
        self.debug(6,f'Running external command {command[:200]}')
        # os.system returns 0 for success on both MacOS and Windows
        return_code = os.system(command)
        self.debug(5,f'External command on OS {os.name} returned {return_code}')        
        return (return_code == 0)

    def setup_fast_sysex(self):
        """Set up fast sysex upload.
        """
        # Do this only once.
        # NOTE: modules are loaded once when Live starts, but stay alive when a new
        # song is loaded; so this initialisation only occurs when Live (re)starts. 
        if ElectraOneBase._fast_sysex == None:
            if SENDMIDI_CMD:
                # find sendmidi
                self.debug(1,'Testing whether fast uploading of presets is supported.')
                testcommand = f"{SENDMIDI_CMD} dev '{E1_PORT_NAME}'"
                if self._run_command(testcommand):
                    self.debug(1,'Fast uploading of presets supported. Great, using that!')
                    ElectraOneBase._fast_sysex = True
                else:
                    self.debug(1,'Fast uploading of presets not supported (command failed), reverting to slow method.')
                    ElectraOneBase._fast_sysex = False
            else:
                self.debug(1,'Slow uploading of presets configured.')
                ElectraOneBase._fast_sysex = False
            
    # --- ACK/NACK queue handling

    # Note: many of the commands below use SysExs to control the E1; the E1
    # typically responds with AKCs/NACKs, but the commands do not catch them because
    # - this appears to be unnecessary as far as the E1 is concerned
    # - would therefore slow down the script
    # - but most importantly: it is hard to catch them because most commands
    #   are not executed in a thread.
    # As a workaround (because the commands concerned are used to update the
    # display of the E1), the midi_burst_off command waits a bit to ensure that
    # all possible ACKs will be (silently!) received by the time the
    # command finished
    #
    # Call _increment_acxks_pending() *before* sending out the SysEx that
    # expects an ACK as response to avoid a race condition where the ACK is
    # received before the counter is incremented, and hence the
    # __wait_for_ack_or_timeout() fails
    def _increment_acks_pending(self):
        """Increment the number of pending ACKs by 1.
           (See ACK/NACK received functions in ElectraOne, and
            __wait_for_ack_or_timeout() below.)
        """
        ElectraOneBase.acks_pending += 1
        ElectraOneBase.acks_pending_incremented_time = time.time()
        self.debug(4,f'ACKS pending incremented to {ElectraOneBase.acks_pending} at time { ElectraOneBase.acks_pending_incremented_time }')

    def __adjust_timeout(self,timeout):
        """Adjust the timeout depending on whether fast sysex sending is
           suported or not, and whether logging of E1 messages is enabled.
           - timeout: time to wait (in seconds); float
           result: timeout in (fractional) seconds
        """
        # stretch timeout when no fast sysex uploading
        # TODO: how to deal with faster windows sysex processing?
        if not ElectraOneBase._fast_sysex:
            timeout = 50 * timeout
        # floor timeout to minimum
        timeout = max(ElectraOneBase.MIN_TIMEOUT,timeout)
        timeout = timeout * TIMEOUT_STRETCH
        return timeout
        
    def __wait_for_pending_acks_until(self,end_time):
        """Wait if there are any pending acks, until the specified end_time.
           (Can only be called inside a thread.)
           - end_time: time until which to wait, in (fractional) seconds; float
           - result: time waited, in (fractional) seconds; float
        """
        start_time = time.time()
        while (ElectraOneBase.acks_pending > 0) and \
              (time.time() < end_time ):
            self.debug(4,f'Thread waiting for ACK, current time is {time.time():.3f}.')
            time.sleep(0.01) # sleep a bit (10ms) to pause the thread
        return time.time() - start_time
        
    def __clear_acks_queue(self):
        """If any acks are pending, wait until they have been received (until
           some timeout).
           (Can only be called inside a thread.)
        """
        # wait four seconds since acks_pending was incremented last
        end_time = ElectraOneBase.acks_pending_incremented_time + 4.0
        self.debug(4,f'Thread clearing acks queue ({ElectraOneBase.acks_pending} pending) on {time.time():.3f}, wait until {end_time:.3f} (preset uploading: {ElectraOneBase.preset_uploading}).')
        waiting_time = self.__wait_for_pending_acks_until(end_time)
        now = time.time()
        if (ElectraOneBase.acks_pending == 0):
            self.debug(4,f'Thread: acks queue cleared at {now:.3f} within {waiting_time:.3f} seconds (preset uploading: {ElectraOneBase.preset_uploading}).')
        else:
            # clear any pending acks/nacks
            ElectraOneBase.acks_pending = 0            
            self.debug(4,f'Thread: acks queue still not empty at {now:.3f} after {waiting_time:.3f} seconds (preset uploading: {ElectraOneBase.preset_uploading}).')
        
    def __wait_for_ack_or_timeout(self, timeout):
        """Wait until all pending ACk or NACK messages from the E1 have
           been received, or the timeout, whichever is sooner. The timeout depends
           on whether fast sysex sending is suported or not, and whether logging
           of E1 messages is enabled.
           Return whether last message received was an ACK.
           (Can only be called inside a thread.)
           - timeout: time to wait (in seconds); float
        """
        timeout = self.__adjust_timeout(timeout)
        start_time = time.time()
        end_time = start_time + timeout
        self.debug(4,f'Thread waiting for ACK, setting timeout {timeout:.3f} seconds at time {start_time:.3f} (preset uploading: {ElectraOneBase.preset_uploading}).')
        waiting_time = self.__wait_for_pending_acks_until(end_time)
        now = time.time()
        if (ElectraOneBase.acks_pending == 0) and \
           (ElectraOneBase.ack_or_nack_received == ACK_RECEIVED):
            self.debug(4,f'Thread: ACK received at {now:.3f} within {waiting_time:.3f} seconds (preset uploading: {ElectraOneBase.preset_uploading}).')
            return True
        else:
            # clear any pending acks/nacks
            ElectraOneBase.acks_pending = 0            
            self.debug(4,f'Thread: ACK not received at {now:.3f} after {waiting_time:.3f} seconds, operation may have failed (preset uploading: {ElectraOneBase.preset_uploading}).')
            return False

    # --- send MIDI ---
    
    def send_midi(self, message):
        """Send a MIDI message through Ableton Live.
           - message: the MIDI message to send; sequence of bytes
        """
        self.debug(5,f'Sending MIDI message (first 10): { hexify(message[:10]) }')
        self.debug(6,f'Sending MIDI message: { hexify(message) }.')
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
        message = make_cc(channel, cc_no, value )
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
        message1 = make_cc(channel, cc_no, msb)
        message2 = make_cc(channel, 0x20 + cc_no, lsb)
        self.send_midi(message1)
        self.send_midi(message2)

    def send_parameter_as_cc7(self, p, channel, cc_no):
        """Send the value of a Live parameter as a 7bit MIDI CC message 
           (through Ableton Live)
           - p : Ableton Live parameter; Live.DeviceParameter.DeviceParameter
           - channel: MIDI Channel; int (1..16)
           - cc_no: CC parameter number; int (0..127)
        """
        self.debug(4,f'Sending value for {p.original_name} ({p.name}) over MIDI channel {channel} as CC parameter {cc_no} in 7bit.')
        if p.is_quantized:
            # this is either an on/off button or a control with overlays on the E1
            # (by assumption such parameters are always 7bit CC)
            idx = int(p.value)
            value = cc7_value_for_item_idx(idx,p.value_items)
        else:
            value = cc7_value_for_par(p)
        self.send_midi_cc7(channel, cc_no, value)

    def send_parameter_as_cc14(self, p, channel, cc_no):
        """Send the value of a Live parameter as a 14bit MIDI CC message 
           (through Ableton Live).
           - p : Ableton Live parameter; Live.DeviceParameter.DeviceParameter
           - channel: MIDI Channel; int (1..16)
           - cc_no: CC parameter number; int (0..127)
        """
        self.debug(4,f'Sending value for {p.original_name} over MIDI channel {channel} as CC parameter {cc_no} in 14bit.')
        # a quantized parameter is never a 14bit CC
        assert not p.is_quantized, f'Parameter {p.original_name} is not supposed to be quantized!'
        value = cc14_value_for_par(p)
        self.send_midi_cc14(channel, cc_no, value)

    def send_parameter_using_ccinfo(self, p, ccinfo):
        """Send the value of Live a parameter as a MIDI CC message 
           (through Ableton Live, using CC info to determine where and how).
           - parameter: Ableton Live parameter; Live.DeviceParameter.DeviceParameter
           - ccinfo: CC information (channel, cc, bits) about the parameter; CCInfo
        """
        #self.debug(4,f'Sending value for {p.original_name} using CCInfo {ccinfo}.')
        channel = ccinfo.get_midi_channel()
        cc_no = ccinfo.get_cc_no()
        if ccinfo.is_cc14():
            self.send_parameter_as_cc14(p, channel, cc_no)
        else:
            self.send_parameter_as_cc7(p, channel, cc_no)                

    # --- MIDI SysEx handling ---
    
    _TRANSLATION = { '♭' : 'b'
                   , '♯' : '#'
                   , '°' : '*'
                   , '∞' : 'inf'
                   }
    
    def _ascii_chars(self, c):
        """Replace important UNICODE char with similar ASCII char or string.
           Map other non ASCII chars to '?'
           - return: ASCII string (byte < 128)
        """
        if c in self._TRANSLATION:
            return self._TRANSLATION[c]
        elif ord(c) < 128:
            return c
        else:
            self.debug(5,f'UNICODE character {c} replaced.')
            return '?'

    def ascii_str(self,s):
        """Replace all important UNICODE chars in str with similar ASCII.
           Map other non ASCII chars to '?'
           - return: ASCII string
        """
        # use generator instead of list comprehension to not store intermediate result
        return ''.join( (self._ascii_chars(c) for c in s) )

    def _ascii_bytes(self,s):
        """Replace all important UNICODE chars in s with similar ASCII.
           Map other non ASCII chars to '?'. Return as a sequence of bytes.
           - return: sequence of bytes < 128
        """
        #return tuple( (ord(c) for c in self.ascii_str(s)) )
        chars_gen = (self._ascii_chars(c) for c in s) # generator
        return tuple(ord(c) for chars in chars_gen for c in chars) 

    def _send_midi_sysex(self, command, data):
        """Send the command and parameters as a E1 sysex message (prepend
           header and append termination), using fast sysex sending if
           supported. Caller must ensure that data does not contain bytes > 127.
           (We rely on Live to catch this and report errors.)
           - command: the sysex command; (bytes)
           - data: the sysex data to send; (bytes)
        """
        sysex_message = make_E1_sysex(command,data)
        self.debug(4,f'Sending SysEx ({len(sysex_message)} bytes).')
        # test whether longer SysEx message, and fast uploading is supported
        if len(sysex_message) > 100 and ElectraOneBase._fast_sysex: 
            # convert bytes sequence to its string representation.
            # (strip first and last byte of SysEx command in bytes parameter
            # because sendmidi syx adds them again)
            bytestr = ' '.join(str(b) for b in sysex_message[1:-1])
            command = f"{SENDMIDI_CMD} dev '{E1_PORT_NAME}' syx { bytestr }"
            if not self._run_command(command):
                self.debug(4,'Sending SysEx failed')
        else:
            self.send_midi(sysex_message)
        
    # --- commands that can be sent to the E1
            
    def send_e1_request(self):
        """Send a sysex request to the E1.
        """
        self.debug(4,f'Sending E1 sysex request.')
        # see https://docs.electra.one/developers/midiimplementation.html#get-an-electra-info
        sysex_command = (0x02, 0x7F)
        self._send_midi_sysex(sysex_command, ())
        # this command does not send an ack, but only a request_response
        
    def _send_lua_command(self, command):
        """Send a LUA command to the E1.
           - command: the command to send; str
        """
        self.debug(5,f'Sending LUA command {command} (length {len(command)}).')
        assert (ElectraOneBase.SYSEX_LUA_COMMAND_MAX_LENGTH == -1) or \
            (len(command) <= ElectraOneBase.SYSEX_LUA_COMMAND_MAX_LENGTH), \
            f'LUA command too long.'
        # see https://docs.electra.one/developers/luaext.html
        sysex_command = (0x08, 0x0D)
        sysex_lua = self._ascii_bytes(command) 
        # LUA commands respond with ACK/NACK
        self._increment_acks_pending()
        self._send_midi_sysex(sysex_command, sysex_lua)

    def midi_burst_on(self):
        """Prepare the script for a burst of updates; set a small delay
           to prevent clogging the E1, and disable window repaints.
        """
        self.debug(4,'MIDI burst on.')
        # TODO: set proper timings; note that the current HW has 256k RAM
        # so the buffers are only 32 entries for sysex, and 128 non-sysex
        # So really what should be done is wait after filling all buffers in
        # a burst
        ElectraOneBase._send_midi_sleep = ElectraOneBase.BURST_MIDI_SLEEP
        ElectraOneBase._send_value_update_sleep = ElectraOneBase.BURST_VALUE_UPDATE_SLEEP 
        # defer drawing
        self._send_lua_command('aa()')
        # wait a bit to ensure the command is processed before sending actual
        # value updates (we cannot wait for the actual ACK)
        time.sleep(ElectraOneBase.BURST_ON_OFF_SLEEP) 
        
    def midi_burst_off(self):
        """Reset the delays, because updates are now individual. And allow
           immediate window updates again. Draw any buffered window repaints.
        """
        self.debug(4,'MIDI burst off.')
        # wait a bit to ensure all MIDI CC messages have been processed
        time.sleep(ElectraOneBase.BURST_ON_OFF_SLEEP) 
        ElectraOneBase._send_midi_sleep = ElectraOneBase.MIDI_SLEEP
        ElectraOneBase._send_value_update_sleep = ElectraOneBase.VALUE_UPDATE_SLEEP
        # reenable drawing and update display
        self._send_lua_command('zz()')
        # wait a bit to ensure the command is processed
        # (we cannot wait for the actual ACK)
        time.sleep(ElectraOneBase.BURST_ON_OFF_SLEEP)

    def update_track_labels(self, idx, label):
        """Update the label for a track on all relevant pages
           in the currently selected mixer preset.
           - idx: index of the track (starting at 0); int
           - label: new text; str
        """
        assert idx in range(NO_OF_TRACKS), f'Track index {idx} out of range.' 
        self.debug(4,f'Update label for track {idx} to {label}.')
        # execute command (defined in mixer preset)
        command = f'utl({idx},"{label}")'
        # we assume label never exceeds SYSEX_LUA_COMMAND_MAX_LENGTH-8
        self._send_lua_command(command)
        
    def update_return_sends_labels(self, returnidx, label):
        """Update the label for a return track and the associated send controls
           in the currently selected mixer preset.
           - returnidx: index of the return track (starting at 0); int
           - label: new text; str
        """
        assert returnidx in range(MAX_NO_OF_SENDS), f'Return index {returnidx} out of range.' 
        self.debug(4,f'Update label for return track {returnidx} to {label}.')
        # execute command (defined in mixer preset)
        command = f'ursl({returnidx},"{label}")'
        # we assume label never exceeds SYSEX_LUA_COMMAND_MAX_LENGTH-9
        self._send_lua_command(command)
        
    def set_mixer_visibility(self, tc, rc):
        """Set the visibility of the controls and group labels when
           tc tracks and rc returns are active (and need
           to be visible in the mixer preset, currently selected.
           - tc: track count; int
           - rc: return track count; int
        """
        assert tc in range(NO_OF_TRACKS+1), f'Track count {tc} out of range.' 
        assert rc in range(MAX_NO_OF_SENDS+1), f'Return count {rc} out of range.' 
        self.debug(4,f'Setting mixer preset visibility: {tc} tracks and {rc} returns.')
        # execute command (defined in mixer preset)
        command = f'smv({tc},{rc})'
        # we assume SYSEX_LUA_COMMAND_MAX_LENGTH is big enought to hold two ints
        self._send_lua_command(command)

    def set_channel_eq_visibility_on_track(self,idx,flag):
        """Set the visibility of the eq device for the specified track.
           - idx: index of the track (starting at 0; NO_OF_TRACKS for master track); int
           - flag: whether the eq-device should be visible; bool
        """
        assert idx in range(NO_OF_TRACKS+1), f'Track index {idx} out of range.' 
        self.debug(4,f'Setting channel equaliser visibility for track {idx} to {flag}.')
        # execute command (defined in mixer preset)
        if flag:
          command = f'seqv({idx},true)'
        else:
          command = f'seqv({idx},false)'
        # we assume SYSEX_LUA_COMMAND_MAX_LENGTH is big enought to hold this
        self._send_lua_command(command)

    def set_arm_visibility_on_track(self,idx,flag):
        """Set the visibility of the arm button for the specified track.
           - idx: index of the track (starting at 0)
           - flag: whether the arm button should be visible; bool
        """
        assert idx in range(NO_OF_TRACKS), f'Track index {idx} out of range.' 
        self.debug(4,f'Setting arm button visibility for track {idx} to {flag}.')
        # execute command (defined in mixer preset)
        if flag:
          command = f'sav({idx},true)'
        else:
          command = f'sav({idx},false)'
        # we assume SYSEX_LUA_COMMAND_MAX_LENGTH is big enought to hold this
        self._send_lua_command(command)
        
    def set_tempo(self,valuestr):
        """Set the tempo dial value to the specified value string
           - valuestr: string representing value to display; str
        """
        self.debug(4,f'Setting the tempo string to {valuestr}.')
        # execute command (defined in mixer preset)
        command = f'st("{valuestr}")'
        # we assume SYSEX_LUA_COMMAND_MAX_LENGTH is big enought to hold this
        self._send_lua_command(command)
        
    def set_position(self,valuestr):
        """Set the position dial value to the specified value string
           - valuestr: string representing value to display; str
        """
        self.debug(4,f'Setting the position string to {valuestr}.')
        # execute command (defined in mixer preset)
        command = f'sp("{valuestr}")'
        # we assume SYSEX_LUA_COMMAND_MAX_LENGTH is big enought to hold this
        self._send_lua_command(command)

    def set_loop_start(self,valuestr):
        """Set the loop start dial value to the specified value string
           - valuestr: string representing value to display; str
        """
        self.debug(4,f'Setting the loop start string to {valuestr}.')
        # execute command (defined in mixer preset)
        command = f'ls("{valuestr}")'
        # we assume SYSEX_LUA_COMMAND_MAX_LENGTH is big enought to hold this
        self._send_lua_command(command)
        
    def set_loop_length(self,valuestr):
        """Set the loop length dial value to the specified value string
           - valuestr: string representing value to display; str
        """
        self.debug(4,f'Setting the loop length string to {valuestr}.')
        # execute command (defined in mixer preset)
        command = f'll("{valuestr}")'
        # we assume SYSEX_LUA_COMMAND_MAX_LENGTH is big enought to hold this
        self._send_lua_command(command)

    def _join_lua_list_chunks(self,l,prefix):
        """Join the list of strings into strings using commas, each no longer
           than SYSEX_LUA_COMMAND_MAX_LENGTH - len(prefix);
           (no limit if maxlen < SYSEX_LUA_COMMAND_MAX_LENGTH)
           - l: list of strings; [str]
           - prefix: prefix; length of which to subtract from maximum length; int
           - result: list of strings; [str]
        """
        if ElectraOneBase.SYSEX_LUA_COMMAND_MAX_LENGTH < 0:
            res = [ ','.join(l) ]
        else:
            maxlen = ElectraOneBase.SYSEX_LUA_COMMAND_MAX_LENGTH - len(prefix)
            self.debug(5,f'Join {l} using {maxlen}.')
            res = []
            i = 0
            while i < len(l):
                j = i
                s = ''
                while (j < len(l)) and (len(s) + len(l[j]) <= maxlen):
                    s = s + ',' + l[j]
                    j += 1
                if j > i:
                    self.debug(5,f'Joining string of length {len(s)-1}.')
                    res.append(s[1:]) # skip first comma
                    i = j
                else:
                    self.debug(5,f'String {l[i]} skipped (length {len(l[i])}).')
                    i = j+1
        return res

    def update_device_selector_for(self,idx,devicenames):
        """Set the device selector for the specified track.
           - idx: index of the track (starting at 0;
               NO_OF_TRACKS is first return track; NO_TRACKS+MAX_NO_OF_SENDS is master)
           - devicename: list of devicenames on this track; [str]
        """
        # convert list of devicenames to a LUA style list
        # truncate devicenames to 14 characters
        strs = [ f'"{n[:14]}"' for n in devicenames ]
        # then join the elements, making sure the resulting strings do not
        # exceed SYSEX_LUA_COMMAND_MAX_LENGTH when sent later
        chunks = self._join_lua_list_chunks(strs,'oca({})')
        self.debug(4,f'Setting the device selector for track/return/master {idx} to {chunks}.')
        # execute commands (defined in mixer preset)
        # send namelist in chunks to handle SYSEX_LUA_COMMAND_MAX_LENGTH
        command = f'oci()' 
        self._send_lua_command(command)
        for chunk in chunks:
            command = f'oca({{{chunk}}})' # {{ adds a {
            self._send_lua_command(command)
        command = f'ocd({idx})' 
        self._send_lua_command(command)
        
    def update_session_control(self,idx,clipinfo):
        """Update the session control matrix for the specified track.
           - idx: index of the track (starting at 0;
           - clipinfo: list of (name,color) string tuples, one for each slot
               (colour '0' and name '' indicate an empty clip slot
        """
        # convert list of (name,color) tuples to a LUA style list
        # first convert list of tuples into list of strings for each tuple
        # while truncating clipnames to 14 characters
        strs = [ f'"{n[:14]}",{c}' for (n,c) in clipinfo ]
        # then join the elements, making sure the resulting strings do not
        # exceed SYSEX_LUA_COMMAND_MAX_LENGTH when sent later
        chunks = self._join_lua_list_chunks(strs,'scua({})')
        self.debug(4,f'Setting the session control matrix for track {idx} to {chunks}.')
        # execute commands (defined in mixer preset)
        # send clipinfo in chunks to handle SYSEX_LUA_COMMAND_MAX_LENGTH
        command = f'scui()'
        self._send_lua_command(command)
        for chunk in chunks:
            command = f'scua({{{chunk}}})' # {{ adds a {
            self._send_lua_command(command)
        command = f'scud({idx})' 
        self._send_lua_command(command)
        
    def send_value_update(self, cid, vid, valuestr):
        """Send a value update for a control in the currently displayed patch
           on the E1.
           - cid: control id in the preset; int
           - vid: value id in the preset; int (0 for simple controls)
           - valuestr: string representing value to display; str
        """
        self.debug(4,f'Send value update {valuestr} for control ({cid},{vid}).')
        # see https://docs.electra.one/developers/midiimplementation.html#override-value-text
        assert cid in range(1,433), f'Control id {cid} out of range.' 
        assert vid in range(17), f'Value id {vid} out of range.' 
        sysex_command = (0x14, 0x0E)
        sysex_controlid = (cid % 128 , cid // 128)
        sysex_valueid = (vid, ) 
        sysex_text = self._ascii_bytes(valuestr)
        # this SysEx command repsonds with an ACK/NACK 
        self._increment_acks_pending()
        self._send_midi_sysex(sysex_command, sysex_controlid + sysex_valueid + sysex_text)
        time.sleep(ElectraOneBase._send_value_update_sleep) # don't overwhelm the E1!
        
    def setup_logging(self):
        """Enable or disable logging on the E1 (based on E1_LOGGING)
           and set the port over which logging messages are sent (based on
           E1_LOGGING_PORT).
           Also ensure controller events like preset slot changes are
           sent back over the E1_PORT so the remote script can listen
           and respond to them.
           NOTE: waits for receipt of ACK, so MUST only be called within a thread!
        """
        # Set the logging port
        if E1_LOGGING >= 0 :
            self.debug(1,'Enable logging on the E1.')
            # see https://docs.electra.one/developers/midiimplementation.html#set-the-midi-port-for-logger
            sysex_command = (0x14, 0x7D)
            sysex_port = (E1_LOGGING_PORT, 0x00)
            # this SysEx command repsonds with an ACK/NACK over the correct post since 3.1.4
            self._increment_acks_pending()
            self._send_midi_sysex(sysex_command, sysex_port)
        else:
            self.debug(1,'Disable logging on the E1.')
        # Enable/disable logging
        # see https://docs.electra.one/developers/midiimplementation.html#logger-enable-disable
        sysex_command = (0x7F, 0x7D)
        if E1_LOGGING >=0 :
            sysex_status = ( 0x01, E1_LOGGING )
        else:
            sysex_status = ( 0x00, 0x00 )
        ElectraOneBase.ack_received = False
        # this SysEx command repsonds with an ACK/NACK 
        self._increment_acks_pending()
        self._send_midi_sysex(sysex_command, sysex_status)
        # wait for it
        self.__wait_for_ack_or_timeout(0.05)
        # set the MIDI port for Controller events (to catch slot switching events)
        # https://docs.electra.one/developers/midiimplementation.html#set-the-midi-port-for-controller-events
        self.debug(1,f'Set E1 controller events port to {E1_PORT}.')
        sysex_command = (0x14, 0x7B)
        sysex_port = ( E1_PORT, )
        ElectraOneBase.ack_received = False
        # this SysEx command repsonds with an ACK/NACK 
        self._increment_acks_pending()
        self._send_midi_sysex(sysex_command, sysex_port)
        # wait for it
        self.__wait_for_ack_or_timeout(0.05)
            
    def activate_preset_slot(self, slot):
        """Select a slot on the E1 and activate the preset present there.
           - slot: slot to select; tuple of ints (bank: 0..5, preset: 0..1)
        """
        self.debug(4,f'Activating slot {slot}.')
        (bankidx, presetidx) = slot
        assert bankidx in range(6), f'Bank index {bankidx} out of range.'
        assert presetidx in range(12), f'Preset index {presetifx} out of range.'
        # see https://docs.electra.one/developers/midiimplementation.html#switch-preset-slot
        sysex_command = (0x09, 0x08)
        sysex_slot = (bankidx, presetidx)
        # this SysEx command repsonds with an ACK/NACK 
        self._increment_acks_pending()
        self._send_midi_sysex(sysex_command, sysex_slot)
        # Note: The E1 will in response send a preset changed message (7E 02)
        # (followed by an ack (7E 01)) whcih will set the visible slot and
        # start a refresh

    def remove_preset_from_slot(self, slot):
        """Remove the current preset (and its lua script) from a slot on the E1.
           - slot: slot to delete preset from; (bank: 0..5, preset: 0..1)
        """
        self.debug(4,f'Removing preset from slot {slot}.')
        (bankidx, presetidx) = slot
        assert bankidx in range(6), 'Bank index out of range.'
        assert presetidx in range(12), 'Preset index out of range.'
        # see https://docs.electra.one/developers/midiimplementation.html#preset-remove
        # Note: this also removes any lua script associated with the slot
        sysex_command = (0x05, 0x01)
        sysex_slot = (bankidx, presetidx)
        # this SysEx command repsonds with an ACK/NACK 
        self._increment_acks_pending()
        self._send_midi_sysex(sysex_command, sysex_slot)

    # --- preset upload thread and helper functions
    
    def __load_preloaded_preset(self, slot, preset_name):
        """Load a preloaded preset and associated luascript that are already
           preloaded on the E1 to the indicated slot. 
           - slot: slot to upload to; (bank: 0..5, preset: 0..1)
           - preset_name: name of the preset to load; str
        """
        self.debug(3,f'Loading preloaded preset for {preset_name} into slot {slot}.')
        (bankidx, presetidx) = slot
        assert bankidx in range(6), f'Bank index {bankidx} out of range.'
        assert presetidx in range(12), f'Preset index {presetifx} out of range.'
        # see https://docs.electra.one/developers/midiimplementation.html#load-preloaded-preset
        sysex_command = (0x04, 0x08)
        json = f'{{ "bankNumber": {bankidx}, "slot": {presetidx}, "preset": "{E1_PRESET_FOLDER}/{preset_name}" }}'
        sysex_json = self._ascii_bytes(json)
        # this SysEx command repsonds with an ACK/NACK 
        self._increment_acks_pending()
        self._send_midi_sysex(sysex_command, sysex_json)
        
    def __select_slot_only(self, slot):
        """Select a slot on the E1 but do not activate the preset already there.
           - slot: slot to select; tuple of ints (bank: 0..5, preset: 0..1)
        """
        self.debug(3,f'Selecting slot {slot}.')
        (bankidx, presetidx) = slot
        assert bankidx in range(6), f'Bank index {bankidx} out of range.'
        assert presetidx in range(12), f'Preset index {presetifx} out of range.'
        # (TODO: not documented yet!)
        sysex_command = (0x14, 0x08)
        sysex_slot = (bankidx, presetidx)
        # this SysEx command repsonds with an ACK/NACK
        self._increment_acks_pending()
        self._send_midi_sysex(sysex_command, sysex_slot)
        ElectraOneBase.current_visible_slot = slot
        # Unlike activate (see below) the E1 will not send a preset changed
        # message in response, but only an ACK

    def __upload_lua_script_to_current_slot(self, luascript):
        """Upload the specified LUA script to the currently selected slot on
           the E1 (use __select_slot_only to select the desired slot)
           - luascript: LUA script to upload; str
        """
        self.debug(3,f'Uploading LUA script:\n{luascript}.')
        # see https://docs.electra.one/developers/midiimplementation.html#upload-a-lua-script        
        sysex_command = (0x01, 0x0C)
        sysex_script = self._ascii_bytes(luascript)
        # this SysEx command repsonds with an ACK/NACK 
        self._increment_acks_pending()
        self._send_midi_sysex(sysex_command, sysex_script)

    def __upload_preset_to_current_slot(self, preset):
        """Upload the specified preset to the currently selected slot on
           the E1 (use __select_slot_only to select the desired slot)
           - preset: preset to upload; str (JASON, .epr format)
        """
        self.debug(3,f'Uploading preset (size {len(preset)} bytes).')
        # see https://docs.electra.one/developers/midiimplementation.html#upload-a-preset
        sysex_command = (0x01, 0x01)
        sysex_preset = self._ascii_bytes(preset)
        if not DUMP: # no need to write this to the log if the same thing is dumped
            self.debug(6,f'Preset = { preset }')
        # this SysEx command repsonds with an ACK/NACK 
        self._increment_acks_pending()
        self._send_midi_sysex(sysex_command, sysex_preset)

    
    def __upload_preset_thread(self, slot, preset_name, preset, luascript):
        """To be called as a thread. Select a slot, then load preloaded
           preset and luascript, or upload a preset and a lua script for it.
           In all cases wait (within a timeout) for confirmation from the E1.
           Reactivate the interface when done and request to rebuild the
           midi map.
           - slot: slot to upload to; (bank: 0..5, preset: 0..1)
           - preset_name: name of the preset to load; str
           - preset: preset to upload; str (JASON, .epr format)
           - luascript: LUA script to upload; str
        """
        # should anything happen inside this thread, make sure we write to debug
        try:
            self.debug(2,'Upload thread started...')
            # consume any stray pending ACKs or NACKs from previous commands
            # to clear the pending acks queue
            self.__clear_acks_queue()
            # try loading preloaded preset + lua first
            loaded = False
            if ElectraOneBase.E1_PRELOADED_PRESETS_SUPPORTED and USE_PRELOAD_FEATURE:
                self.__load_preloaded_preset(slot,preset_name)
                # don't wait to briefly; complex presets do take some time to load
                loaded = self.__wait_for_ack_or_timeout(1.00)
            # if loading preloaded preset failed upload preset
            # instead and wait for ACK                    
            if loaded:
                ElectraOneBase.current_visible_slot = slot
                ElectraOneBase.preset_upload_successful = True
            else:
                self.debug(3,'Loading preloaded preset failed; revert to upload.')
                # preloading failed: upload instead
                # first select slot and wait for ACK
                self.__select_slot_only(slot)
                if self.__wait_for_ack_or_timeout(0.010):
                    # upload preset
                    self.__upload_preset_to_current_slot(preset)
                    # timeout depends on patch complexity
                    # patch sizes range from 500 - 100.000 bytes
                    if self.__wait_for_ack_or_timeout( len(preset) * ElectraOneBase.PRESET_LENGTH_TIMEOUT_FACTOR ):
                        # preset uploaded, now upload lua script and wait for ACK
                        self.__upload_lua_script_to_current_slot(luascript)
                        if self.__wait_for_ack_or_timeout( len(luascript) * ElectraOneBase.LUA_LENGTH_TIMEOUT_FACTOR ):
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
                # rebuild midi map (will also refresh state) (this is why interface needs to be reaOUctivated first ;-)
                self.debug(2,'Upload thread requesting MIDI map to be rebuilt.')
                self.request_rebuild_midi_map()                
                self.debug(2,'Upload thread done.')
        except:
            ElectraOneBase.preset_uploading = False
            self.debug(1,f'Exception occured in upload thread {sys.exc_info()}')
        
    def upload_preset(self, slot, preset_name, preset, luascript):
        """Select a slot and upload a preset and associated luascript. First
           try to load a preloaded preset and associated luascript that are
           already preloaded on the E1, using preset_name.
           If that fails, upload the provided preset and luacsript.
           Returns immediately, but closes interface until preset fully loaded
           in the background. Once upload finished, the thread will request to
           rebuild the midi map.
           - slot: slot to upload to; (bank: 0..5, preset: 0..1)
           - preset_name: name of the preset to load; str
           - preset: preset to upload; str (JASON, .epr format)
           - luascript: LUA script to upload; str
        """
        # 'close' the interface until preset uploaded.
        ElectraOneBase.preset_uploading = True  # do this outside thread because thread may not even execute first statement before finishing
        ElectraOneBase.preset_upload_successful = False
        # thread also requests to rebuild MIDI map at the end (if successful), and this then calls refresh state
        self._upload_thread = threading.Thread(target=self.__upload_preset_thread,args=(slot,preset_name,preset,luascript))
        self._upload_thread.start()


        
    
        
