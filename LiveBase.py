# LiveBase
# - Base class with common Live functions and interface to Live
#
# Part of ElectraOne
#
# Ableton Live MIDI Remote Script for the Electra One
#
# Author: Jaap-henk Hoepman (info@xot.nl)
#
# Distributed under the MIT License, see LICENSE
#

import Live

# Python imports
from pathlib import Path
import inspect

# Local imports
#from .config import *
from .Log import Log


class LiveBase(Log):
    """Live base class with common functions
       (interfacing with Live through c_instance).
    """

    # -- CLASS variables (exist exactly once, only inside this class)

    # Path to where this remote script is installed
    REMOTE_SCRIPT_PATH = None
    
    # --- INIT
    
    def __init__(self, c_instance):
        """Initialise.
           - c_instance: Live interface object (see __init.py__)
        """
        Log.__init__(self, c_instance)
        # get the path to this remote script instance
        if not LiveBase.REMOTE_SCRIPT_PATH:
            LiveBase.REMOTE_SCRIPT_PATH = Path(inspect.getfile(LiveBase)).parent
        

    # --- standard folders and files

    def dumppath(self):
        """Folder to dump presets in
           - result:  ; Path
        """
        return LiveBase.REMOTE_SCRIPT_PATH / 'dumps'

    def preloadedpath(self):
        """Folder to load predefined presets from
           - result:  ; Path
        """
        return LiveBase.REMOTE_SCRIPT_PATH / 'preloaded'
    
    def luascriptfname(self):
        """Filename to load default LUA script from
           - result:  ; Path
        """
        return LiveBase.REMOTE_SCRIPT_PATH / 'default.lua'
    
    # --- helper functions (Live API)
    
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

    def toggle_lock(self):
        """Toggle device appointment locking
        """
        self._c_instance.toggle_lock()
        
    def script_handle(self):
        """Return a reference to the main object of this remote script
        """
        return self._c_instance.handle()
        
    def set_session_highlight(self,track,row,width,height,flag):
        """Set the session highlight in the session view
           - track: index of first track; int
           - row: index of first row; int
           - width: int
           - height: int
           - flag: bool
        """
        self._c_instance.set_session_highlight(track,row,width,height,flag)
    
    # --- get list of visible  tracks/chains
    
    def _dump_track_info(self,t):
        """For debugging
        """
        self.debug(6,f'Track {t.name}:')
        self.debug(7,f'Is visible = {t.is_visible}')
        self.debug(7,f'Is grouped = {t.is_grouped}')                
        self.debug(7,f'Can show chains = {t.can_show_chains}')
        self.debug(7,f'Is showing chains = {t.is_showing_chains}')
        self.debug(7,f'Is foldable = {t.is_foldable}')        
        if t.is_foldable:
            self.debug(7,f'Fold state = {t.fold_state}')        
    
    def _find_first_rack(self,torc):
        for d in torc.devices:
            self.debug(7,f'find_first_rack considering {d.name}')
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
        # and is_showing_chains == False, so this fails for
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
            self._dump_track_info(t)
            torcs.append(t)
            torcs.extend( self._visible_chains_for_torc(t) )
        self.debug(6,f'Visible tracks or chains:')
        for torc in torcs:
            self.debug(6,f'{torc.name}')
        return torcs

    # --- other helper functions

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
    
