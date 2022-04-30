# TransportController
# - control transport
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
PLAY_STOP_CC = 60
RECORD_CC = 61
REWIND_CC = 62
FORWARD_CC = 63


class TransportController(ElectraOneBase):
    """Manage the transport.
    """
    
    def __init__(self, c_instance):
        ElectraOneBase.__init__(self, c_instance)
        # keep track of rewind/forward button states (to move while
        # button pressed, see update_display)
        self._rewind_pressed = False
        self._forward_pressed = False
        self._add_listeners()
        self._init_cc_handlers()
        self._value_update_timer = 5 # delay value updates until MIDI map ready
        self.debug(0,'TransportController loaded.')

    # --- helper functions ---
    
    def update_display(self):
        # handle events asynchronously
        if self._value_update_timer == 0:
            self._init_controller_values()
        if self._value_update_timer >= 0:
            self._value_update_timer -= 1
        # Move backword or forward in a sing while rewind or forward button pressed
        if self._rewind_pressed:
            self.song().jump_by(-FORW_REW_JUMP_BY_AMOUNT)
        if self._forward_pressed:
            self.song().jump_by(FORW_REW_JUMP_BY_AMOUNT)
    
    def disconnect(self):
        # cleanup
        self._remove_listeners()

    # --- Listeners
            
    def _add_listeners(self):
        # add listeners for changes to Live elements
        self.song().add_record_mode_listener(self._on_record_mode_changed)
        self.song().add_is_playing_listener(self._on_is_playing_changed)


    def _remove_listeners(self):
        # remove all listeners added
        self.song().remove_record_mode_listener(self._on_record_mode_changed)
        self.song().remove_is_playing_listener(self._on_is_playing_changed)

    def _on_record_mode_changed(self):
        self.debug(2,'Record mode changed.')
        # TODO: send value update
        if self.song().record_mode:
            value = 127
        else:
            value = 0
        self.send_midi_cc7(MIDI_MASTER_CHANNEL, RECORD_CC, value)
    
    def _on_is_playing_changed(self):
        self.debug(2,'Stop/play change.')
        if self.song().is_playing:
            value = 127
        else:
            value = 0
        self.send_midi_cc7(MIDI_MASTER_CHANNEL, PLAY_STOP_CC, value)

    # --- initialise values ---
    
    def _init_controller_values(self):
        # send the values of the controlled elements to the E1 (to bring them in sync)
        self._on_record_mode_changed()
        self._on_is_playing_changed()
        
    # --- Handlers ---
    
    def _init_cc_handlers(self):
        # define handlers for incpming midi events
        self._CC_HANDLERS = {
               (MIDI_MASTER_CHANNEL, REWIND_CC) : self._do_rewind
            ,  (MIDI_MASTER_CHANNEL, FORWARD_CC) : self._do_forward
            ,  (MIDI_MASTER_CHANNEL, PLAY_STOP_CC) : self._do_play_stop
            ,  (MIDI_MASTER_CHANNEL, RECORD_CC) : self._do_record
            }
        pass

    def _do_rewind(self,value):        
        self.debug(2,'Rewind button action.')
        self._rewind_pressed = (value > 63)

    def _do_forward(self,value):        
        self.debug(2,'Forward button action.')
        self._forward_pressed = (value > 63)

    def _do_play_stop(self,value):        
        self.debug(2,'Play/stop button action.')
        if (value > 63):
            self.song().start_playing()
        else:
            self.song().stop_playing()

    def _do_record(self,value):        
        self.debug(2,'Record button action.')
        self.song().record_mode = (value > 63)

    # --- MIDI ---
    
    def process_midi(self, midi_channel, cc_no, value):
        # receive incoming midi events and pass them to the correct handler
        self.debug(5,f'Trying TransportControler.')
        if (midi_channel,cc_no) in self._CC_HANDLERS:
            handler = self._CC_HANDLERS[(midi_channel,cc_no)]
            if handler:
                self.debug(5,f'TransportController: handler found.')
                handler(value)

    
    def build_midi_map(self, script_handle, midi_map_handle):
        self.debug(2,'Building transport MIDI map.')
        # Map CCs to be forwarded as defined in MIXER_CC_HANDLERS
        for (midi_channel,cc_no) in self._CC_HANDLERS:
            Live.MidiMap.forward_midi_cc(script_handle, midi_map_handle, midi_channel - 1, cc_no)

   
