# ElectraOne
#
# Ableton Live MIDI Remote Script for the Electra One
#
# Author: Jaap-henk Hoepman (info@xot.nl)
#
# Distributed under the MIT License, see LICENSE
#

# Python imports
import json

# Local imports
from .ElectraOneBase import ElectraOneBase 
from .EffectController import EffectController
from .MixerController import MixerController
from .config import *

# SysEx defines and helpers

CC_STATUS = 0xB0
E1_SYSEX_PREFIX = (0xF0, 0x00, 0x21, 0x45) 
E1_SYSEX_PRESET_CHANGED = (0x7E, 0x02)  # followed by bank-number slot-number and terminated by 0xF7
E1_SYSEX_ACK = (0x7E, 0x01) # followed by two zero's (reserved) and terminated by 0xF7
E1_SYSEX_NACK = (0x7E, 0x00) # followed by two zero's (reserved) and terminated by 0xF7
E1_SYSEX_REQUEST_RESPONSE = (0x01, 0x7F) # followed by json data and terminated by 0xF7
SYSEX_TERMINATE = 0xF7

E1_SYSEX_REQUEST = (0xF0, 0x00, 0x21, 0x45, 0x02, 0x7F, 0xF7)

def is_sysex_preset_changed(midi_bytes):
    return (len(midi_bytes) == 9) and \
           (midi_bytes[4:6] == E1_SYSEX_PRESET_CHANGED) and \
           (midi_bytes[8] == SYSEX_TERMINATE)

def is_sysex_ack(midi_bytes):
    return (len(midi_bytes) == 9) and \
           (midi_bytes[4:6] == E1_SYSEX_ACK) and \
           (midi_bytes[8] == SYSEX_TERMINATE)

def is_sysex_nack(midi_bytes):
    return (len(midi_bytes) == 9) and \
           (midi_bytes[4:6] == E1_SYSEX_NACK) and \
           (midi_bytes[8] == SYSEX_TERMINATE)

def is_sysex_request_response(midi_bytes):
    return (midi_bytes[4:6] == E1_SYSEX_REQUEST_RESPONSE) and \
           (midi_bytes[len(midi_bytes)-1] == SYSEX_TERMINATE)

# --- ElectraOne class


