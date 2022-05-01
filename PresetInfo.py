# PresetInfo
# - class to store the JSON preset and the associated CC-map
#
# Part of ElectraOne.
#
# Ableton Live MIDI Remote Script for the Electra One
#
# Author: Jaap-henk Hoepman (info@xot.nl)
#
# Distributed under the MIT License, see LICENSE

from .config import *
from .CCInfo import CCInfo, UNMAPPED_CC, IS_CC7, IS_CC14

UNMAPPED_CCINFO = CCInfo((MIDI_EFFECT_CHANNEL,IS_CC7,UNMAPPED_CC))

class PresetInfo:
    """ Class containing an E1 JSON preset and the associated CC-map
      - The preset is a JSON string in Electra One format.
      - The MIDI cc mapping data is a dictionary of Ableton Live original
        parameter names with their corresponding CCInfo (either as an untyped
        tuple when preloaded from from Devices.py, or a CCInfo object when
        constructed on the fly). This is hidden from the caller through
        get_ccinfo_for_parameter()
    """
    
    def __init__(self,json_preset,cc_map):
        self._json_preset = json_preset
        self._cc_map = cc_map

    def get_ccinfo_for_parameter(self,parameter):
        """Return the MIDI CC parameter info assigned to the device parameter
           (looked up through it's original_name which is guaranteed (?).
           not to change over time.
           Return default CCInfo if not mapped.
        """
        assert self._cc_map != None, 'Empty cc-map'
        if parameter.original_name in self._cc_map:
            v = self._cc_map[parameter.original_name]
            if type(v) is tuple:
                return CCInfo(v)
            else:
                return v  
        else:
            return UNMAPPED_CCINFO
        
    def get_preset(self):
        """Retrun the JSON preset as a string
        """
        assert self._json_preset != None, 'Empty JSON preset'
        return self._json_preset
