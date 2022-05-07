# MixerController
# - control transport, tracks, returns and master 
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
# This part is considerably messier than EffectController, as Ableton
# unfortunately does not consider all potentially MIDI mappable controls as
# 'parameters' that can be passed to Live.MidiMap.map_midi_cc (after which all
# handling of control updates on the E1 or changes to controls in  Live itself
# (through the GUI or the another remote controller) are synced automatically :-( 
#
# This assumes a mixer preset with controls assigned to channel
# MIDI_MASTER_CHANNEL and MIDI_TRACKS_CHANNEL with the following assignment
# of CC parameters (where it is assumed each channel runs a Channel-EQ device).
# All faders are CC14 MSB first mapped to the specified cc-no (and cc-no+32)
#
# Track x+1 (for x in [0..4]) all assigned to MIDI_TRACKS_CHANNEL
#
# - 0 + x (32 + x) Pan
# - 5 + x (37 + x) Volume
# - 79 + x Active (On/Off)
# - 84 + x Solo/cue (On/Off)
# - 89 + x Arm (On/Off)
#
# - 10 + x (42 + x) High
# - 15 + x (47 + x) Mid Freq
# - 20 + x (52 + x) Mid
# - 25 + x (57 + x) Low
# - 111 + x Rumble (On/Off)
# - 64 + x (96 + x) Output
#
#
# The sends for rack x+1 (for x in [0..4]) all assigned to MIDI_SENDS_CHANNEL
#
# - 0 + x (32 + x) Send A
# - 5 + x (37 + x) Send B
# - 10 + x (42 + x) Send C
# - 15 + x (47 + x) Send D
# - 20 + x (52 + x) Send E
# - 25 + x (57 + x) Send F

#
# Transport all assigned to MIDI_MASTER_CHANNEL
#
# - 15 prev tracks (Trigger)
# - 47 next tracks (Trigger)
# - 16 play/stop (On/Off)
# - 48 record (On/Off)
# - 17 rewind (trigger)
# - 49 forward (Trigger)

PREV_TRACKS_CC = 68
NEXT_TRACKS_CC = 69

# Master all assigned to MIDI_MASTER_CHANNEL
#
# - 0 (32) Pan
# - 1 (33) Volume
# - 2 (34) Cue volume
# - 9 Solo (On/Off)
#
# - 3 (35) High
# - 4 (36) Mid Freq
# - 5 (37) Mid
# - 6 (38) Low
# - 7 (39) Output
# - 8 Rumble (On/Off)
#
# - 64-79 (96-101) SEND A-E Pan
# - 70-75 (102-107) SEND A-E Volume
# - 76-81 (108-113) SEND A_E Mute
#

# TODO
# ? should we deal with selected track changes


# Ableton Live imports
import Live

# Local imports
from .config import *
from .ElectraOneBase import ElectraOneBase
from .TransportController import TransportController
from .MasterController import MasterController
from .ReturnController import ReturnController
from .TrackController import TrackController


# TODO: somehow, when loading a new song, the display is automatically updated
# check what happens to understand why!!

