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

# Ableton Live imports
import Live

# Local imports
from .config import *
from .ElectraOneBase import ElectraOneBase
from .TransportController import TransportController
from .MasterController import MasterController
from .ReturnController import ReturnController
from .TrackController import TrackController

# CCs (see DOCUMENTATION.md)
PREV_TRACKS_CC = 68
NEXT_TRACKS_CC = 69

class MixerController(ElectraOneBase):
    """Electra One track, transport, returns and mixer control.
       Also initialises and manages the E1 mixer preset.
    """

    def __init__(self, c_instance):
        """Initialise a mixer controller.
           (Typically called only once, after loading a song.)
           - c_instance: Live interface object (see __init.py__)
        """
        ElectraOneBase.__init__(self, c_instance)
        # mixer preset is assumed to be uploaded by the user in advance
        # (with configuration constants set accordingly)
        #
        # initialise transport and master controller
        self._transport_controller = TransportController(c_instance)        
        self._master_controller = MasterController(c_instance)
        # initialise return track controllers
        self._return_controllers = []
        self._remap_return_tracks()
        # index of the first mapped track in the list of visible tracks
        self._first_track_index = 0
        # initialise track controllers
        self._track_controllers = []
        self._remap_tracks()
        # init MIDI handlers
        self._init_cc_handlers()
        self._add_listeners()
        self.debug(0,'MixerController loaded.')

    # --- helper functions ---

    def _validate_track_index(self,idx):
        """Check a proposal for a new first track index, adjusting it to
           never go too far left or right.
           - idx: proposal for new first track index; int
           - result: corrected new first track index; int
        """
        # index of first track should always be a multiple of NO_OF_TRACKS: moving
        # forward/backward then always shows the same block of tracks
        # in the mixer
        no_of_tracks = len(self.get_visible_torcs())
        idx = min(idx, NO_OF_TRACKS * (no_of_tracks // NO_OF_TRACKS))
        idx = max(idx, 0)            
        return idx

    def _slot_is_visible(self):
        """Returh whether the mixer preset slot is currently visible on the E1
        """
        visible = (CONTROL_MODE == CONTROL_BOTH) or \
            (ElectraOneBase.current_visible_slot == MIXER_PRESET_SLOT)
        self.debug(6,f'Mixer controller is visible: {visible}')
        return visible
    
    # --- interface ---

    def refresh_state(self):
        """Send the values of the controlled elements to the E1
           (to bring them in sync); hide controls for non existing
           (return)tracks.
           Forwarded to the transport, master, return and track controllers
           when mixer is visible.
           (Called whenever the mixer preset is selected or tracks
           added or deleted.)
        """
        if self._slot_is_visible():
            self.debug(2,'MixCont refreshing state.')
            self._set_controls_visibility()
            self.mixer_midi_burst_on()
            self._transport_controller.refresh_state()
            self._master_controller.refresh_state()
            # refresh tracks
            for track in self._track_controllers:
                track.refresh_state()
            # refresh return tracks
            for retrn in self._return_controllers:
                retrn.refresh_state()
            self.mixer_midi_burst_off()
            self.debug(2,'MixCont state refreshed.')
        else:
            self.debug(2,'MixCont not refreshing state (mixer not visible).')
            
    def update_display(self):
        """Update the dispay (called every 100ms).
           Forwarded to the transport, master, return and track controllers.
        """
        self.debug(6,'MixCont update display.')
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
        self._remove_listeners()
        self._transport_controller.disconnect()        
        self._master_controller.disconnect()
        for retrn in self._return_controllers:
            retrn.disconnect()    
        for track in self._track_controllers:
            track.disconnect()    

    def select(self):
        """Select the mixer preset on the E1. (Warning: assumes E1 is ready)
        """
        self.debug(2,'Select Mixer')
        self.activate_preset_slot(MIXER_PRESET_SLOT)
        
    # --- Listeners
                
    def _add_listeners(self):
        """Add listeners for changes in visible tracks, to copy changes to the
           controller.
        """
        self.song().add_visible_tracks_listener(self._on_tracks_added_or_deleted)
        # TODO: should also listen to visible_chains changes, but
        # this is not easy, because by defualt tracks do not have that listener
        # self.song().add_loop_listener(self._on_loop_changed)

    def _remove_listeners(self):
        """Remove all listeners added.
        """
        self.song().remove_visible_tracks_listener(self._on_tracks_added_or_deleted)

    # The rather convulated method used below to add a showing_chains_listener
    # is  necessary because this listener can only be added to a track that
    # can have chains. Initialy it may not, so every time a device is added
    # we have to see if now have to add a showing_chains_listener
    
    def _on_devices_changed(self):
        for track in self.song().visible_tracks:
            if (type(track) == Live.Track.Track) and track.can_show_chains:
                self.debug(5,f'Adding showing chains listener for track {track.name}')
                if not track.is_showing_chains_has_listener(self._on_tracks_added_or_deleted):
                    track.add_is_showing_chains_listener(self._on_tracks_added_or_deleted)
        
    def _add_chain_visibility_listeners(self):
        """Add listeners for changes in chain visibility, to copy changes to the
           controller.
        """
        for track in self.song().visible_tracks:
            if type(track) == Live.Track.Track:
                if not track.devices_has_listener(self._on_devices_changed):
                    track.add_devices_listener(self._on_devices_changed)
                
    def _remove_chain_visibility_listeners(self):
        """Remove all chain visibility listeners added.
        """
        for track in self.song().visible_tracks:
            if type(track) == Live.Track.Track:
                if track.devices_has_listener(self._on_devices_changed):
                    track.remove_devices_listener(self._on_devices_changed)
        
    def _remap_return_tracks(self):
        """Create new return track controllers for the current set of
           visible return tracks
           (unmap and destroy existing return track controllers)
        """
        for rtrn in self._return_controllers:
            rtrn.disconnect()
        return_count = min(MAX_NO_OF_SENDS, len(self.song().return_tracks))
        self._return_controllers = [ ReturnController(self.get_c_instance(), i)
                                     for i in range(return_count) ]
        
    def _remap_tracks(self):
        """Create new track controllers for the current set of visible tracks
           (unmap and destroy existing track controllers). Show a message
           to the user to tell which tracks are currently mapped.
        """
        # TODO: unfortunately, even if tracks are added/removed or
        # folded/expanded that would not altered the visibility of the tracks
        # currently shown in the mixer, the mixer is updated and may show
        # a different view because self._first_track_index points to another track
        self._remove_chain_visibility_listeners()
        for tc in self._track_controllers:
            tc.disconnect()
        visible_torcs = self.get_visible_torcs()            
        last_track_index = min(self._first_track_index + NO_OF_TRACKS, len(visible_torcs))
        track_range = range(self._first_track_index, last_track_index)
        self._track_controllers = [ TrackController(self.get_c_instance(), visible_torcs[i], i-self._first_track_index)
                                    for i in track_range ]
        self._add_chain_visibility_listeners()
        self.show_message(f'E1 managing tracks { self._first_track_index+1 } - { last_track_index }.')
        
    def _handle_selected_tracks_change(self):
        """Call this whenever the current set of selected tracks changes.
            Updates MIDI mapping, listeners and the displayed values.
        """
        self._remap_tracks()
        # no need to remap return tracks as the selection of those never changes
        # make the right controls and group labels visible if mixer currently visible
        self.debug(2,'MixCont requesting MIDI map to be rebuilt.')
        self.request_rebuild_midi_map() # also refreshes state ; is ignored when the effect controller also requests it during initialisation (which is exactly what we want)

    def _set_controls_visibility(self):
        """Set visibility of eq devices, tracks, sends and returns on the E1.
        """
        if self._slot_is_visible():
            # set visibility of the (return) tracks and sends
            self.set_mixer_visibility(len(self._track_controllers),len(self._return_controllers))
            # set visibility of the channel-eq devices
            for t in self._track_controllers:
                self.set_channel_eq_visibility_on_track(t._offset, t._eq_device_controller != None)
            #if self._master_controller._eq_device_controller:
            #    self.set_channel_eq_visibility_on_track(NO_OF_TRACKS,True)
            #else:
            #    self.set_channel_eq_visibility_on_track(NO_OF_TRACKS,False)
            self.set_channel_eq_visibility_on_track(NO_OF_TRACKS, self._master_controller._eq_device_controller != None)
            # set visibility of the arm button (hidden for group tracks and chains)
            for t in self._track_controllers:
                self.set_arm_visibility_on_track(t._offset, t._base_arm_cc != None)
                
    def _on_tracks_added_or_deleted(self):
        """ Call this whenever tracks are added or deleted (this includes
            the Return tracks). Updates MIDI mapping, listeners and the
            displayed values.
        """
        self.debug(2,'Tracks added or deleted.')
        # reconnect the return tracks (a return track may hev been added or deleted)
        self._remap_return_tracks()
        # make sure the first track index is still pointing to existing tracks
        self._first_track_index = self._validate_track_index(self._first_track_index)
        self._remap_tracks()
        self.debug(2,'MixCont requesting MIDI map to be rebuilt.')
        self.request_rebuild_midi_map() # also refreshes state ; is ignored when the effect controller also requests it during initialisation (which is exactly what we want)
        
    # --- Handlers ---
        
    def _init_cc_handlers(self):
        """Define handlers for incoming MIDI CC messages.
           (previous and next track selection for the  mixer.)
        """
        self._CC_HANDLERS = {
               (MIDI_MASTER_CHANNEL, PREV_TRACKS_CC) : self._handle_prev_tracks
            ,  (MIDI_MASTER_CHANNEL, NEXT_TRACKS_CC) : self._handle_next_tracks
            }
        
    def _handle_prev_tracks(self,value):
        """Shift left NO_OF_TRACKS; don't move before first track.
        """
        if value > 63:
            self.debug(3,'Prev tracks pressed.')
            # shift left, but not before first track
            self._first_track_index = self._validate_track_index(self._first_track_index - NO_OF_TRACKS)
            self._handle_selected_tracks_change()
            
    def _handle_next_tracks(self,value):
        """Shift right NO_OF_TRACKS; don't move beyond last track.
        """
        if value > 63:
            self.debug(3,'Next tracks pressed.')
            # shift right, but not beyond last track
            self._first_track_index = self._validate_track_index(self._first_track_index + NO_OF_TRACKS)
            self._handle_selected_tracks_change()

    # --- MIDI mapping ---
        
    def process_midi(self, midi_channel, cc_no, value):
        """Receive incoming MIDI CC messages, and distribute them to the
           transport, master, return and track controllers.
           - midi_channel: MIDI channel of incomming message; int (1..16)
           - cc_no: MIDI CC number; int (0..127)
           - value: incoming CC value; int (0..127)
        """
        self.debug(4,f'Handling ({midi_channel},{cc_no}) with value {value}.')
        if (midi_channel,cc_no) in self._CC_HANDLERS:
            self.debug(5,f'MixerController: handler found for CC {cc_no} on MIDI channel {midi_channel}.')
            handler = self._CC_HANDLERS[(midi_channel,cc_no)]
            handler(value)
            return
        if self._transport_controller.process_midi(midi_channel,cc_no,value):
            return
        if self._master_controller.process_midi(midi_channel,cc_no,value):
            return
        for track in self._track_controllers:
            if track.process_midi(midi_channel,cc_no,value):
                return
        for retrn in self._return_controllers:
            if retrn.process_midi(midi_channel,cc_no,value):
                return

    def build_midi_map(self, script_handle, midi_map_handle):
        """Build a MIDI map for the full mixer, and refresh its state.
           - script_handle: reference to the main remote script class
               (whose receive_midi method will be called for any MIDI CC messages
               marked to be forwarded here)
           - midi_map_hanlde: MIDI map handle as passed to Ableton Live, to
               which MIDI mappings must be added.
        """
        self.debug(2,'MixCont building mixer MIDI map.')
        # Map CCs to be forwarded as defined in _CC_HANDLERS
        for (midi_channel,cc_no) in self._CC_HANDLERS:
            Live.MidiMap.forward_midi_cc(script_handle, midi_map_handle, midi_channel - 1, cc_no)
        self._transport_controller.build_midi_map(script_handle,midi_map_handle)
        self._master_controller.build_midi_map(script_handle,midi_map_handle)
        for retrn in self._return_controllers:
            retrn.build_midi_map(script_handle,midi_map_handle)
        for track in self._track_controllers:
            track.build_midi_map(script_handle,midi_map_handle)
        self.debug(2,'MixCont mixer MIDI map built.')
        self.refresh_state()


