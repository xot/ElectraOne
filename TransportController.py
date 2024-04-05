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

class TransportController(ElectraOneBase):
    """Manage the transport (play/stop, record, rewind, forward).
    """
    
    def __init__(self, c_instance):
        """Initialise.
           - c_instance: Live interface object (see __init.py__)
        """
        ElectraOneBase.__init__(self, c_instance)
        # keep last displayed position to throttle updates
        self._lastpos = None
        self._add_listeners()
        self._init_cc_handlers()
        self.debug(0,'TransportController loaded.')

    # --- initialise values ---
    
    def refresh_state(self):
        """Send the states of the play/stop and record buttons to the E1
           (to bring them in sync)
        """
        self.debug(2,'Refreshing transport state.')
        self._on_record_mode_changed()
        self._on_is_playing_changed()
        self._on_position_changed()
        self._on_tempo_changed()

    def update_display(self):
        """ Called every 100 ms. Used to monitor rewind/forward buttons 
            (move backward or forward in a song while rewind or forward
             button pressed)
        """
        pass 
        
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
        self.song().add_current_song_time_listener(self._on_position_changed)        
        self.song().add_tempo_listener(self._on_tempo_changed)


    def _remove_listeners(self):
        """Remove all listeners added
        """
        self.song().remove_record_mode_listener(self._on_record_mode_changed)
        self.song().remove_is_playing_listener(self._on_is_playing_changed)
        self.song().remove_current_song_time_listener(self._on_position_changed)        
        self.song().remove_tempo_listener(self._on_tempo_changed)

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

    def _on_position_changed(self):
        """Update the value shown for the position control on the E1.
        """
        pos = self.song().get_current_beats_song_time()
        # throttle updates; ignore changes in ticks
        if (self._lastpos == None) or \
           (pos.bars != self._lastpos.bars) or \
           (pos.beats != self._lastpos.beats) or \
           (pos.sub_division != self._lastpos.sub_division):
            self._lastpos = pos
            self.debug(6,f'Position changed to {pos}.')
            if (ElectraOneBase.current_visible_slot == MIXER_PRESET_SLOT):
                self.set_position(str(pos)[:-4])
        
    def _on_tempo_changed(self):
        """Update the value shown for the tempo control on the E1.
        """
        tempo = f'{self.song().tempo:.2f}'
        self.debug(4,f'Tempo changed to {tempo}.')
        if (ElectraOneBase.current_visible_slot == MIXER_PRESET_SLOT):
            self.set_tempo(tempo)
        
    # --- Handlers ---
    
    def _init_cc_handlers(self):
        """Define handlers for incoming MIDI CC messages.
        """
        self._CC_HANDLERS = {
               (MIDI_MASTER_CHANNEL, POSITION_CC)  : self._handle_position
            ,  (MIDI_MASTER_CHANNEL, TEMPO_CC)     : self._handle_tempo
            ,  (MIDI_MASTER_CHANNEL, PLAY_STOP_CC) : self._handle_play_stop
            ,  (MIDI_MASTER_CHANNEL, RECORD_CC)    : self._handle_record
            }

    def _handle_position(self,value):
        """Handle position relative dial
           - value: incoming MIDI CC value: 7F,7E,.. is rewind, 01,02 is forward
        """
        self.debug(3,f'Position dial action: {value}.')
        if value > 63:
            delta = (value-128) * FORW_REW_JUMP_BY_AMOUNT
        else:
            delta = value * FORW_REW_JUMP_BY_AMOUNT
        self.song().jump_by(delta) # strange; this does NOT update the position straight away
        # when position is actually chagned, _on_position_changed is called
        # and the new position is sent to the E1
        
    def _handle_tempo(self,value):
        """Handle tempo relative dial
           - value: incoming MIDI CC value: 7F,7E,.. is slower, 01,02 is faster
        """
        self.debug(3,f'Tempo dial action: {value}.')
        if value > 63:
            delta = (value-128) * TEMPO_JUMP_BY_AMOUNT
        else:
            delta = value * TEMPO_JUMP_BY_AMOUNT
        self.song().tempo += delta
        
    def _handle_play_stop(self,value):        
        """Handle play/stop button press.
           - value: incoming MIDI CC value; int
        """
        self.debug(3,f'Play/stop button action: {value}.')
        if (value > 63):
            self.song().start_playing()
        else:
            self.song().stop_playing()

    def _handle_record(self,value):        
        """Handle record button press.
           - value: incoming MIDI CC value; int
        """
        self.debug(3,f'Record button action: {value}.')
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

   
