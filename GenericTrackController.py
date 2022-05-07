# GenericTrackController
# - Most of the functionality to control a audio/midi track, return track or
#   the master track.
#
# Part of ElectraOne
#
# Ableton Live MIDI Remote Script for the Electra One
#
# Author: Jaap-henk Hoepman (info@xot.nl)
#
# Distributed under the MIT License, see LICENSE
#
# DOCUMENTATION
#
# General idea of this module:
#
# Proper device parameters (sliders onlt really) are mapped directly to
# their associated MIDI cc_no on a specific channel (see build_midi_map)
# using Live.MidiMap.map_midi_cc.
# From then on value updates from AND to the E1 are handled automatically.
# The only thing to do is call _init_controller_values() once (to send
# the values currently held by the device parameters are sent to the E1 to
# birng them in sync.
#
# For all other controlled elements we need handlers (to handle incoming data
# from the E1 controller) and listeners (to send updates to the E1 controleer)
#
# - Handlers (see: _init_cc_handlers, receive_midi, build_midi_map)
# Link a (MIDI_channel,cc_no) pair to a handler function that must be
# called whenever the specfied midi CC message (7bit only) is sent by the E1.
# Uses Live.MidiMap.forward_midi_cc (see build_midi_map)
# which causes the specified MIDI message to be received through Receive_midi.
# The handler is then called with the received value. 
#
# - Listeners (see: _add/remove_listeners):
# Register a function to call whenever a Live element that is controlled
# changes state. Used for Live elements that cannot be mapped to Midi directly
# using Live.MidiMap.map_midi_cc (because Ableton doesn't model them as true
# device parameters.
#
# This class is the base class for TrackController, MasterController and
# ReturnController. The idea being that all three share a similar structure
# (they are all 'tracks') except that each of them has slightly different
# features. Which features are present is indicated through the definition of
# the corresponding CC parameter value in the __init__ constructor of the
# subclass (where the value ```None``` indicates a feature is missing).
#
# The GenericTrackController expects the subclass to define a method
# _my_cc that derives the actual CC parameter number to use for a particular
# instance of an audio/midi track (TrackController) or a return track
# (ReturnController).
#
# It also expects the subclasses to define _init_cc_handlers to set
# self._CC_HANDLERS to the required handlers. (This roundabout way is necessary
# because these handlers may depend on the particular instance of the track
# they manage and therefore need to call _my_cc() to obtain the correct CC
# parameter number.


# Ableton Live imports
import Live

# Local imports
from .config import *
from .PresetInfo import PresetInfo
from .ElectraOneBase import ElectraOneBase
from .EffectController import build_midi_map_for_device, update_values_for_device


