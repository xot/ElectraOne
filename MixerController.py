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
# MIDI_MIXER_CHANNEL and MIDI_MIXER_CHANNEL+1 with the following assignment
# of CC parameters (where it is assumed each channel runs a Channel-EQ device).
# All faders are CC14 MSB first mapped to the specified cc-no (and cc-no+32)
#
# Track x+1 (for x in [0..4]) all assigned to MIDI_MIXER_CHANNEL+1
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
# - 69 + x (101 + x) Send A
# - 74 + x (106 + x) Send B
#
# Transport all assigned to MIDI_MIXER_CHANNEL
#
# - 15 prev tracks (Trigger)
# - 47 next tracks (Trigger)
# - 16 play/stop (On/Off)
# - 48 record (On/Off)
# - 17 rewind (trigger)
# - 49 forward (Trigger)

PREV_TRACKS_CC = 15
NEXT_TRACKS_CC = 47

# Master all assigned to MIDI_MIXER_CHANNEL
#
# - 0 (32) Pan
# - 1 (33) Volume
# - 2 (34) Cue volume
# - 14 Solo (On/Off)
#
# - 3 (35) High
# - 4 (36) Mid Freq
# - 5 (37) Mid
# - 6 (38) Low
# - 36 Rumble (On/Off)
# - 7 (39) Output
#
# - 8 (40) SEND A Pan
# - 9 (41) SEND A Volume
# - 10 SEND A Active (On/Off)
#
# - 11 (43) SEND B Pan
# - 12 (44) SEND B Volume
# - 13 SEND B Active (On/Off)

# TODO
# - monitor track insertions, deletions
# ? monitor selected track changes


# Ableton Live imports
from _Framework.ControlSurface import ControlSurface
import Live

# Local imports
from .config import *
from .ElectraOneBase import ElectraOneBase
from .TransportController import *
from .MasterController import *
from .ReturnController import *
from .TrackController import *



# TODO: somehow, when loading a new song, the display is automatically updated
# check what happens to understand why!!


class MixerController(ElectraOneBase):
    """Electra One track, transport, returns and mixer control.
       Also initialises and manages the E1 mixer preset.
    """

    def __init__(self, c_instance):
        ElectraOneBase.__init__(self, c_instance)
        self.__c_instance = c_instance
        self._transport_controller = TransportController(c_instance)        
        self._master_controller = MasterController(c_instance)
        # allocate return track controllers (at most two, but take existence into account)
        returns = min(2,len(self.song().return_tracks))
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
        idx = min(idx, len(self.song().visible_tracks) - NO_OF_TRACKS)
        idx = max(idx, 0)            
        self.show_message(f'Mixer managing tracks { idx+1 } - { idx + NO_OF_TRACKS }.')
        return idx
        
    def update_display(self):
        self._transport_controller.update_display()
        self._master_controller.update_display()
        for retrn in self._return_controllers:
            retrn.update_display()    
        for track in self._track_controllers:
            track.update_display()    
        
    def disconnect(self):
        """Called right before we get disconnected from Live; cleanup
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
        # TODO: upload track info (eg track names
        # TODO: upload values
        for tc in self._track_controllers:
            tc.disconnect()
        last_track_index = min(self._first_track_index + NO_OF_TRACKS, len(self.song().visible_tracks))
        track_range = range(self._first_track_index, last_track_index)
        self._track_controllers = [ TrackController(self.__c_instance,i,i-self._first_track_index)
                                    for i in track_range ]
        self.request_rebuild_midi_map()

    def _on_tracks_added_or_deleted(self):
        self.debug(2,'Tracks added or deleted.')
        self._first_track_index = self._validate_track_index(self._first_track_index)
        self._handle_selection_change()
        # TODO: deal with return track changes

    # --- initialise values ---
    
    # --- Handlers ---
        
    def _init_handlers(self):
        # Handle E1 controler buttons that need special treatment 
        # Keys are tuples of MIDI channels (range [1-16]) and CC_NO's,
        # their value is a handler h, called with the received value V
        # when the MIDI event specified by the key happens.
        # see build_midi_map and receive_midi
        self._CC_HANDLERS = {
               (MIDI_MIXER_CHANNEL, PREV_TRACKS_CC) : self._do_prev_tracks
            ,  (MIDI_MIXER_CHANNEL, NEXT_TRACKS_CC) : self._do_next_tracks
            }
        
    def _do_prev_tracks(self,value):
        """Shift left NO_OF_TRACKS; don't move before first track.
        """
        if value == 127:
            self.debug(2,'Prev tracks pressed.')
            self._first_track_index = self._validate_track_index(self._first_track_index - NO_OF_TRACKS)
            self._handle_selection_change()
            
    def _do_next_tracks(self,value):
        """Shift right NO_OF_TRACKS; don't move beyond last track.
        """
        if value == 127:
            self.debug(2,'Next tracks pressed.')
            self._first_track_index = self._validate_track_index(self._first_track_index + NO_OF_TRACKS)
            self._handle_selection_change()

    # --- MIDI mapping ---
        
    def receive_midi(self, midi_bytes):
        self.debug(4,f'Receiving MIDI { midi_bytes }')
        # only handle 7bit CC events that are three bytes long
        if len(midi_bytes) != 3:
            return
        (status,cc_no,value) = midi_bytes
        midi_channel = status - 176 + 1
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
        self.debug(1,'Building mixer MIDI map.')
        # Map CCs to be forwarded as defined in _CC_HANDLERS
        for (midi_channel,cc_no) in self._CC_HANDLERS:
            Live.MidiMap.forward_midi_cc(script_handle, midi_map_handle, midi_channel - 1, cc_no)
        self._transport_controller.build_midi_map(script_handle,midi_map_handle)
        self._master_controller.build_midi_map(script_handle,midi_map_handle)
        for retrn in self._return_controllers:
            retrn.build_midi_map(script_handle,midi_map_handle)
        for track in self._track_controllers:
            track.build_midi_map(script_handle,midi_map_handle)
        
                

