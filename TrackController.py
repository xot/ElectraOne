# TrackController
# - control one track
#
# Part of ElectraOne
#
# Ableton Live MIDI Remote Script for the Electra One
#
# Author: Jaap-henk Hoepman (info@xot.nl)
#
# Distributed under the MIT License, see LICENSE

# Ableton Live imports
import Live

# Local imports
from .config import *
from .PresetInfo import PresetInfo
from .ElectraOneBase import ElectraOneBase, cc_value_for_item_idx
from .EffectController import build_midi_map_for_device, update_values_for_device

# CCs (see MixerController.py)
# These are base values, to which TRACKS_FACTOR is added for each next return track
PAN_CC = 0
VOLUME_CC = 5
MUTE_CC = 116   
SOLO_CUE_CC = 84
ARM_CC = 89
#

# Sends (on MIDI_SENDS_CHANNEL)
SENDS_CC = 0  # code below assumes all sends are mapped after each other, ie with increments of NO_OF_TRACKS=5

# TODO: Handle tracks that cannot be armed
# TODO: Handle track names
# TODO: hide/gray out unmapped sends

# Change this to managa a different EQ like device on every track
# TODO: move this to devices
#
# Specify the device.class_name here
TRACK_EQ_DEVICE_NAME = 'ChannelEq'
#
# Specify the CC-map here (like in Devices.py)
# The only rule is that the actual cc_no for a parameter is obtained
# by adding the offset to the base defined here
TRACK_EQ_CC_MAP = { # 'Device On': (MIDI_TRACKS_CHANNEL,0,-1)
              'Highpass On': (MIDI_TRACKS_CHANNEL, 0, 121)
            , 'Low Gain': (MIDI_TRACKS_CHANNEL, 1, 25)
            , 'Mid Gain': (MIDI_TRACKS_CHANNEL, 1, 20)
            , 'Mid Freq': (MIDI_TRACKS_CHANNEL, 1, 15)
            , 'High Gain': (MIDI_TRACKS_CHANNEL, 1, 10)
            , 'Gain': (MIDI_TRACKS_CHANNEL, 0, 64)
            }


