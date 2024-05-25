# Devices
# - Keep track of predefined presets
#
# Ableton Live MIDI Remote Script for the Electra One
#
# Author: Jaap-henk Hoepman (info@xot.nl)
#
# Distributed under the MIT License, see LICENSE
#

# Python imports
import os
import unicodedata

# Local imports
from .ElectraOneBase import ElectraOneBase
from .PresetInfo import PresetInfo
from .CCInfo import CCMap

class Devices(ElectraOneBase):
    # Dictionary with preset info (preset JSON, MIDI cc mapping, and LUA script)
    # for known devices (indexed by device.original_name and then by a
    # version triple; (0,0,0) for the default valid for all versions
    #
    # Each entry contains
    # - The preset is a JSON string in Electra One format.
    #   (The current implementation assumes that all quantized parameters
    #   are 7-bit absolute CC values while all non quantized parameters are
    #   14-bit absolute values)
    # - The LUA script is a string, possibly empty
    # - The MIDI cc mapping data is a dictionary of Ableton Live original parameter
    #   names with their corresponding MIDI CCInfo values (as ordinary tuples)
    #   in the preset. The CCInfo data must match the info in the preset used for
    #   the same parameter.

    def __init__(self,c_instance):
        """Load the predefined presets from file and store their data
           internally.
        """
        ElectraOneBase.__init__(self, c_instance)
        self.debug(1,'Constructing DEVICES.')
        # load default LUA script
        assert os.path.exists(self.luascriptfname()), f'Error: Default LUA script {self.luascriptfname()} does not exist.'
        self.debug(2,f'Loading default LUA script {self.luascriptfname()}.')
        with open(self.luascriptfname(),'r') as inf:
            self._default_lua_script = inf.read()
        # Dictionary of device presets in preloaded to dump (see above for structure)
        self._DEVICES = {}
        assert os.path.exists(self.preloadedpath()), f'Error: Folder {self.preloadedpath()} does not exist.'
        self.debug(2,f'Scanning {self.preloadedpath()} for devices.')
        preset_paths = self.preloadedpath().glob('*.epr')
        # process each preset path and store in DEVICES
        for preset_path in preset_paths:
            self._process_preset(preset_path)

    def _extract_version_from_name(self,device_versioned_name):
        """Extract the canonical device name and the version information from
           a versioned device name (<devicename>.<major>.<minor>.<patch,
           with all three version integers optional)
           result: device name, version tuple; (str, (int,int,int))
        """
        extended_name = device_versioned_name + '.0.0.0' # make sure enough version fields exist
        splits = extended_name.rsplit('.')
        return (splits[0] , (int(splits[1]),int(splits[2]),int(splits[3])))

    def _process_preset(self,preset_path):
        """Process one preset, storing its data in DEVICES
           - preset_path: path to .epr file containing JSON preset
        """
        self.debug(5,f'Processing {preset_path}.')
        json_preset_path = preset_path
        lua_script_path = preset_path.with_suffix('.lua')
        ccmap_path = preset_path.with_suffix('.ccmap')
        device_versioned_name = preset_path.stem
        # Ugh: Mac uses different encoding for UTF; normalise so that
        # device name returned by Ableton corresponds to device name
        # read from file system; deals with special letters like ä in
        # device names
        # (https://stackoverflow.com/questions/9757843/unicode-encoding-for-filesystem-in-mac-os-x-not-correct-in-python)
        device_versioned_name = unicodedata.normalize('NFC',str(device_versioned_name))
        (device_name,version) = self._extract_version_from_name(device_versioned_name)
        # create new dictionary entry if necessary
        if device_name not in self._DEVICES:
            self._DEVICES[device_name] = {}
        self.debug(5,f'Predefining {device_name} ({device_versioned_name}) for Live version {version} or higher.')
        # load and process the .epr preset
        with open(json_preset_path,'r') as inf:
            json_preset = inf.read()
        # load the .lua script if it exist
        lua_script = ""
        # append the .lua if it exists
        if os.path.exists(lua_script_path):
            with open(lua_script_path,'r') as inf:
                lua_script += inf.read()
        # load the .ccmap
        with open(ccmap_path,'r') as inf:
            ccmap_str = inf.read()
        # create a ccmap from the string 
        ccmap = CCMap(ccmap_str)
        preset_info = PresetInfo(json_preset,lua_script,ccmap)
        self._DEVICES[device_name][version] = (device_versioned_name,preset_info)

    def get_default_lua_script(self):
        """Return the default LUA script, loaded from DEFAULT_LUA_SCRIPT_FILE
           or referring ot the one already preloaded on the E1
        """
        if ElectraOneBase.E1_PRELOADED_PRESETS_SUPPORTED:
            # in this case we assume (!) the defualt.lua is preloaded on E1
            return 'require("xot/default")\n'
        else:
            return self._default_lua_script

    def get_predefined_preset_info(self,device_name):
        """Return the predefined preset information for a device,
           (None,None) if it doesn't exist.
           Tries to find Live version specific presets for a device,
           so returns also the version specific name if found.
           - device_name: (class)name for a device to lookup
           - result: tuple versioned name, preset info ; (str,PresetInfo)
        """
        if device_name in self._DEVICES:
            presets = self._DEVICES[device_name]
            versions = list(presets.keys())
            # find most recent versioned preset for current live version
            closest = (0,0,0)
            for version in versions:
                if (closest < version) and (version <= ElectraOneBase.LIVE_VERSION):
                    closest = version
            return presets[closest]
        else:
            return (None,None)

