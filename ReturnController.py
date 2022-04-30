# ReturnController
# - control one return track
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

# CCs (see MixerController.py)
# These are base values, to which RETURNS_FACTOR is added for each next return track
RETURNS_PAN_CC = 8
RETURNS_VOLUME_CC = 9
RETURNS_MUTE_CC = 10
#
RETURNS_FACTOR = 3

class ReturnController(ElectraOneBase):
    """Manage a return track.
    """
 
    def __init__(self, c_instance, idx):
        """Initialise a return controller for return idx (starting at 0). 
        """
        ElectraOneBase.__init__(self, c_instance)
        self._idx = idx
        self._add_listeners()
        self._init_cc_handlers()
        self._value_update_timer = 5 # delay value updates until MIDI map ready
        self.debug(0,'ReturnController loaded.')

    # --- helper functions ---
    
    def _track(self):
        # retrun a reference to the track managed
        return self.song().return_tracks[self._idx]

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
        retrn = self._track()
        retrn.add_mute_listener(self._on_mute_changed)

    def _remove_listeners(self):
        # remove all listeners added
        retrn = self._track()
        retrn.remove_mute_listener(self._on_mute_changed)

    def _on_mute_changed(self):
        retrn = self._track()
        if retrn.mute:
            value = 0
        else:
            value = 127
        self.send_midi_cc7(MIDI_MASTER_CHANNEL, self._my_cc(RETURNS_MUTE_CC), value)

    # --- initialise values ---
    
    def _init_controller_values(self):
        # send the values of the controlled elements to the E1 (to bring them in sync)
        self._on_mute_changed()
        retrn = self._track()
        self.send_parameter_as_cc14(retrn.mixer_device.panning, MIDI_MASTER_CHANNEL, self._my_cc(RETURNS_PAN_CC))
        self.send_parameter_as_cc14(retrn.mixer_device.volume, MIDI_MASTER_CHANNEL, self._my_cc(RETURNS_VOLUME_CC))

    # --- Handlers ---
    
    def _my_cc(self,base_cc):
        # derive the actual cc_no from the assigned base CC and my index
        return base_cc + RETURNS_FACTOR * self._idx
    
    def _init_cc_handlers(self):
        # define handlers for incpming midi events
        self._CC_HANDLERS = {
                (MIDI_MASTER_CHANNEL, self._my_cc(RETURNS_MUTE_CC) ) : self._handle_mute_button
            }

    def _handle_mute_button(self,value):
        self.debug(2,'Return track { self._idx } activation button action.')
        retrn = self._track()
        retrn.mute = (value < 64)

    # --- MIDI ---
    
    def process_midi(self, midi_channel, cc_no, value):
        # receive incoming midi events and pass them to the correct handler
        self.debug(5,f'ReturnControler: trying return { self._idx}.')
        if (midi_channel,cc_no) in self._CC_HANDLERS:
            handler = self._CC_HANDLERS[(midi_channel,cc_no)]
            if handler:
                self.debug(5,f'ReturnController: handler found.')
                handler(value)
    
    def build_midi_map(self, script_handle, midi_map_handle):
        self.debug(2,f'Building MIDI map of return track { self._idx }.')
        # Map CCs to be forwarded as defined in MIXER_CC_HANDLERS
        for (midi_channel,cc_no) in self._CC_HANDLERS:
            Live.MidiMap.forward_midi_cc(script_handle, midi_map_handle, midi_channel - 1, cc_no)
        # TODO/FIXME: not clear how this is honoured in the Live.MidiMaap.map_midi_cc call
        needs_takeover = True
        map_mode = Live.MidiMap.MapMode.absolute_14_bit
        retrn = self._track()
        self.debug(3,f'Mapping send { self._idx } pan to CC { self._my_cc(RETURNS_PAN_CC) } on MIDI channel { MIDI_MASTER_CHANNEL }')
        Live.MidiMap.map_midi_cc(midi_map_handle, retrn.mixer_device.panning, MIDI_MASTER_CHANNEL-1, self._my_cc(RETURNS_PAN_CC), map_mode, not needs_takeover)
        Live.MidiMap.map_midi_cc(midi_map_handle, retrn.mixer_device.volume, MIDI_MASTER_CHANNEL-1, self._my_cc(RETURNS_VOLUME_CC), map_mode, not needs_takeover)
    

   
