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
           - parameter: Ableton Live parameter; Live.DeviceParameter.DeviceParameter
           - result: a CCInfo object describing the assignment, or
             UNMAPPED_CCINFO if not mapped.
        """
        assert self._cc_map != None, 'Empty cc-map'
        # look up through parameter original_name which is guaranteed (?) not
        # to change over time.
        if parameter.original_name in self._cc_map:
            v = self._cc_map[parameter.original_name]
            if type(v) is tuple:
                return CCInfo(v)
            else:
                return v # Then it is CCInfo 
        else:
            return UNMAPPED_CCINFO
        
    def get_preset(self):
        """Retrun the JSON preset as a string
           - result: preset; str
        """
        assert self._json_preset != None, 'Empty JSON preset'
        return self._json_preset

    def validate(self):
        """ Check for internal consistency; return first found error as string.
            (Note that there are actually valid reasons to have several device
             parameters mapped to the same control/CC)
        """
        seen = []
        duplicates = set()
        assert self._cc_map !=  None, 'Validate expects a non-empty CC map'
        assert self._json_preset != None, 'Validate expects a non-empty JSON preset'
        for cc_info in self._cc_map.values():
            # remember, for preloaded presets the cc_map actually contains tuples...
            if type(cc_info) is tuple:
                cc_info = CCInfo(cc_info)
            channel = cc_info.get_midi_channel()
            if channel not in range(1,17):
                return f'Bad MIDI channel {channel} in CC map.'
            cc_no = cc_info.get_cc_no()
            if cc_no not in range(0,128):
                return f'Bad MIDI CC parameter {cc_no} in CC map.'
            seeing = (channel, cc_no)
            if seeing in seen:
                duplicates.add(seeing)
            else:
                seen.append(seeing)
        if len(duplicates) > 0:
            return f'Warning: Duplicates { duplicates } in CC map.'
        else:
            return None
