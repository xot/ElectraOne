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
from .PropertyControllers import PropertyControllers

SCALES = ['Major', 'Minor', 'Dorian', 'Mixolydian' ,'Lydian' ,'Phrygian' ,'Locrian', 'Whole Tone', 'Half-whole Dim.', 'Whole-half Dim.', 'Minor Blues', 'Minor Pentatonic', 'Major Pentatonic', 'Harmonic Minor', 'Harmonic Major', 'Dorian #4', 'Phrygian Dominant', 'Melodic Minor', 'Lydian Augmented', 'Lydian Dominant', 'Super Locrian', 'Bhairav', 'Hungarian Minor', '8-Tone Spanish', 'Hirajoshi', 'In-Sen', 'Iwato', 'Kumoi', 'Pelog Selisir', 'Pelog Tembung', 'Messaien 3', 'Messaien 4', 'Messaien 5', 'Messaien 6', 'Messaien 7']    

class TransportController(PropertyControllers):
    """Manage the transport (play/stop, record, rewind, forward).
    """
    
    def __init__(self, c_instance):
        """Initialise.
           - c_instance: Live interface object (see __init.py__)
        """
        PropertyControllers.__init__(self, c_instance)
        # keep last displayed position to throttle updates
        self._lastpos = None
        # add property controllers
        self.add_on_off_property(self.song(),'record_mode',MIDI_MASTER_CHANNEL,RECORD_CC)        
        self.add_property(self.song(),'is_playing',MIDI_MASTER_CHANNEL,PLAY_STOP_CC,self._handle_play_stop,self._on_is_playing_changed)
        self.add_property(self.song(),'tempo',MIDI_MASTER_CHANNEL,TEMPO_CC,self._handle_tempo,self._on_tempo_changed)        
        self.add_property(self.song(),'current_song_time',MIDI_MASTER_CHANNEL,POSITION_CC,self._handle_position,self._on_position_changed)        
        if ElectraOneBase.E1_DAW:
            self.add_property(self.song(),'tap_tempo',MIDI_MASTER_CHANNEL,TAP_TEMPO_CC,self._handle_tap_tempo,None)        
            self.add_on_off_property(self.song(),'nudge_down',MIDI_MASTER_CHANNEL,NUDGE_DOWN_CC)            
            self.add_on_off_property(self.song(),'nudge_up',MIDI_MASTER_CHANNEL,NUDGE_UP_CC)            
            self.add_on_off_property(self.song(),'metronome',MIDI_MASTER_CHANNEL,METRONOME_CC)
            self.add_list_property(self.song(),'clip_trigger_quantization',MIDI_MASTER_CHANNEL,QUANTIZATION_CC)
            self.add_list_property(self.song(),'root_note',MIDI_MASTER_CHANNEL,ROOT_NOTE_CC)
            if ElectraOneBase.LIVE_VERSION >= (12,0,5):
                self.add_on_off_property(self.song(),'scale_mode`',MIDI_MASTER_CHANNEL,SCALE_MODE_CC)            
            self.add_list_property(self.song(),'scale_name',MIDI_MASTER_CHANNEL,SCALE_NAME_CC,SCALES)
            self.add_on_off_property(self.song(),'arrangement_overdub',MIDI_MASTER_CHANNEL,ARRANGEMENT_OVERDUB_CC)
            self.add_on_off_property(self.song(),'session_automation_record',MIDI_MASTER_CHANNEL,SESSION_AUTOMATION_RECORD_CC)
            self.add_on_off_property(self.song(),'re_enable_automation_enabled',MIDI_MASTER_CHANNEL,RE_ENABLE_AUTOMATION_ENABLED_CC)
            self.add_on_off_property(self.song(),'session_record',MIDI_MASTER_CHANNEL,SESSION_RECORD_CC)
            self.add_property(self.song(),'loop_start',MIDI_MASTER_CHANNEL,LOOP_START_CC,self._handle_loop_start,self._on_loop_start_changed)        
            self.add_on_off_property(self.song(),'punch_in',MIDI_MASTER_CHANNEL,PUNCH_IN_CC)
            self.add_on_off_property(self.song(),'loop',MIDI_MASTER_CHANNEL,LOOP_CC)
            self.add_on_off_property(self.song(),'punch_out',MIDI_MASTER_CHANNEL,PUNCH_OUT_CC)
            self.add_property(self.song(),'loop_length',MIDI_MASTER_CHANNEL,LOOP_LENGTH_CC,self._handle_loop_length,self._on_loop_length_changed)        
            self.add_property(self.song(),'undo',MIDI_MASTER_CHANNEL,UNDO_CC,self._handle_undo,None)        
            self.add_property(self.song(),'redo',MIDI_MASTER_CHANNEL,REDO_CC,self._handle_redo,None)        
        self.debug(0,'TransportController loaded.')

    # --- initialise values ---

    # refresh_state() and disconnect() inherited from PropertyControllers

    def update_display(self):
        """ Called every 100 ms. 
        """
        pass
        
    # --- Special listeners
            
    def _on_is_playing_changed(self):
        """Update the value shown for the play/stop control on the E1.
        """
        self.debug(3,'Stop/play changed.')
        value = 127 * self.song().is_playing  # True = 127; False = 0
        self.send_midi_cc7(MIDI_MASTER_CHANNEL, PLAY_STOP_CC, value)

    def _on_position_changed(self):
        """Update the value shown for the position control on the E1.
        """
        pos = self.song().get_current_beats_song_time()
        # throttle updates; ignore changes in ticks
        if (self._lastpos == None) or \
           (pos.bars != self._lastpos.bars) or \
           (pos.beats != self._lastpos.beats) or \
           ((pos.sub_division != self._lastpos.sub_division) and POSITION_FINE):
            self._lastpos = pos
            self.debug(6,f'Position changed to {pos}.')
            if (ElectraOneBase.current_visible_slot == MIXER_PRESET_SLOT):
                self.set_position(str(pos)[:-4])

    def _on_loop_start_changed(self):
        """Update the value shown for the loop start control on the E1.
        """
        pos = self.song().get_beats_loop_start()
        self.debug(4,f'Loop start changed to {pos}.')
        if (ElectraOneBase.current_visible_slot == MIXER_PRESET_SLOT):
            self.set_loop_start(str(pos)[:-4])
        
    def _on_loop_length_changed(self):
        """Update the value shown for the loop length control on the E1.
        """
        pos = self.song().get_beats_loop_length()
        self.debug(4,f'Loop start changed to {pos}.')
        if (ElectraOneBase.current_visible_slot == MIXER_PRESET_SLOT):
            self.set_loop_length(str(pos)[:-4])
        
    def _on_tempo_changed(self):
        """Update the value shown for the tempo control on the E1.
        """
        tempo = f'{self.song().tempo:.2f}'
        self.debug(4,f'Tempo changed to {tempo}.')
        if (ElectraOneBase.current_visible_slot == MIXER_PRESET_SLOT):
            self.set_tempo(tempo)
                
    # --- Special handlers ---
    
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

    def _handle_loop_start(self,value):
        """Handle loop start relative dial
           - value: incoming MIDI CC value: 7F,7E,.. is rewind, 01,02 is forward
        """
        self.debug(3,f'Loop start dial action: {value}.')
        if value > 63:
            delta = (value-128) * FORW_REW_JUMP_BY_AMOUNT
        else:
            delta = value * FORW_REW_JUMP_BY_AMOUNT
        self.song().loop_start += delta
        
    def _handle_loop_length(self,value):
        """Handle loop length relative dial
           - value: incoming MIDI CC value: 7F,7E,.. is rewind, 01,02 is forward
        """
        self.debug(3,f'Loop length dial action: {value}.')
        if value > 63:
            delta = (value-128) * FORW_REW_JUMP_BY_AMOUNT
        else:
            delta = value * FORW_REW_JUMP_BY_AMOUNT
        self.song().loop_length += delta
        
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
        
    def _handle_tap_tempo(self,value):
        """Tap tempo
        """
        if value > 63:
            self.debug(3,'Tap tempo pressed.')
            self.song().tap_tempo()

    def _handle_undo(self,value):
        """Undo
        """
        if value > 63:
            self.debug(3,'Undo pressed.')
            self.song().undo()

    def _handle_redo(self,value):
        """Redo
        """
        if value > 63:
            self.debug(3,'Redo pressed.')
            self.song().redo()
            
    def _handle_play_stop(self,value):        
        """Handle play/stop button press.
           - value: incoming MIDI CC value; int
        """
        self.debug(3,f'Play/stop button action: {value}.')
        if (value > 63):
            self.song().start_playing()
        else:
            self.song().stop_playing()

    # --- MIDI ---
    
    # all inherited from PropertyControllers   
