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
from .ElectraOneBase import ElectraOneBase

# CCs (see MixerController.py)
# These are base values, to which TRACKS_FACTOR is added for each next return track
PAN_CC = 0
VOLUME_CC = 5
MUTE_CC = 79
SOLO_CUE_CC = 84
ARM_CC = 89
#
TRACKS_FACTOR = 1

SENDS_CC = 69  # code below assumes all sends are mapped after each other, ie with increments of NO_OF_TRACKS=5

# TODO: Map equaliser controls
# TODO: Handle tracks that cannot be armed
# TODO: Handle track names

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
        self.debug(0,'ReturnController loaded.')

    # --- helper functions ---
    
    def _track(self):
        # retrun a reference to the track managed
        return self.song().visible_tracks[self._idx]

    def _my_cc(self,base_cc):
        # derive the actual cc_no from the assigned base CC and my index
        return base_cc + TRACKS_FACTOR * self._offset
    
    def update_display(self):
        # handle events asynchronously
        if self._value_update_timer == 0:
            self._init_controller_values()
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
        track.add_arm_listener(self._on_arm_changed)
        track.add_solo_listener(self._on_solo_cue_changed)

    def _remove_listeners(self):
        # remove all listeners added
        track = self._track()
        track.remove_mute_listener(self._on_mute_changed)
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


    # --- initialise values ---
    
    def _init_controller_values(self):
        # send the values of the controlled elements to the E1 (to bring them in sync)
        self._on_mute_changed()
        self._on_arm_changed()         
        self._on_solo_cue_changed()
        track = self._track()
        self.send_parameter_as_cc14(track.mixer_device.panning, MIDI_TRACKS_CHANNEL, self._my_cc(PAN_CC))
        self.send_parameter_as_cc14(track.mixer_device.volume, MIDI_TRACKS_CHANNEL, self._my_cc(VOLUME_CC))
        # TODO: remove assumption/restriction of 2 sends
        sends = track.mixer_device.sends[:2]
        cc_no = self._my_cc(SENDS_CC)
        for send in sends:
            self.send_parameter_as_cc14(send,MIDI_TRACKS_CHANNEL,cc_no)
            cc_no += NO_OF_TRACKS
                
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
        # TODO: remove assumption/restriction of 2 sends
        sends = track.mixer_device.sends[:2]
        cc_no = self._my_cc(SENDS_CC)
        for send in sends:
            self.debug(3,f'Mapping send to CC { cc_no } on MIDI channel { MIDI_TRACKS_CHANNEL }')
            Live.MidiMap.map_midi_cc(midi_map_handle, send, MIDI_TRACKS_CHANNEL-1, cc_no, map_mode, not needs_takeover)
            cc_no += NO_OF_TRACKS
    

   
        
   