class TrackController(ElectraOneBase):
    """Manage an audio or midi track.
    """
    
    def __init__(self, c_instance, idx, offset):
        """Initialise a return controller for track idx
        """
        ElectraOneBase.__init__(self, c_instance)
        # index of this track in self.song().visible_tracks
        self._idx = idx
        # offset of this track relative to the first mapped track
        self._offset = offset
        self._add_listeners()
        self._init_cc_handlers()
        self._value_update_timer = 5 # delay value updates until MIDI map ready
        self.debug(0,'TrackController loaded.')

    # --- helper functions ---
    
    def _track(self):
        # retrun a reference to the track managed
        return self.song().visible_tracks[self._idx]

    def _my_cc(self,base_cc):
        # derive the actual cc_no from the assigned base CC and my index
        return base_cc + self._offset

    def _my_channel_eq(self):
        # Return a reference to the Channel EQ device on my track, if present.
        # None if not
        devices = self._track().devices
        for d in devices:
            if d.class_name == TRACK_EQ_DEVICE_NAME:
                self.debug(4,'ChannelEq (or similar) device found')
                return d
        return None

    def _my_channel_eq_preset_info(self):
        # add the offset to the cc_no present in TRACK_EQ_CC_MAP
        cc_map = {}
        for p in TRACK_EQ_CC_MAP:
            (channel, is_cc14, cc_no) = TRACK_EQ_CC_MAP[p]
            cc_map[p] = (channel, is_cc14, self._my_cc(cc_no))
        return PresetInfo('',cc_map)

    def refresh_state(self):
        # send the values of the controlled elements to the E1 (to bring them in sync)
        self._on_mute_changed()
        if track.can_be_armed: # group track cannot!
            self._on_arm_changed()         
        self._on_solo_cue_changed()
        track = self._track()
        self.send_parameter_as_cc14(track.mixer_device.panning, MIDI_TRACKS_CHANNEL, self._my_cc(PAN_CC))
        self.send_parameter_as_cc14(track.mixer_device.volume, MIDI_TRACKS_CHANNEL, self._my_cc(VOLUME_CC))
        # send sends
        # note: if list is shorter, less sends included
        sends = track.mixer_device.sends[:MAX_NO_OF_SENDS]
        cc_no = self._my_cc(SENDS_CC)
        for send in sends:
            self.send_parameter_as_cc14(send,MIDI_SENDS_CHANNEL,cc_no)
            cc_no += NO_OF_TRACKS
        # send channel eq
        channel_eq = self._my_channel_eq()
        preset_info = self._my_channel_eq_preset_info()
        update_values_for_device(channel_eq, preset_info,self)

    def update_display(self):
        # handle events asynchronously
        if self._value_update_timer == 0:
            self.refresh_state()
        if self._value_update_timer >= 0:
            self._value_update_timer -= 1
    
    def disconnect(self):
        # cleanup
        self._remove_listeners()

    # --- Listeners
    
    def _add_listeners(self):
        # add listeners for changes to Live elements
        track = self._track()
        track.add_mute_listener(self._on_mute_changed)
        if track.can_be_armed: # group track cannot!
            track.add_arm_listener(self._on_arm_changed)
        track.add_solo_listener(self._on_solo_cue_changed)

    def _remove_listeners(self):
        # remove all listeners added
        track = self._track()
        track.remove_mute_listener(self._on_mute_changed)
        if track.can_be_armed: # group track cannot!
            track.remove_arm_listener(self._on_arm_changed)
        track.remove_solo_listener(self._on_solo_cue_changed)
        
    def _on_mute_changed(self):
        track = self._track()
        if track.mute:
            value = 0
        else:
            value = 127
        self.send_midi_cc7(MIDI_TRACKS_CHANNEL, self._my_cc(MUTE_CC), value)

    def _on_arm_changed(self):
        track = self._track()
        if track.arm:
            value = 127
        else:
            value = 0
        self.send_midi_cc7(MIDI_TRACKS_CHANNEL, self._my_cc(ARM_CC), value)
    
    def _on_solo_cue_changed(self):
        # TODO not entirely clear whether this is what we want
        track = self._track()
        if track.solo:
            value = 127
        else:
            value = 0
        self.send_midi_cc7(MIDI_TRACKS_CHANNEL, self._my_cc(SOLO_CUE_CC), value)



    # --- Handlers ---
    
    def _init_cc_handlers(self):
        # define handlers for incpming midi events
        self._CC_HANDLERS = {
                (MIDI_TRACKS_CHANNEL, self._my_cc(MUTE_CC) ) : self._handle_mute_button
              , (MIDI_TRACKS_CHANNEL, self._my_cc(SOLO_CUE_CC) ) : self._handle_solo_cue_button
              , (MIDI_TRACKS_CHANNEL, self._my_cc(ARM_CC) ) : self._handle_arm_button            
        }

    def _handle_mute_button(self,value):
        self.debug(2,'Return track { self._idx } activation button action.')
        track = self._track()
        track.mute = (value < 64)

    def _handle_solo_cue_button(self,value):
        self.debug(2,'Return track { self._idx } solo/cue button action.')
        track = self._track()
        track.solo = (value > 63)

    def _handle_arm_button(self,value):
        self.debug(2,'Return track { self._idx } arm button action.')
        track = self._track()
        if track.can_be_armed: # group track cannot!
            track.arm = (value > 63)
        
    # --- MIDI ---
    
    def process_midi(self, midi_channel, cc_no, value):
        # receive incoming midi events and pass them to the correct handler
        self.debug(5,f'TrackControler: trying return { self._idx}.')
        if (midi_channel,cc_no) in self._CC_HANDLERS:
            handler = self._CC_HANDLERS[(midi_channel,cc_no)]
            if handler:
                self.debug(5,f'TrackController: handler found.')
                handler(value)
    
    def build_midi_map(self, script_handle, midi_map_handle):
        self.debug(2,f'Building MIDI map of track { self._idx }.')
        # Map CCs to be forwarded as defined in MIXER_CC_HANDLERS
        for (midi_channel,cc_no) in self._CC_HANDLERS:
            Live.MidiMap.forward_midi_cc(script_handle, midi_map_handle, midi_channel - 1, cc_no)
        # TODO/FIXME: not clear how this is honoured in the Live.MidiMaap.map_midi_cc call
        needs_takeover = True
        map_mode = Live.MidiMap.MapMode.absolute_14_bit
        track = self._track()
        self.debug(3,f'Mapping track { self._idx } pan to CC { self._my_cc(PAN_CC) } on MIDI channel { MIDI_TRACKS_CHANNEL }')
        Live.MidiMap.map_midi_cc(midi_map_handle, track.mixer_device.panning, MIDI_TRACKS_CHANNEL-1, self._my_cc(PAN_CC), map_mode, not needs_takeover)
        Live.MidiMap.map_midi_cc(midi_map_handle, track.mixer_device.volume, MIDI_TRACKS_CHANNEL-1, self._my_cc(VOLUME_CC), map_mode, not needs_takeover)
        sends = track.mixer_device.sends[:MAX_NO_OF_SENDS]
        cc_no = self._my_cc(SENDS_CC)
        for send in sends:
            self.debug(3,f'Mapping send to CC { cc_no } on MIDI channel { MIDI_SENDS_CHANNEL }')
            Live.MidiMap.map_midi_cc(midi_map_handle, send, MIDI_SENDS_CHANNEL-1, cc_no, map_mode, not needs_takeover)
            cc_no += NO_OF_TRACKS
        # build ChannelEq 
        build_midi_map_for_device(midi_map_handle, self._my_channel_eq(), self._my_channel_eq_preset_info(), self.debug)
   
        
   
