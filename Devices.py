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
import json

# Local imports
from .ElectraOneBase import ElectraOneBase
from .PresetInfo import PresetInfo
from .CCInfo import CCMap

# Path to file containing the default LUA script that always needs to be
# included
DEFAULT_LUA_SCRIPT_FILE  = 'default.lua'

class Devices(ElectraOneBase):
    # Dictionary with preset and MIDI cc mapping data for known devices
    # (indexed by device.original_name and then by a triple containing
    # version info, (0,0,0) for the default valid for all versions
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
        ElectraOneBase.__init__(self, c_instance)
        self.debug(1,'Constructing DEVICES.')
        # get paths
        preloaded_path = ElectraOneBase.REMOTE_SCRIPT_PATH / 'preloaded'
        luascript_path = ElectraOneBase.REMOTE_SCRIPT_PATH / DEFAULT_LUA_SCRIPT_FILE
        # load LUA script
        if os.path.exists(luascript_path):
            self.debug(2,f'Loading default LUA script {luascript_path}.')
            with open(luascript_path,'r') as inf:
                self.default_lua_script = inf.read()
        else:
            self.debug(2,f'Warning: Default LUA script {luascript_path} not found.')
            self.default_lua_script = ''
        # Dictionary of device presets in preloaded to dump
        self.DEVICES = {}
        self.debug(2,f'Scanning {preloaded_path} for devices.')
        preset_paths = preloaded_path.glob('*.epr')
        # process each preset path and store in DEVICES
        for preset_path in preset_paths:
            self.process_preset(preset_path)

    def get_default_lua_script(self):
        """Return the default LUA script, loaded from DEFAULT_LUA_SCRIPT_FILE
        """
        return self.default_lua_script

    def extract_version_from_name(self,device_versioned_name):
        """Return a tuple (name, version-3-tuple)
        """
        extended_name = device_versioned_name + '.0.0.0' # make sure enough version fields exist
        splits = extended_name.rsplit('.')
        return (splits[0] , (int(splits[1]),int(splits[2]),int(splits[3])))

    def process_preset(self,preset_path):
        """Process one preset, storing its data in DEVICES
        """
        self.debug(5,f'Processing {preset_path}.')
        json_preset_path = preset_path
        lua_script_path = preset_path.with_suffix('.lua')
        ccmap_path = preset_path.with_suffix('.ccmap')
        device_versioned_name = preset_path.stem
        (device_name,version) = self.extract_version_from_name(device_versioned_name)
        if device_name not in self.DEVICES:
            self.DEVICES[device_name]={}
        self.debug(5,f'Predefining {device_name} ({device_versioned_name}) for Live version {version} or higher.')
        # load and process the .epr preset
        with open(json_preset_path,'r') as inf:
            #print('- Loading preset JSON.')
            json_load = json.load(inf)
            json_preset = json.dumps(json_load, separators=(',', ':'))
            # escape single quotes in json_preset; it will be written
            # as a single-quoted string to Devices.py
            filter_quotes = str.maketrans({ "'": "\\'"})
            filtered_json_preset = json_preset.translate(filter_quotes)
        # load the .lua script if it exist
        lua_script = ""
        # append the .lua if it exists
        if os.path.exists(lua_script_path):
            with open(lua_script_path,'r') as inf:
                #print('- LUA script found. Loading.')
                lua_script += inf.read()
        # escape single quotes in json_preset; it will be written
        # as a single-quoted string to Devices.py
        filter_quotes = str.maketrans({ "'": "\\'"})
        filtered_lua_script = lua_script.translate(filter_quotes)
        # load the .ccmap
        with open(ccmap_path,'r') as inf:
            ccmap_str = inf.read()
            # Remove newlines from ccmap
            # TODO: commented out to allow comments in CC-maps
            #filter_newlines = str.maketrans({ '\n': None})
            #ccmap = ccmap.translate(filter_newlines)
        # parse the ccmap string 
        ccmap = CCMap(ccmap_str)
        preset_info = PresetInfo(filtered_json_preset,filtered_lua_script,ccmap)
        preset = (device_versioned_name,preset_info)
        self.DEVICES[device_name][version]=preset

    def get_predefined_preset_info(self,device_name):
        """Return the predefined preset information for a device, None if it
        doesn't exist. Tries to find Live version specific presets for a device,
        so returns also the version specific name if found
        """
        # try loading version specific definitions
        # e.g. Echo.12.0 or Echo.12
        if device_name in self.DEVICES:
            presets = self.DEVICES[device_name]
            versions = list(presets.keys())
            versions.sort()
            i = 0
            # versions[0]=(0,0,0) always
            while (i < len(versions)) and (versions[i] <= ElectraOneBase.LIVE_VERSION):
                i += 1
            assert i > 0, 'Empty preset dict encountered.'
            return presets[versions[i-1]]
        else:
            return (None,None)

