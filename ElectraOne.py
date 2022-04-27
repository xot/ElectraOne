# ElectraOne
#
# Ableton Live MIDI Remote Script for the Electra One
#
# Author: Jaap-henk Hoepman (info@xot.nl)
#
# Distributed under the MIT License, see LICENSE
#

# Ableton Live imports
from _Framework.ControlSurface import ControlSurface

# Local imports
from .EffectController import EffectController
from .MixerController import MixerController
from .config import check_configuration

# --- ElectraOne class

# TODO: not sure whether extending ControlSurface is needed...
class ElectraOne(ControlSurface):
    """Remote control script for the Electra One. Initialises an
       EffectController that handles the currently selected Effect/Instrument
       and a MixerController that handles the currently selected tracks volumes
       and sends, as well as the global transports and master volume. 
    """

    def __init__(self, c_instance):
        check_configuration()
        ControlSurface.__init__(self, c_instance)
        # TODO: check that indeed an Electra One is connected
        self.__c_instance = c_instance
        self._effect_controller = EffectController(c_instance)
        self._mixer_controller = MixerController(c_instance)
        self.log_message('Remote script loaded.')
        
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
        self._effect_controller.lock_to_device(device)

    def unlock_from_device(self, device):
        """Live can tell the script to unlock from a given device
        """
        self._effect_controller.unlock_from_device(device)

    def toggle_lock(self):
        """Script -> Live
        Use this function to toggle the script's lock on devices
        """
        # Weird; why is Ableton relegating this to the script?
        self.__c_instance.toggle_lock()

    
    def receive_midi(self, midi_bytes):
        """MIDI messages are only received through this function, when
           explicitly forwarded in 'build_midi_map' using
           Live.MidiMap.forward_midi_cc().
        """
        # Only MixerController needs to receive these
        self._mixer_controller.receive_midi(midi_bytes)


    def build_midi_map(self, midi_map_handle):
        """Build all MIDI maps.
        """
        self._effect_controller.build_midi_map(midi_map_handle)
        self._mixer_controller.build_midi_map(self.__c_instance.handle(),midi_map_handle)
        
    def update_display(self):
        """ Called every 100 ms. Used to execute scheduled tasks
        """
        self._effect_controller.update_display()
        self._mixer_controller.update_display()
                               
    def disconnect(self):
        """Called right before we get disconnected from Live
        """
        self._effect_controller.disconnect()
        self._mixer_controller.disconnect()
