# ElectraOne
#
# Ableton Live MIDI Remote Script for the Electra One
#
# Author: Jaap-henk Hoepman (info@xot.nl)
#
# Distributed under the MIT License, see LICENSE
#

# Local imports
from .EffectController import EffectController

# --- ElectraOne class

class ElectraOne:
    """Remote control script for the Electra One. Initialises an
       EffectController that handles the currently selected Effect/Instrument
       and a MixerController that handles the currently selected tracks volumes
       and sends, as well as the global transports and master volume. 
    """

    def __init__(self, c_instance):
        # TODO: check that indeed an Electra One is connected
        self.__c_instance = c_instance
        sefl._effectcontroller = EffectControler(c_instance)
        # register a device appointer;  _set_appointed_device will be called when appointed device changed
        # see _Generic/util.py this is forwarded to EffectController
        self._device_appointer = DeviceAppointer(song=self.__c_instance.song(), appointed_device_setter=self._set_appointed_device)
        self.log_message('ElectraOne loaded.')
        
        
    def receive_midi(self, midi_bytes):
        """MIDI messages are only received through this function, when
           explicitly forwarded in 'build_midi_map'.
        """
        self._effect_controller.receive_midi(midi_bytes)


    def update_display(self):
        """ Called every 100 ms
        """
        self._effect_controller.update_display()

                               
    def _set_appointed_device(self, device):
        self._effect_controller._set_appointed_device(device)
            
    def disconnect(self):
        """Called right before we get disconnected from Live
        """
        self._effect_controller.disconnect()
        self._device_appointer.disconnect()                
