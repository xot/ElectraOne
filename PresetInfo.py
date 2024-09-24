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

from .UniqueParameters import make_device_parameters_unique

class PresetInfo:
    """ Class containing an E1 JSON preset,a LUA scripty and the
        associated CC-map
      - The preset is a JSON string in Electra One format.
      - The LUA script is (a possibly empty) string.
      - The MIDI cc mapping data is a CCMap (see CCInfo)
    """
    
    def __init__(self,json_preset,lua_script,cc_map):
        self._json_preset = json_preset
        self._lua_script = lua_script
        self._cc_map = cc_map

    def get_cc_map(self):
        """Return the CC map
           - result: the CC map; CCMap
        """
        assert self._cc_map != None, 'Empty cc-map.'
        return self._cc_map
    
    def get_preset(self):
        """Return the JSON preset as a string
           - result: preset; str
        """
        assert self._json_preset != None, 'Empty JSON preset.'
        return self._json_preset

    def get_lua_script(self):
        """Return the LUA script as a string
           - result: lua_script; str
        """
        assert self._lua_script != None, 'Empty LUA script.'
        return self._lua_script

    def dump(self, device, device_name, path, debug):
        """Dump the preset info for this device:
           the E1 JSON preset in <path>/<devicename>.epr
           the LUA script in <path>/<devicename>.lua        
           the CCmap in <path>/<devicename>.ccmap
           - device: device to dump; Live.Devices
           - device_name: name of device to dump; str
           - path: path to dump into, str
           - debug: function to log debugging ino
        """
        # (Note: we need to pass device to have access to ALL parameters in
        # the device, not only the ones in the ccmap.)
        debug(2,f'Dumping device: { device_name } in { path }.')
        # dump the preset JSON string 
        fname = f'{ path }/{ device_name }.epr'
        s = self.get_preset()
        with open(fname,'w') as f:            
            f.write(s)
        # dump the LUA script
        fname = f'{ path }/{ device_name }.lua'
        s = self.get_lua_script()
        with open(fname,'w') as f:            
            f.write(s)
        # dump the cc-map
        fname = f'{ path }/{ device_name }.ccmap'
        ccmap = self.get_cc_map()
        with open(fname,'w') as f:
            f.write('{')
            comma = False # concatenate list items with a comma; don't write a comma before the first list entry
            device_parameters = make_device_parameters_unique(device)
            for p in device_parameters:
                if comma:
                    f.write(',')
                comma = True
                ccinfo = ccmap.get_cc_info(p)
                if ccinfo.is_mapped():
                    f.write(f"'{ p.original_name }': { ccinfo }\n")
                else:
                    f.write(f"'{ p.original_name }': None\n")
            f.write('}')
        
    def validate(self, device, device_name, warning):
        """Check for internal consistency of PresetInfo and warn for
           any inconsistencies. Only checks CC map (for now).
           - device: device to which this PresetInfo belongs
           - device_name: name of the device
           - warning: function to call to write any warnings
        """
        assert self._cc_map !=  None, 'Validate expects a non-empty CC map'
        assert self._json_preset != None, 'Validate expects a non-empty JSON preset'
        self._cc_map.validate(device, device_name, warning)
