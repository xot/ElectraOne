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
import threading
import time
import sys
import os
import string

# Local imports
from .config import *
from .Log import Log

# --- MIDI CC handling

# CC status nibble
CC_STATUS = 0xB0

# SysEx incoming commands (as defined by the E1 firmware)
# All SysEx commands start with E1_SYSEX_PREFIX and are terminated by SYSEX_TERMINATE
E1_SYSEX_PREFIX = (0xF0, 0x00, 0x21, 0x45)
SYSEX_TERMINATE = (0xF7, )

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

# possible values for ack_or_nack_received
ACK_RECEIVED = 0
NACK_RECEIVED = 1

class ElectraOneBase(Log):
    """E1 base class with common functions
       (interfacing with Live through c_instance).
    """
    # This is the base class for all other classes in this package, and
    # therefore several instances of it are created.

    # -- CLASS variables (exist exactly once, only inside this class)
    
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
    
    # --- LIBDIR handling

    def _get_libdir(self):
        """Determine library path based on LIBDIR.
           Either ~/LIBDIR, /LIBDIR, or the user home directory,
           the first of these that exist. (Home is assumed to always exist.)
           - result: library path that exists (without trailing /) ; str
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
        # create if path does not exist
        if not os.path.exists(test):
            os.mkdir(test)
        elif not os.path.isdir(test):
                return ''
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
        Log.__init__(self, c_instance)
        
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

    def _find_first_rack(self,torc):
        for d in torc.devices:
            self.debug(6,f'Considering {d.name}')
            if type(d) == Live.RackDevice.RackDevice:
                self.debug(5,f'Rack found: {d.name}')
                return d
        return None

    def _visible_chains_for_torc(self,torc):
        """Return the visible chains for this track or chain
        """
        chains = []
        rack = self._find_first_rack(torc)
        if rack and rack.can_show_chains and rack.is_showing_chains:
            for chain in rack.chains:
                chains.append(chain)
                chains.extend( self._visible_chains_for_torc(chain) )
        return chains

    def get_visible_torcs(self):
        """Return the currently visible chains and tracks
           song: current song; Live.Song.Song
        """
        torcs = []
        for t in self.song().visible_tracks:
            self.debug(5,f'Getting visible torcs for {t.name}')
            torcs.append(t)
            torcs.extend( self._visible_chains_for_torc(t) )
        for torc in torcs:
            self.debug(5,f'Visible torc {torc.name}')
        return torcs    
    
    def request_rebuild_midi_map(self):
        """Request that the MIDI map is rebuilt.
           (The old mapping is (apparently) destroyed.)
        """
        self.debug(2,'Rebuilding MIDI map requested')
        self._c_instance.request_rebuild_midi_map()

    def get_device_name(self, device):
        """Return the (fixed) name of the device (i.e. not the name of the preset)
           - device: the device; Live.Device.Device
           - result: device name; str
        """
        # For native devices and instruments, device.class_name is the name of
        # the device/instrument, and device.name equals the selected preset
        # (or the device/instrumettn name).
        # For plugins and max devices however, device.class_name is useless
        # To reliably identify preloaded presets by name for such devices
        # as well, embed them into a audio/instrument rack and give that rack
        # the name of the device.
        # For racks themselves, device.class_name is also useless, so use
        # device.name instead
        # To distinguish names for plugins/max devices (for which we derive
        # the name from the enclosing rack) from the name of the enclosing
        # rack itself, append a hypen to the name to the derived plugin/max name
        self.debug(6,f'Getting name for device with class_name { device.class_name } as device name. Aka name: { device.name } and class_display_name: { device.class_display_name }, (has type { type(device) }).')
        if device.class_name in ('AuPluginDevice', 'PluginDevice', 'MxDeviceMidiEffect', 'MxDeviceInstrument', 'MxDeviceAudioEffect'):
            cp = device.canonical_parent
            if isinstance(cp,Live.Chain.Chain):
                cp = cp.canonical_parent
                self.debug(6,'Enclosing rack found, using its name.')
                name = cp.name + '-'
            else:
                self.debug(6,'No enclosing rack found, using my own name (unreliable).')
                name = device.name
        elif device.class_name in ('InstrumentGroupDevice','DrumGroupDevice','MidiEffectGroupDevice','AudioEffectGroupDevice'):
            self.debug(6,'I am a rack, using my own name (unreliable).')
            name = device.name
        else:
            name = device.class_name
        self.debug(5,f'Device name is { name }.')
        return name
    
    # --- dealing with fimrware versions

    # E1 software version info as a tuple of integers (major, minor, sub).
    _E1_sw_version = (0,0,0)

    # E1 hardware version info as a tuple of integers (major, minor).
    _E1_hw_version = (0,0)

    # Record whether attached version of E1 is supported by the remote script
    E1_version_supported = False

    # Record whether E1 will forward ACKs from anotehr E1 attached to it
    E1_FORWARDS_ACK = False

    # Record whether E1 supports preloaded presets on the E1 itself
    E1_PRELOADED_PRESETS_SUPPORTED = False

    # Minimum and maximum timeouts to wait for an ACK
    MIN_TIMEOUT = 0
    MAX_TIMEOUT = 0

    # Time to sleep between MIDI CC and LUA value update messages in normal mode
    MIDI_SLEEP = 0
    VALUE_UPDATE_SLEEP = 0

    # Time to sleep between MIDI CC and LUA value update messages in burst mode
    BURST_MIDI_SLEEP = 0
    BURST_VALUE_UPDATE_SLEEP = 0 

    # Time to sleep after turning on/off burst mode
    BURST_ON_OFF_SLEEP = 0

    # Factor to divide patch/lua-script length to compute lenght dependent timeout
    TIMEOUT_LENGTH_FACTOR = 1
    
    def configure_for_version(self, sw_version, hw_version):
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
            ElectraOneBase.E1_FORWARDS_ACK = (sw_version >= (3,2,0))
            ElectraOneBase.E1_PRELOADED_PRESETS_SUPPORTED = (sw_version >= (3,4,0)) 
            # set hwardware dependent options
            # TODO: set proper timings
            if hw_version >= (3,0): # mkII
                ElectraOneBase.MIN_TIMEOUT = 60 # TODO this is large
                ElectraOneBase.MAX_TIMEOUT = 300
                ElectraOneBase.MIDI_SLEEP = 0 # 0.1 
                ElectraOneBase.VALUE_UPDATE_SLEEP = 0 
                ElectraOneBase.BURST_MIDI_SLEEP = 0 # 0.1 
                ElectraOneBase.BURST_VALUE_UPDATE_SLEEP = 0
                ElectraOneBase.BURST_ON_OFF_SLEEP = 0.1                 
                ElectraOneBase.TIMEOUT_LENGTH_FACTOR = 100
                self.show_message(f'E1 mk II, with firmware {sw_version} detected.')
            else: # mkI
                ElectraOneBase.MIN_TIMEOUT = 60
                ElectraOneBase.MAX_TIMEOUT = 250                 
                ElectraOneBase.MIDI_SLEEP = 0
                ElectraOneBase.VALUE_UPDATE_SLEEP = 0 
                ElectraOneBase.BURST_MIDI_SLEEP = 0
                ElectraOneBase.BURST_VALUE_UPDATE_SLEEP = 0 
                ElectraOneBase.BURST_ON_OFF_SLEEP = 0.01                 
                ElectraOneBase.TIMEOUT_LENGTH_FACTOR = 50
                self.show_message(f'E1 mk I, with firmware {sw_version} detected.')
                
    def set_version(self, sw_versionstr, hw_versionstr):
        """Set the E1 firmware version.
           - sw_versionstr: software version string as returned by request response; str
           - hw_versionstr: software version string as returned by request response; str
        """
        # see https://docs.electra.one/developers/midiimplementation.html#get-an-electra-info
        # parse software version string
        # sw_versionstr format "v<major>.<minor>.<sub>" (sub somtimes missing; sub sometimes including trailing letter)
        try:
            version_tuple = sw_versionstr[1:].split('.')
            if len(version_tuple) == 3:
                (majorstr,minorstr,substr) = version_tuple
                # remove any trailing letters from version string
                if substr[-1] not in string.digits:
                    substr = substr[:-1]
                sw_version = (int(majorstr),int(minorstr),int(substr))
            elif len(version_tuple) == 2:
                (majorstr,minorstr) = version_tuple
                sw_version = (int(majorstr),int(minorstr),0)
            else:
                sw_version = (0,0,0)
        except ValueError:
            self.debug(2,f'Failed to parse software version string { sw_versionstr }.')
            ElectraOneBase._E1_sw_version = (0,0,0)
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
            ElectraOneBase._E1_hw_version = (0,0)
        self.configure_for_version(sw_version,hw_version)
        self.debug(2,f'E1 version {sw_version} (software) { hw_version } (hardware).')
        
    # --- Fast MIDI sysex upload handling

    # Unfortunately, Ableton appears not to support subporcess. Importing
    # subprocess raises the error
    #    No module named '_posixsubprocess'
    def _run_command(self, command):
        """Run the command in a shell, and return whether succesful.
           - command: command to run; str
           - result: return whether succesful; bool
        """
        self.debug(5,f'Running external command {command[:40]}')
        self.debug(6,f'Running external command {command[:200]}')
        # os,system returns 0 for success on both MacOS and Windows
        return_code = os.system(command)
        self.debug(5,f'External command on OS {os.name} returned {return_code}')        
        return (return_code == 0)

    def setup_fast_sysex(self):
        """Set up fast sysex upload.
        """
        # Do this only once.
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
    # Call this *before* sending out the SysEx that expects an ACK as response
    # to avoid a race condition where the ACK is received before the counter
    # is incremented, and hence the __wait_for_ack_or_timeout() fails

    def _increment_acks_pending(self):
        """Increment the number of pending ACKs by 1.
           (See ACK/NACK received functions in ElectraOne, and
            __wait_for_ack_or_timeout() below.)
        """
        ElectraOneBase.acks_pending += 1
        now = time.time()
        ElectraOneBase.acks_pending_incremented_time = now
        self.debug(4,f'ACKS pending incremented to {ElectraOneBase.acks_pending} at time { now }')

    def _adjust_timeout(self,timeout):
        """Adjust the timeout depending on whether fast sysex sending is
           suported or not, and whether logging of E1 messages is enabled.
           - timeout: time to wait (in 'units', ranging from 5-1000), equals
             the time in 10ms units to wait when fast sysex loading is enabled
             and no logging takes place on the E1; int
           result: timeout in (fractional) seconds
        """
        # cap timeout to maximum
        timeout = min(timeout,ElectraOneBase.MAX_TIMEOUT) 
        # stretch timeout when no fast sysex uploading
        if not ElectraOneBase._fast_sysex:
            timeout = 8 * timeout
        # also stretch (further) if logging takes place
        if E1_LOGGING >=0 :
            timeout = (1 + E1_LOGGING) * timeout
        if E1_LOGGING_PORT == E1_PORT:
            timeout = 2 * timeout
        # minimum timeout is 1000ms
        timeout = max(ElectraOneBase.MIN_TIMEOUT,timeout)
        # convert to (fractional) seconds
        return timeout/100
        
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
        start_time = time.time()
        end_time = ElectraOneBase.acks_pending_incremented_time + 4.0
        self.debug(4,f'Thread clearing acks queue ({ElectraOneBase.acks_pending} pending) on {start_time:.3f}, wait until {end_time:.3f} (preset uploading: {ElectraOneBase.preset_uploading}).')
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
           - timeout: time to wait (in 'units', ranging from 5-1000); int
        """
        timeout = self._adjust_timeout(timeout)
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

    def send_parameter_as_cc7(self, p, channel, cc_no):
        """Send the value of a Live parameter as a 7bit MIDI CC message 
           (through Ableton Live)
           - p : Ableton Live parameter; Live.DeviceParameter.DeviceParameter
           - channel: MIDI Channel; int (1..16)
           - cc_no: CC parameter number; int (0..127)
        """
        self.debug(4,f'Sending value for {p.original_name} ({p.name}) over MIDI channel {channel} as CC parameter {cc_no} in 7bit.')
        if p.is_quantized:
            idx = int(p.value)
            value = cc_value_for_item_idx(idx,p.value_items)
        else:
            value = cc_value(p,127)
        self.send_midi_cc7(channel, cc_no, value)

    def send_parameter_as_cc14(self, p, channel, cc_no):
        """Send the value of a Live parameter as a 14bit MIDI CC message 
           (through Ableton Live).
           - p : Ableton Live parameter; Live.DeviceParameter.DeviceParameter
           - channel: MIDI Channel; int (1..16)
           - cc_no: CC parameter number; int (0..127)
        """
        self.debug(4,f'Sending value for {p.original_name} over MIDI channel {channel} as CC parameter {cc_no} in 14bit.')
        value = cc_value(p,16383)
        self.send_midi_cc14(channel, cc_no, value)

    def send_parameter_using_ccinfo(self, p, ccinfo):
        """Send the value of Live a parameter as a MIDI CC message 
           (through Ableton Live, using CC info to determine where and how).
           - parameter: Ableton Live parameter; Live.DeviceParameter.DeviceParameter
           - ccinfo: CC information (channel, cc, bits) about the parameter; CCInfo
        """
        self.debug(4,f'Sending value for {p.original_name} over {ccinfo}.')
        channel = ccinfo.get_midi_channel()
        cc_no = ccinfo.get_cc_no()
        if ccinfo.is_cc14():
            self.send_parameter_as_cc14(p, channel, cc_no)
        else:
            self.send_parameter_as_cc7(p, channel, cc_no)                

    # --- MIDI SysEx handling ---

    def _safe_ord (self, c ):
        o = ord(c)
        if o > 127:
            o = ord('?')
            self.debug(5,f'UNICODE character {c} replaced.')
        return o
    
    def _E1_sysex(self, message):
        return E1_SYSEX_PREFIX + message + SYSEX_TERMINATE

    def _send_midi_sysex(self, message):
        """Send the command and parameters as a E1 sysex message (prepend
           header and append termination), using fast sysex sending if
           supported.
           - message: the MIDI message to send; sequence of bytes
        """
        sysex_message = self._E1_sysex(message)
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
            
    def send_e1_request(self):
        """Send a sysex request to the E1.
        """
        self.debug(4,f'Sending E1 sysex request.')
        # see https://docs.electra.one/developers/???
        sysex_command = (0x02, 0x7F)
        self._send_midi_sysex(sysex_command)
        # this command does not send an ack, but only a request_response
        
    def _send_lua_command(self, command):
        """Send a LUA command to the E1.
           - command: the command to send; str
        """
        self.debug(4,f'Sending LUA command {command}.')
        # see https://docs.electra.one/developers/luaext.html
        sysex_command = (0x08, 0x0D)
        sysex_lua = tuple([ self._safe_ord(c) for c in command ])
        # LUA commands respond with ACK/NACK
        self._increment_acks_pending()
        # in CONTROL_BOTH mode BOTH E1s send an ACK! (if the first E1 is at version 3.2.0
        # and this only affects all calls to _send_lua_command
        if (CONTROL_MODE == CONTROL_BOTH) and ElectraOneBase.E1_FORWARDS_ACK:
            self._increment_acks_pending()
        self._send_midi_sysex(sysex_command + sysex_lua)

    def midi_burst_on(self,command):
        """Prepare the script for a burst of updates; set a small delay
           to prevent clogging the E1, and disable window repaints.
           - command: command to use (addressing mixer or effect)
        """
        self.debug(4,'MIDI burst on.')
        # TODO: set proper timings; note that the current HW has 256k RAM
        # so the buffers are only 32 entries for sysex, and 128 non-sysex
        # So really what should be done is wait after filling all buffers in
        # a burst
        ElectraOneBase._send_midi_sleep = ElectraOneBase.BURST_MIDI_SLEEP
        ElectraOneBase._send_value_update_sleep = ElectraOneBase.BURST_VALUE_UPDATE_SLEEP 
        # defer drawing
        self._send_lua_command(command)
        # wait a bit to ensure the command is processed before sending actual
        # value updates (we cannot wait for the actual ACK)
        time.sleep(ElectraOneBase.BURST_ON_OFF_SLEEP) 
        
    def midi_burst_off(self,command):
        """Reset the delays, because updates are now individual. And allow
           immediate window updates again. Draw any buffered window repaints.
           - command: command to use (addressing mixer or effect)
        """
        self.debug(4,'MIDI burst off.')
        # wait a bit to ensure all MIDI CC messages have been processed
        # and all ACKs/NACks for LUA commands sent have been received
        time.sleep(ElectraOneBase.BURST_ON_OFF_SLEEP) 
        ElectraOneBase._send_midi_sleep = ElectraOneBase.MIDI_SLEEP
        ElectraOneBase._send_value_update_sleep = ElectraOneBase.VALUE_UPDATE_SLEEP
        # reenable drawing and update display
        self._send_lua_command(command)
        # wait a bit to ensure the command is processed
        # (we cannot wait for the actual ACK)
        time.sleep(ElectraOneBase.BURST_ON_OFF_SLEEP)

    def effect_midi_burst_on(self):
        """Tell effect to disable redraws to prepare for a burst of MIDI updated
        """
        self.midi_burst_on('aaa()')
        
    def effect_midi_burst_off(self):
        """Tell effect to reenable redraws, and update display to new state.
           No more MIDI burst.
        """
        self.midi_burst_off('zzz()')

    def mixer_midi_burst_on(self):
        """Tell mixer to disable redraws to prepare for a burst of MIDI updated
        """
        self.midi_burst_on('aa()')
        
    def mixer_midi_burst_off(self):
        """Tell mixer to reenable redraws, and update display to new state.
           No more MIDI burst.
        """
        self.midi_burst_off('zz()')
        
    def update_track_labels(self, idx, label):
        """Update the label for a track on all relevant pages
           in the currently selected mixer preset.
           - idx: index of the track (starting at 0); int
           - label: new text; str
        """
        assert idx in range(NO_OF_TRACKS), f'Track index {idx} out of range.' 
        self.debug(4,f'Update label for track {idx} to {label}.')
        command = f'utl({idx},"{label}")'
        self._send_lua_command(command)
        
    def update_return_sends_labels(self, returnidx, label):
        """Update the label for a return track and the associated send controls
           in the currently selected mixer preset.
           - returnidx: index of the return track (starting at 0); int
           - label: new text; str
        """
        assert returnidx in range(MAX_NO_OF_SENDS), f'Return index {returnidx} out of range.' 
        self.debug(4,f'Update label for return track {returnidx} to {label}.')
        command = f'ursl({returnidx},"{label}")'
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
        command = f'smv({tc},{rc})'
        self._send_lua_command(command)

    def set_channel_eq_visibility_on_track(self,idx,flag):
        """Set the visibility of the eq device for the specified track.
           - idx: index of the track (starting at 0; NO_OF_TRACKS for master track); int
           - flag: whether the eq-device should be visible; bool
        """
        assert idx in range(NO_OF_TRACKS+1), f'Track index {idx} out of range.' 
        self.debug(4,f'Setting channel equaliser visibility for track {idx} to {flag}.')
        if flag:
          command = f'seqv({idx},true)'
        else:
          command = f'seqv({idx},false)'
        self._send_lua_command(command)

    def send_value_update(self, cid, vid, valuestr):
        """Send a value update for a control in the currently displayed patch
           on the E1.
           - cid: control id in the preset; int
           - vid: value id in the preset; int (0 for simple controls)
           - valuestr: string representing value to display; str
        """
        self.debug(4,f'Send value update {valuestr} for control ({cid},{vid}).')
        sysex_command = (0x14, 0x0E)
        sysex_controlid = (cid % 128 , cid // 128)
        sysex_valueid = (vid, ) 
        sysex_text = tuple([ self._safe_ord(c) for c in valuestr ])
        # this SysEx command repsonds with an ACK/NACK 
        self._increment_acks_pending()
        self._send_midi_sysex(sysex_command + sysex_controlid + sysex_valueid + sysex_text)
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
        if E1_LOGGING >= 0:
            self.debug(1,'Enable logging.')
        else:
            self.debug(1,'Disable logging.')
        # Set the logging port
        if E1_LOGGING >= 0 :
            # see https://docs.electra.one/developers/midiimplementation.html#set-the-midi-port-for-logger
            sysex_command = (0x14, 0x7D)
            sysex_port = (E1_LOGGING_PORT, 0x00)
            # this SysEx command repsonds with an ACK/NACK over the correct post since 3.1.4
            self._increment_acks_pending()
            self._send_midi_sysex(sysex_command + sysex_port)
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
        self._send_midi_sysex(sysex_command + sysex_status)
        # wait for it
        self.__wait_for_ack_or_timeout(5)
        # set the MIDI port for Controller events (to catch slot switching events)
        # https://docs.electra.one/developers/midiimplementation.html#set-the-midi-port-for-controller-events
        self.debug(1,f'Set E1 controller events port to {E1_PORT}.')
        sysex_command = (0x14, 0x7B)
        sysex_port = ( E1_PORT, )
        ElectraOneBase.ack_received = False
        # this SysEx command repsonds with an ACK/NACK 
        self._increment_acks_pending()
        self._send_midi_sysex(sysex_command + sysex_port)
        # wait for it
        self.__wait_for_ack_or_timeout(5)
            
    def _select_slot_only(self, slot):
        """Select a slot on the E1 but do not activate the preset already there.
           - slot: slot to select; tuple of ints (bank: 0..5, preset: 0..1)
        """
        self.debug(4,f'Selecting slot {slot}.')
        (bankidx, presetidx) = slot
        assert bankidx in range(6), f'Bank index {bankidx} out of range.'
        assert presetidx in range(12), f'Preset index {presetifx} out of range.'
        # (TODO: not documented yet!)
        sysex_command = (0x14, 0x08)
        sysex_select = (bankidx, presetidx)
        # this SysEx command repsonds with an ACK/NACK
        self._increment_acks_pending()
        self._send_midi_sysex(sysex_command + sysex_select)
        ElectraOneBase.current_visible_slot = slot
        # Unlike activate (see below) the E1 will not send a preset changed
        # message in response, but only an ACK

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
        sysex_select = (bankidx, presetidx)
        # this SysEx command repsonds with an ACK/NACK 
        self._increment_acks_pending()
        self._send_midi_sysex(sysex_command + sysex_select)
        ElectraOneBase.current_visible_slot = slot
        # Note: The E1 will in response send a preset changed message (7E 02)
        # (followed by an ack (7E 01))

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
        sysex_select = (bankidx, presetidx)
        # this SysEx command repsonds with an ACK/NACK 
        self._increment_acks_pending()
        self._send_midi_sysex(sysex_command + sysex_select)
        
    def _load_preloaded_preset(self, slot, preset_name):
        """Load a preloaded preset and associated luascript that are already
           preloaded on the E1 to the indicated slot. 
           - slot: slot to upload to; (bank: 0..5, preset: 0..1)
           - preset_name: name of the preset to load; str
        """
        self.debug(4,f'Loading preloaded preset for {preset_name} into slot {slot}.')
        (bankidx, presetidx) = slot
        assert bankidx in range(6), f'Bank index {bankidx} out of range.'
        assert presetidx in range(12), f'Preset index {presetifx} out of range.'
        # see https://docs.electra.one/developers/midiimplementation.html#load-preloaded-preset
        sysex_command = (0x04, 0x08)
        json = f'{{ "bankNumber": {bankidx}, "slot": {presetidx}, "preset": "{E1_PRESET_FOLDER}/{preset_name}" }}'
        sysex_json = tuple([ self._safe_ord(c) for c in json ])
        # this SysEx command repsonds with an ACK/NACK 
        self._increment_acks_pending()
        self._send_midi_sysex(sysex_command + sysex_json)
        
    def _upload_lua_script_to_current_slot(self, luascript):
        """Upload the specified LUA script to the currently selected slot on
           the E1 (use _select_slot_only to select the desired slot)
           - luascript: LUA script to upload; str
        """
        self.debug(4,f'Uploading LUA script {luascript}.')
        # see https://docs.electra.one/developers/midiimplementation.html#upload-a-lua-script        
        sysex_command = (0x01, 0x0C)
        sysex_script = tuple([ ord(c) for c in luascript ])
        # this SysEx command repsonds with an ACK/NACK 
        self._increment_acks_pending()
        self._send_midi_sysex(sysex_command + sysex_script)

    def _upload_preset_to_current_slot(self, preset):
        """Upload the specified preset to the currently selected slot on
           the E1 (use _select_slot_only to select the desired slot)
           - preset: preset to upload; str (JASON, .epr format)
        """
        self.debug(4,f'Uploading preset (size {len(preset)} bytes).')
        # see https://docs.electra.one/developers/midiimplementation.html#upload-a-preset
        sysex_command = (0x01, 0x01)
        sysex_preset = tuple([ ord(c) for c in preset ])
        if not DUMP: # no need to write this to the log if the same thing is dumped
            self.debug(6,f'Preset = { preset }')
        # this SysEx command repsonds with an ACK/NACK 
        self._increment_acks_pending()
        self._send_midi_sysex(sysex_command + sysex_preset)

    
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
            self.debug(2,'Upload thread starting...')
            # consume any stray pending ACKs or NACKs from previous commands
            # to clear the pending acks queue
            self.__clear_acks_queue()
            # try loading preloaded preset + lua first
            loaded = False
            if ElectraOneBase.E1_PRELOADED_PRESETS_SUPPORTED:
                self._load_preloaded_preset(slot,preset_name)
                # don't wait to briefly; complex presets do take some time to load
                loaded = self.__wait_for_ack_or_timeout(50)
            # if loading preloaded preset failed upload preset
            # instead and wait for ACK                    
            if loaded:
                ElectraOneBase.current_visible_slot = slot
                ElectraOneBase.preset_upload_successful = True
            else:
                self.debug(2,'Loading preloaded presdet failed; revert to upload.')
                # preloading failed: upload instead
                # first select slot and wait for ACK
                self._select_slot_only(slot)
                if self.__wait_for_ack_or_timeout(10):
                    # upload preset
                    self._upload_preset_to_current_slot(preset)
                    # timeout depends on patch complexity
                    # patch sizes range from 500 - 100.000 bytes
                    if self.__wait_for_ack_or_timeout( int(len(preset)/ElectraOneBase.TIMEOUT_LENGTH_FACTOR) ):
                        # preset uploaded, now upload lua script and wait for ACK
                        self._upload_lua_script_to_current_slot(luascript)
                        if self.__wait_for_ack_or_timeout( 10*int(len(luascript)/ElectraOneBase.TIMEOUT_LENGTH_FACTOR) ):
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


        
    
        