class MixerController(ElectraOneBase):
    """Electra One track, transport, returns and mixer control.
       Also initialises and manages the E1 mixer preset.
    """

    def __init__(self, c_instance):
        ElectraOneBase.__init__(self, c_instance)
        self._refresh_state_timer = -1 # prevent refresh at the moment
        # TODO: Upload mixer preset if defined
        #if MIXER_PRESET:
        #    self.debug(1,'Uploading mixer preset.')
        #    self.upload_preset(MIXER_PRESET_SLOT,MIXER_PRESET)
        self._transport_controller = TransportController(c_instance)        
        self._master_controller = MasterController(c_instance)
        # allocate return track controllers (at most two, but take existence into account)
        returns = min(MAX_NO_OF_SENDS,len(self.song().return_tracks))
        self._return_controllers = [ReturnController(c_instance,i) for i in range(returns)]
        # TODO: upload mixer preset to E1 to Ableton bank (if not already present)
        # index of the first mapped track in the list of visible tracks
        self._first_track_index = 0
        self._track_controllers = []  # filled by self._handle_selection_change()
        # init MIDI handlers
        self._init_handlers()
        self._add_global_listeners()
        # force an update
        self._handle_selection_change()
        self.debug(0,'MixerController loaded.')

    # --- helper functions ---

    def _validate_track_index(self,idx):
        # Adjust the newly selected track to never go too far left or right.
        idx = min(idx, len(self.song().visible_tracks) - NO_OF_TRACKS)
        idx = max(idx, 0)            
        return idx
    
    def refresh_state(self):
        self.debug(2,'MixCont refreshing state.')
        self._transport_controller.refresh_state()
        self._master_controller.refresh_state()
        for retrn in self._return_controllers:
            retrn.refresh_state()    
        for track in self._track_controllers:
            track.refresh_state()    
    
    def update_display(self):
        """Update the dispay (called every 100ms).
           Forwarded to the transport, master, return and track controllers.
           Used to effectuate a state refresh (after some delay) called for
           by _handle_selection_change
        """
        self.debug(4,'MixCont update display.')
        # handle a refresh state after some delay
        if self._refresh_state_timer == 0:
            self.refresh_state()
        if self._refresh_state_timer >= 0:
            self._refresh_state_timer -= 1
        # forward update request to children
        self._transport_controller.update_display()
        self._master_controller.update_display()
        for retrn in self._return_controllers:
            retrn.update_display()    
        for track in self._track_controllers:
            track.update_display()    
        
    def disconnect(self):
        """Called right before we get disconnected from Live; cleanup
           Forwarded to the transport, master, return and track controllers.
        """
        self._remove_global_listeners()
        self._transport_controller.disconnect()        
        self._master_controller.disconnect()
        for retrn in self._return_controllers:
            retrn.disconnect()    
        for track in self._track_controllers:
            track.disconnect()    

    # --- Listeners
                
    def _add_global_listeners(self):
        self.song().add_visible_tracks_listener(self._on_tracks_added_or_deleted)
        # self.song().add_loop_listener(self.__on_loop_changed)
        # TODO : add listening to track name changes

    def _remove_global_listeners(self):
        self.song().remove_visible_tracks_listener(self._on_tracks_added_or_deleted)

    def _handle_selection_change(self):
        """Call this whenever the current set of selected tracks changes
           (e.g. when adding or deleting tracks, or when shifting the focus
           left or right.
        """
        for tc in self._track_controllers:
            tc.disconnect()
        last_track_index = min(self._first_track_index + NO_OF_TRACKS, len(self.song().visible_tracks))
        track_range = range(self._first_track_index, last_track_index)
        self._track_controllers = [ TrackController(self.get_c_instance(),i,i-self._first_track_index)
                                    for i in track_range ]
        self.show_message(f'E1 managing tracks { self._first_track_index+1 } - { self._first_track_index + NO_OF_TRACKS }.')
        self.debug(2,'MixCont requesting MIDI map to be rebuilt.')
        self.request_rebuild_midi_map()
        self._refresh_state_timer = 2 # delay value updates until MIDI map ready

    def _on_tracks_added_or_deleted(self):
        """ Call this whenever tracks are added or deleted; this includes
            the Return tracks.
        """
        self.debug(2,'Tracks added or deleted.')
        # make sure the first track index is still pointing to existing tracks
        self._first_track_index = self._validate_track_index(self._first_track_index)
        # reconnect the return tracks
        for rtrn in self._return_controllers:
            rtrn.disconnect()
        returns = min(MAX_NO_OF_SENDS,len(self.song().return_tracks))
        self._return_controllers = [ReturnController(self.get_c_instance(),i) for i in range(returns)]
        # reconnect the tracks, this also requests value update (incl. the return tracks)
        self._handle_selection_change() 

    # --- Handlers ---
        
    def _init_handlers(self):
        self._CC_HANDLERS = {
               (MIDI_MASTER_CHANNEL, PREV_TRACKS_CC) : self._do_prev_tracks
            ,  (MIDI_MASTER_CHANNEL, NEXT_TRACKS_CC) : self._do_next_tracks
            }
        
    def _do_prev_tracks(self,value):
        """Shift left NO_OF_TRACKS; don't move before first track.
        """
        if value == 127:
            self.debug(3,'Prev tracks pressed.')
            self._first_track_index = self._validate_track_index(self._first_track_index - NO_OF_TRACKS)
            self._handle_selection_change()
            
    def _do_next_tracks(self,value):
        """Shift right NO_OF_TRACKS; don't move beyond last track.
        """
        if value == 127:
            self.debug(3,'Next tracks pressed.')
            self._first_track_index = self._validate_track_index(self._first_track_index + NO_OF_TRACKS)
            self._handle_selection_change()

    # --- MIDI mapping ---
        
    def process_midi(self, midi_channel, cc_no, value):
        """Receive incoming MIDI CC messages, and distribute them to the
           transport, master, return and track controllers.
        """
        self.debug(4,f'Handling ({midi_channel},{cc_no}) with value {value}.')
        if (midi_channel,cc_no) in self._CC_HANDLERS:
            handler = self._CC_HANDLERS[(midi_channel,cc_no)]
            if handler:
                self.debug(4,f'Handler found.')
                handler(value)
        self._transport_controller.process_midi(midi_channel,cc_no,value)                    
        self._master_controller.process_midi(midi_channel,cc_no,value)    
        for retrn in self._return_controllers:
            retrn.process_midi(midi_channel,cc_no,value)    
        for track in self._track_controllers:
            track.process_midi(midi_channel,cc_no,value)    

    def build_midi_map(self, script_handle, midi_map_handle):
        """Build a MIDI map for the full mixer.
        """
        self.debug(1,'MixCont building mixer MIDI map.')
        # Map CCs to be forwarded as defined in _CC_HANDLERS
        for (midi_channel,cc_no) in self._CC_HANDLERS:
            Live.MidiMap.forward_midi_cc(script_handle, midi_map_handle, midi_channel - 1, cc_no)
        self._transport_controller.build_midi_map(script_handle,midi_map_handle)
        self._master_controller.build_midi_map(script_handle,midi_map_handle)
        for retrn in self._return_controllers:
            retrn.build_midi_map(script_handle,midi_map_handle)
        for track in self._track_controllers:
            track.build_midi_map(script_handle,midi_map_handle)
        
                