class GenericTrackController(ElectraOneBase):
    """Manage a generic track
    """
    
    def __init__(self, c_instance):
        """Initialise a return controller for a generic track
        """
        ElectraOneBase.__init__(self, c_instance)
        # initialisations provided by derived classes
        self._track = None
        self._name = None
        # EQ device info
        self._eq_device_name = None # if None not present (ie all returns)
        self._eq_cc_map = None
        # midi info
        self._midichannel = None
        # sliders
        self._base_pan_cc = None
        self._base_volume_cc = None
        self._base_cue_volume_cc = None  # if None, not present (ie all non master tracks)
        self._sends_cc = None # if None, not present (ie all non audio/midi tracks)
        # buttons
        self._base_mute_cc = None # if None, not present (i.e. master track)
        self._base_arm_cc = None # if None, not present (i.e. groups and returns)
        self._base_solo_cue_cc = None # if None, not present (i.e. all non audio/midi tracks)
        #
        self.debug(0,'GenericTrackController loaded.')

        
    # --- helper functions ---

    
    def _my_cc(self,base_cc):
        # derive the actual cc_no from the assigned base CC and my index
        # to be defined by subclass
        pass

    def _my_channel_eq(self):
        # Return a reference to the Channel EQ device on my track, if present.
        # None if not
        devices = self._track.devices
        for d in devices:
            if d.class_name == self._eq_device_name:
                self.debug(4,'ChannelEq (or similar) device found')
                return d
        return None

    def _my_channel_eq_preset_info(self):
        # add the offset to the cc_no present in TRACK_EQ_CC_MAP
        cc_map = {}
        for p in self._eq_cc_map:
            (channel, is_cc14, cc_no) = self._eq_cc_map[p]
            cc_map[p] = (channel, is_cc14, self._my_cc(cc_no))
        return PresetInfo('',cc_map)

    def refresh_state(self):
        # send the values of the controlled elements to the E1 (to bring them in sync)
        # called and initiated by MixerController
        track = self._track
        if self._base_mute_cc != None:
            self._on_mute_changed()
        if self._base_arm_cc != None:
            self._on_arm_changed()
        if self._base_solo_cue_cc != None:
            self._on_solo_cue_changed()
        self.send_parameter_as_cc14(track.mixer_device.panning, self._midichannel, self._my_cc(self._base_pan_cc))
        self.send_parameter_as_cc14(track.mixer_device.volume, self._midichannel, self._my_cc(self._base_volume_cc))
        if self._base_cue_volume_cc:  # master track only
            self.send_parameter_as_cc14(track.mixer_device.cue_volume, self._midichannel, self._my_cc(self._base_cue_volume_cc))
        # send sends
        if self._sends_cc != None: # audio/midi track only
            # note: if list is shorter, less sends included
            sends = track.mixer_device.sends[:MAX_NO_OF_SENDS]
            cc_no = self._my_cc(self._sends_cc)
            for send in sends:
                self.send_parameter_as_cc14(send,MIDI_SENDS_CHANNEL,cc_no)
                cc_no += NO_OF_TRACKS
        # send channel eq
        channel_eq = self._my_channel_eq()
        if channel_eq:
            preset_info = self._my_channel_eq_preset_info()
            update_values_for_device(channel_eq, preset_info,self)

    def update_display(self):
        pass
    
    def disconnect(self):
        # cleanup
        self._remove_listeners()

    # --- Listeners
    
    def _add_listeners(self):
        # add listeners for changes to Live elements
        track = self._track
        if self._base_mute_cc != None:
            track.add_mute_listener(self._on_mute_changed)
        if self._base_arm_cc != None: 
            track.add_arm_listener(self._on_arm_changed)
        if self._base_solo_cue_cc != None:
            track.add_solo_listener(self._on_solo_cue_changed)

    def _remove_listeners(self):
        # remove all listeners added
        track = self._track
        # track may already have been deleted
        if track:
            if self._base_mute_cc != None:
                track.remove_mute_listener(self._on_mute_changed)
            if self._base_arm_cc != None:
                track.remove_arm_listener(self._on_arm_changed)
            if self._base_solo_cue_cc != None:
                track.remove_solo_listener(self._on_solo_cue_changed)
        
    def _on_mute_changed(self):
        if self._base_mute_cc != None:
            if self._track.mute:
                value = 0
            else:
                value = 127
            self.send_midi_cc7(self._midichannel, self._my_cc(self._base_mute_cc), value)

    def _on_arm_changed(self):
        if self._base_arm_cc != None:
            if self._track.arm:
                value = 127
            else:
                value = 0
            self.send_midi_cc7(self._midichannel, self._my_cc(self._base_arm_cc), value)
    
    def _on_solo_cue_changed(self):
        # TODO not entirely clear whether this is what we want
        if self._base_solo_cue_cc != None:
            if self._track.solo:
                value = 127
            else:
                value = 0
            self.send_midi_cc7(self._midichannel, self._my_cc(self._base_solo_cue_cc), value)

    # --- Handlers ---
    
    def _init_cc_handlers(self):
        # define handlers for incpming midi events
        # to be defined by subclass
        pass
    
    def _handle_mute_button(self,value):
        self.debug(2,f'Track { self._name } activation button action.')
        if self._base_mute_cc != None:
            self._track.mute = (value < 64)

    def _handle_arm_button(self,value):
        self.debug(2,f'Return track { self._name } arm button action.')
        if self._base_arm_cc != None:
            self._track.arm = (value > 63)

    def _handle_solo_cue_button(self,value):
        self.debug(2,f'Return track { self._name } solo/cue button action.')
        if self._base_solo_cue_cc != None:
            self._track.solo = (value > 63)

    # --- MIDI ---
    
    def process_midi(self, midi_channel, cc_no, value):
        # receive incoming midi events and pass them to the correct handler
        self.debug(5,f'GenericTrackControler: trying to process MIDI by track { self._name}.')
        if (midi_channel,cc_no) in self._CC_HANDLERS:
            handler = self._CC_HANDLERS[(midi_channel,cc_no)]
            if handler:
                self.debug(5,f'GenericTrackController: handler found.')
                handler(value)
    
    def build_midi_map(self, script_handle, midi_map_handle):
        self.debug(2,f'Building MIDI map of track { self._name }.')
        # Map btton CCs to be forwarded as defined in MIXER_CC_HANDLERS
        for (midi_channel,cc_no) in self._CC_HANDLERS:
            Live.MidiMap.forward_midi_cc(script_handle, midi_map_handle, midi_channel - 1, cc_no)
        # map main sliders
        # TODO/FIXME: not clear how this is honoured in the Live.MidiMaap.map_midi_cc call
        needs_takeover = True
        map_mode = Live.MidiMap.MapMode.absolute_14_bit
        track = self._track
        self.debug(3,f'Mapping track { self._name } pan to CC { self._my_cc(self._base_pan_cc) } on MIDI channel { self._midichannel }')
        Live.MidiMap.map_midi_cc(midi_map_handle, track.mixer_device.panning, self._midichannel-1, self._my_cc(self._base_pan_cc), map_mode, not needs_takeover)
        Live.MidiMap.map_midi_cc(midi_map_handle, track.mixer_device.volume, self._midichannel-1, self._my_cc(self._base_volume_cc), map_mode, not needs_takeover)
        if self._base_cue_volume_cc != None:  # master track only
            Live.MidiMap.map_midi_cc(midi_map_handle, track.mixer_device.cue_volume, self._midichannel-1, self._my_cc(self._base_cue_volume_cc), map_mode, not needs_takeover)
        # map sends (if present)
        if self._sends_cc != None:
            sends = track.mixer_device.sends[:MAX_NO_OF_SENDS]
            cc_no = self._my_cc(self._sends_cc)
            for send in sends:
                self.debug(3,f'Mapping send to CC { cc_no } on MIDI channel { MIDI_SENDS_CHANNEL }')
                Live.MidiMap.map_midi_cc(midi_map_handle, send, MIDI_SENDS_CHANNEL-1, cc_no, map_mode, not needs_takeover)
                cc_no += NO_OF_TRACKS
        # map ChannelEq (if present)
        channel_eq = self._my_channel_eq()
        if channel_eq:
            build_midi_map_for_device(midi_map_handle, channel_eq, self._my_channel_eq_preset_info(), self.debug)

   
        
   