class ElectraOne(ElectraOneBase):
    """Remote control script for the Electra One. Initialises an
       EffectController that handles the currently selected Effect/Instrument
       and a MixerController that handles the currently selected tracks volumes
       and sends, as well as the global transports and master volume. 
    """

    def __init__(self, c_instance):
        check_configuration()
        ElectraOneBase.__init__(self, c_instance)
        # TODO: check that indeed an Electra One is connected
        self.send_midi(E1_SYSEX_REQUEST)
        self._effect_controller = EffectController(c_instance)
        self._mixer_controller = MixerController(c_instance)
        self.log_message('ElectraOne remote script loaded.')
        
    def suggest_input_port(self):
        """Tell Live the name of the preferred input port name.
        """
        return 'Electra Controller (Electra Port 1)'

    def suggest_output_port(self):
        """Tell Live the name of the preferred output port name.
        """
        return 'Electra Controller (Electra Port 1)'

    def can_lock_to_devices(self):
        """Live can ask the script whether it can be locked to devices
        """
        return True

    def lock_to_device(self, device):
        """ Live can tell the script to lock to a given device
        """
        self.debug(1,'Main lock to device called.') 
        self._effect_controller.lock_to_device(device)

    def unlock_from_device(self, device):
        """Live can tell the script to unlock from a given device
        """
        self.debug(1,'Main unlock called.') 
        self._effect_controller.unlock_from_device(device)

    def toggle_lock(self):
        """Script -> Live
        Use this function to toggle the script's lock on devices
        """
        # Weird; why is Ableton relegating this to the script?
        self.debug(1,'Main toggle lock called.') 
        self.get_c_instance().toggle_lock()

    def _process_midi_cc(self, midi_bytes):
        """Process incoming MIDI CC message.
        """
        (status,cc_no,value) = midi_bytes
        midi_channel = status - CC_STATUS + 1
        self._mixer_controller.process_midi(midi_channel,cc_no,value)

    def _do_preset_changed(self, midi_bytes):
        self.debug(3,'Preset selected on the E1')
        if (midi_bytes[6:8] == MIXER_PRESET_SLOT):
            self.debug(3,'Mixer preset selected')
            self._mixer_controller.refresh_state()
        elif (midi_bytes[6:8] == EFFECT_PRESET_SLOT):  
            self.debug(3,'Effect preset selected')
            self._effect_controller.refresh_state()
        else:
            self.debug(3,'Other preset selected (ignoring)')                

    def _do_ack(self, midi_bytes):
        self.debug(3,'ACK received.')
        
    def _do_nack(self, midi_bytes):
        self.debug(3,'NACK received.')

    def _do_request_response(self, midi_bytes):
        json_bytes = midi_bytes[6:-1] # all bytes after the command, except the terminator byte 
        json_str = ''.join(chr(c) for c in json_bytes)
        self.debug(3,f'Request response received: {json_str}' )
        # json_dict = json.loads(json_str)

    def _process_midi_sysex(self, midi_bytes):
        """Process incoming MIDI SysEx message. Expected SysEx:
           - message informing script of preset selection change on E1
        """
        self.debug(5,f'Handling SysEx { midi_bytes }.')
        if is_sysex_preset_changed(midi_bytes):
            self._do_preset_changed(midi_bytes)
        elif is_sysex_nack(midi_bytes):
            self._do_nack(midi_bytes)
        elif is_sysex_ack(midi_bytes):
            self._do_ack(midi_bytes)
        elif is_sysex_request_response(midi_bytes):
            self._do_request_response(midi_bytes)
                
    def receive_midi(self, midi_bytes):
        """MIDI messages are only received through this function, when
           explicitly forwarded in 'build_midi_map' using
           Live.MidiMap.forward_midi_cc().
        """
        self.debug(3,'Main receive MIDI called.')
        self.debug(3,f'MIDI bytes received (first 10) { midi_bytes[:10] }')
        if ((midi_bytes[0] & 0xF0) == CC_STATUS) and (len(midi_bytes) == 3):
            # is a CC
            self._process_midi_cc(midi_bytes)
        elif midi_bytes[0:4] == E1_SYSEX_PREFIX:
            # is a SysEx from the E1
            self._process_midi_sysex(midi_bytes)
        else:
            self.debug(2,'Unexpected MIDI bytes not processed.')

    def build_midi_map(self, midi_map_handle):
        """Build all MIDI maps.
        """
        self.debug(1,'Main build midi map called.') 
        self._effect_controller.build_midi_map(midi_map_handle)
        self._mixer_controller.build_midi_map(self.get_c_instance().handle(),midi_map_handle)
        
    def refresh_state(self):
        """Appears to be called by Live when it thinks the state of the
           remote controller needs to be updated.
        """
        self.debug(1,'Main refresh state called.') 
        self._effect_controller.refresh_state()
        self._mixer_controller.refresh_state()
    
    def update_display(self):
        """ Called every 100 ms. Used to execute scheduled tasks
        """
        self.debug(3,'Main update display called.') 
        self._effect_controller.update_display()
        self._mixer_controller.update_display()
                               
    def connect_script_instances(self,instanciated_scripts):
        """ Called by the Application as soon as all scripts are initialized.
            You can connect yourself to other running scripts here.
        """
        self.debug(1,'Main connect script instances called.') 
        pass

    def disconnect(self):
        """Called right before we get disconnected from Live
        """
        self.debug(1,'Main disconnect called.') 
        self._effect_controller.disconnect()
        self._mixer_controller.disconnect()


