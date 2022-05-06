# ElectraOne
#
# Ableton Live MIDI Remote Script for the Electra One
#
# Author: Jaap-henk Hoepman (info@xot.nl)
#
# Distributed under the MIT License, see LICENSE
#

# Ableton Live imports
#from _Framework.ControlSurface import ControlSurface

# Local imports
from .ElectraOneBase import ElectraOneBase 
from .EffectController import EffectController
from .MixerController import MixerController
from .config import *

# --- ElectraOne class

CC_STATUS = 0xB0
E1_SYSEX_PREFIX = (0xF0, 0x00, 0x21, 0x45) 
E1_SYSEX_PRESET_CHANGED = (0x7E, 0x02)  # followed by bank-number slot-number
SYSEX_TERMINATE = 0xF7

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
        self.__c_instance = c_instance
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
        self.__c_instance.toggle_lock()

    def receive_midi_cc(self, midi_bytes):
        (status,cc_no,value) = midi_bytes
        midi_channel = status - CC_STATUS + 1
        self._mixer_controller.process_midi(midi_channel,cc_no,value)


    def receive_midi_sysex(self, midi_bytes):
        self.debug(4,f'Handling SysEx { midi_bytes }.')
        if (len(midi_bytes) == 9) and \
           (midi_bytes[4:6] == E1_SYSEX_PRESET_CHANGED) and \
           (midi_bytes[8] == SYSEX_TERMINATE):
            self.debug(3,'Preset selected')
            if (midi_bytes[6:8] == MIXER_PRESET_SLOT):
                self.debug(3,'Mixer preset selected')
                self._mixer_controller.refresh_state()
            elif (midi_bytes[6:8] == EFFECT_PRESET_SLOT):  
                self.debug(3,'Effect preset selected')
                self._effect_controller.refresh_state()
                
    def receive_midi(self, midi_bytes):
        """MIDI messages are only received through this function, when
           explicitly forwarded in 'build_midi_map' using
           Live.MidiMap.forward_midi_cc().
        """
        self.debug(1,'Main receive MIDI called.')
        self.debug(2,f'MIDI bytes received (first 10) { midi_bytes[:10] }')
        if ((midi_bytes[0] & 0xF0) == CC_STATUS) and (len(midi_bytes) == 3):
            receive_midi_cc(midi_bytes)
        elif midi_bytes[0:4] == E1_SYSEX_PREFIX:
            self.receive_midi_sysex(midi_bytes)
        else:
            self.debug(2,'Unexpected MIDI bytes not processed.')

    def build_midi_map(self, midi_map_handle):
        """Build all MIDI maps.
        """
        self.debug(1,'Main build midi map called.') 
        self._effect_controller.build_midi_map(midi_map_handle)
        self._mixer_controller.build_midi_map(self.__c_instance.handle(),midi_map_handle)
        
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
        #self.debug(1,'Main update display called.') 
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


