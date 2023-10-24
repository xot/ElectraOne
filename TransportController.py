# TransportController
# - control transport (play/stop, record, rewind, forward)
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

# CCs (see DOCUMENTATION.md)
PLAY_STOP_CC = 64
RECORD_CC = 65
REWIND_CC = 66
FORWARD_CC = 67


class TransportController(ElectraOneBase):
    """Manage the transport (play/stop, record, rewind, forward).
    """
    
    def __init__(self, c_instance):
        """Initialise.
           - c_instance: Live interface object (see __init.py__)
        """
        ElectraOneBase.__init__(self, c_instance)
        # keep track of rewind/forward button states (to move while
        # button pressed, see update_display)
        self._rewind_pressed = False
        self._forward_pressed = False
        self._add_listeners()
        self._init_cc_handlers()
        self.debug(0,'TransportController loaded.')

    # --- helper functions ---
    
    # --- initialise values ---
    
    def refresh_state(self):
        """Send the states of the play/stop and record buttons to the E1
           (to bring them in sync)
        """
        self.debug(2,'Refreshing transport state.')
        self._on_record_mode_changed()
        self._on_is_playing_changed()

    def update_display(self):
        """ Called every 100 ms. Used to monitor rewind/forward buttons 
            (move backward or forward in a song while rewind or forward
             button pressed)
        """
        # 
        if self._rewind_pressed:
            self.song().jump_by(-FORW_REW_JUMP_BY_AMOUNT)
        if self._forward_pressed:
            self.song().jump_by(FORW_REW_JUMP_BY_AMOUNT)
    
    def disconnect(self):
        """Called right before we get disconnected from Live.
           Cleans up.
        """
        # cleanup
        self._remove_listeners()

    # --- Listeners
            
    def _add_listeners(self):
        """Add listeners for play/stop and record button in Live.
        """
        self.song().add_record_mode_listener(self._on_record_mode_changed)
        self.song().add_is_playing_listener(self._on_is_playing_changed)


    def _remove_listeners(self):
        """Remove all listeners added
        """
        self.song().remove_record_mode_listener(self._on_record_mode_changed)
        self.song().remove_is_playing_listener(self._on_is_playing_changed)

    def _on_record_mode_changed(self):
        """Update the value shown for the record control on the E1.
        """
        self.debug(3,'Record mode changed.')
        if self.song().record_mode:
            value = 127
        else:
            value = 0
        self.send_midi_cc7(MIDI_MASTER_CHANNEL, RECORD_CC, value)
    
    def _on_is_playing_changed(self):
        """Update the value shown for the play/stop control on the E1.
        """
        self.debug(3,'Stop/play changed.')
        if self.song().is_playing:
            value = 127
        else:
            value = 0
        self.send_midi_cc7(MIDI_MASTER_CHANNEL, PLAY_STOP_CC, value)
        
    # --- Handlers ---
    
    def _init_cc_handlers(self):
        """Define handlers for incoming MIDI CC messages.
        """
        self._CC_HANDLERS = {
               (MIDI_MASTER_CHANNEL, REWIND_CC)    : self._handle_rewind
            ,  (MIDI_MASTER_CHANNEL, FORWARD_CC)   : self._handle_forward
            ,  (MIDI_MASTER_CHANNEL, PLAY_STOP_CC) : self._handle_play_stop
            ,  (MIDI_MASTER_CHANNEL, RECORD_CC)    : self._handle_record
            }

    def _handle_rewind(self,value):
        """Handle rewind button press.
           - value: incoming MIDI CC value; int
        """
        self.debug(3,'Rewind button action.')
        self._rewind_pressed = (value > 63)

    def _handle_forward(self,value):        
        """Handle forward button press.
           - value: incoming MIDI CC value; int
        """
        self.debug(3,'Forward button action.')
        self._forward_pressed = (value > 63)

    def _handle_play_stop(self,value):        
        """Handle play/stop button press.
           - value: incoming MIDI CC value; int
        """
        self.debug(3,'Play/stop button action.')
        if (value > 63):
            self.song().start_playing()
        else:
            self.song().stop_playing()

    def _handle_record(self,value):        
        """Handle record button press.
           - value: incoming MIDI CC value; int
        """
        self.debug(3,'Record button action.')
        self.song().record_mode = (value > 63)

    # --- MIDI ---
    
    def process_midi(self, midi_channel, cc_no, value):
        """Process incoming MIDI CC events for this track, and pass them to
           the correct handler (defined by self._CC_HANDLERS as set up
           by the call to self._init_cc_handlers() )
           - midi_channel: MIDI channel of incomming message; int (1..16)
           - cc_no: MIDI CC number; int (0..127)
           - value: incoming CC value; int (0..127)
           - returns: whether midi event processed by handler here; bool
        """
        self.debug(5,f'Trying TransportControler.')
        if (midi_channel,cc_no) in self._CC_HANDLERS:
            self.debug(5,f'TransportController: handler found for CC {cc_no} on MIDI channel {midi_channel}.')
            handler = self._CC_HANDLERS[(midi_channel,cc_no)]
            handler(value)
            return True
        else:
            return False
    
    def build_midi_map(self, script_handle, midi_map_handle):
        """Map all transport controls on their associated MIDI CC numbers; make sure
           the right MIDI CC messages are forwarded to the remote script to be
           handled by the MIDI CC handlers defined here.
           - script_handle: reference to the main remote script class
               (whose receive_midi method will be called for any MIDI CC messages
               marked to be forwarded here)
           - midi_map_hanlde: MIDI map handle as passed to Ableton Live, to
               which MIDI mappings must be added.
        """
        self.debug(3,'Building transport MIDI map.')
        # Map CCs to be forwarded as defined in MIXER_CC_HANDLERS
        for (midi_channel,cc_no) in self._CC_HANDLERS:
            self.debug(4,f'TransportController: setting up handler for CC {cc_no} on MIDI channel {midi_channel}')
            Live.MidiMap.forward_midi_cc(script_handle, midi_map_handle, midi_channel - 1, cc_no)

   
