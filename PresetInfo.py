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

from .CCInfo import CCInfo, UNMAPPED_CCINFO

class PresetInfo:
    """ Class containing an E1 JSON preset,a LUA scripty and the
        associated CC-map
      - The preset is a JSON string in Electra One format.
      - The LUA script is (a possibly empty) string.
      - The MIDI cc mapping data is a dictionary of Ableton Live original
        parameter names with their corresponding CCInfo (either as an untyped
        tuple when preloaded from from Devices.py, or a CCInfo object when
        constructed on the fly). This is hidden from the caller through
        get_ccinfo_for_parameter()
    """
    
    def __init__(self,json_preset,lua_script,cc_map):
        self._json_preset = json_preset
        self._lua_script = lua_script
        self._cc_map = cc_map

    def get_ccinfo_for_parameter(self,parameter):
        """Return the MIDI CC parameter info assigned to the device parameter
           - parameter: Ableton Live parameter; Live.DeviceParameter.DeviceParameter
           - result: a CCInfo object describing the assignment, or
             UNMAPPED_CCINFO if not mapped.
        """
        assert self._cc_map != None, 'Empty cc-map'
        # look up through parameter original_name which is should not change over
        # time (this is _Not_ guaranteed however: add entries to CC-map whenever
        # a parameter name does change
        if parameter.original_name in self._cc_map:
            v = self._cc_map[parameter.original_name]
            if type(v) is tuple:
                return CCInfo(v)
            else:
                return v # Then it is CCInfo 
        else:
            return UNMAPPED_CCINFO
        
    def get_preset(self):
        """Return the JSON preset as a string
           - result: preset; str
        """
        assert self._json_preset != None, 'Empty JSON preset'
        return self._json_preset

    def get_lua_script(self):
        """Return the LUA script as a string
           - result: lua_script; str
        """
        return self._lua_script

    def validate(self, device, device_name, warning):
        """Check for internal consistency of ccmap and warn for any unmapped
           or badly mapped parameters;
           this may (for example) indicate that Live added or renamed
           parameters the last time a preset was constructed 
           (Note that there are actually valid reasons to have several device
            parameters mapped to the same control/CC)
           - device: device to which this PresetInfo belongs
           - device_name: name of the device
           - warning: function to call to write any warnings
        """
        assert self._cc_map !=  None, 'Validate expects a non-empty CC map'
        assert self._json_preset != None, 'Validate expects a non-empty JSON preset'
        # check CC map consistency
        seen = []
        for cc_info in self._cc_map.values():
            # remember, for preloaded presets the cc_map actually contains tuples...
            if type(cc_info) is tuple:
                cc_info = CCInfo(cc_info)
            channel = cc_info.get_midi_channel()
            if channel not in range(1,17):
                warning(f'Bad MIDI channel {channel} in CC map.')
            cc_no = cc_info.get_cc_no()
            if cc_no not in range(0,128):
                warning(f'Bad MIDI CC parameter {cc_no} in CC map.')
            seeing = (channel, cc_no)
            if seeing in seen:
                warning(f'Duplicate {seeing} in CC map.')
            else:
                seen.append(seeing)
        # check parameter mappings
        pnames = [p.original_name for p in device.parameters]
        ccnames = self._cc_map.keys()
        for name in pnames:
            if not name in ccnames:
                self.warning(f'Unmapped parameter {name} found for {device_name}!')
        for name in ccnames:
            if not name in pnames:
                self.warning(f'Mapped parameter {name} does not exist for {device_name}!')
