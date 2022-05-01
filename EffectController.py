# EffectController
# - control devices (effects and instruments)
#
# Part of ElectraOne
#
# Ableton Live MIDI Remote Script for the Electra One
#
# Author: Jaap-henk Hoepman (info@xot.nl)
#
# Distributed under the MIT License, see LICENSE
#

# Python imports
import os

# Ableton Live imports
from _Generic.util import DeviceAppointer
import Live

# Local imports
from .config import *
from .CCInfo import CCInfo
from .PresetInfo import PresetInfo
from .Devices import get_predefined_preset_info
from .ElectraOneBase import ElectraOneBase 
from .ElectraOneDumper import ElectraOneDumper
# --- helper functions

# TODO: adapt to also get an appropriate name for MaxForLive devices
def get_device_name(device):
    return device.class_name

def build_midi_map_for_device(midi_map_handle, device, preset_info, debug):
    # Internal function to build the MIDI map for a device, also
    # used by TrackController and MasterController too to map the
    # ChannelEq device. Uses preset_info to get the CCInfo for device
    # parameters.
    if device != None:
        parameters = device.parameters
        # TODO/FIXME: not clear how this is honoured in the Live.MidiMap.map_midi_cc call
        needs_takeover = True
        for p in parameters:                
            ccinfo = preset_info.get_ccinfo_for_parameter(p)
            if ccinfo.is_mapped():
                if ccinfo.is_cc14():
                    map_mode = Live.MidiMap.MapMode.absolute_14_bit
                else:
                    map_mode = Live.MidiMap.MapMode.absolute
                cc_no = ccinfo.get_cc_no()
                midi_channel = ccinfo.get_midi_channel()
                # BUG: this call internally adds 1 to the specified MIDI channel!!!
                debug(3,f'Mapping { p.original_name } to CC { cc_no } on MIDI channel { midi_channel }')
                Live.MidiMap.map_midi_cc(midi_map_handle, p, midi_channel-1, cc_no, map_mode, not needs_takeover)

# TODO: bit of a hack to pass ElectraOneBase as sender_object
def update_values_for_device(device, preset_info,sender_object):
    # Internal function to update the displayed values for a device, also
    # used by TrackController and MasterController too to map the
    # ChannelEq device. Uses preset_info to get the CCInfo for device
    # parameters.
    if device:
        for p in device.parameters:
            ccinfo = preset_info.get_ccinfo_for_parameter(p)
            if ccinfo.is_mapped():
                sender_object.send_parameter_using_ccinfo(p,ccinfo)

                
# --- ElectraOne class

class EffectController(ElectraOneBase):
    """Remote control script for the Electra One
    """

    def __init__(self, c_instance):
        ElectraOneBase.__init__(self, c_instance)
        # TODO: check that indeed an Electra One is connected
        self._assigned_device = None
        self._assigned_device_locked = False
        self._preset_info = None
        # timer set when device appointed; countdown through update_display
        # until 0, in which case update_display calls the update_values function
        # If -1 no updating needed.
        self._value_update_timer = -1
        # register a device appointer;  _set_appointed_device will be called when appointed device changed
        # see _Generic/util.py
        self._device_appointer = DeviceAppointer(song=self.song(), appointed_device_setter=self._set_appointed_device)
        self.debug(0,'EffectController loaded.')
        
        
    def debug(self,level,m):
        """Write a debug message to the log, if debugging is enabled
        """
        if level < DEBUG:
            self.log_message(f'E1: {m}')

    # === presets ===

    # see https://docs.electra.one/developers/midiimplementation.html#upload-a-preset
    # Upload the preset (a json string) to the Electro One
    # 0xF0 SysEx header byte
    # 0x00 0x21 0x45 Electra One MIDI manufacturer Id
    # 0x01 Upload data
    # 0x01 Preset file
    # preset-json-data bytes representing ascii bytes of the preset file
    # 0xF7 SysEx closing byte
    #
    # preset is the json preset as a string
    def upload_preset(self,preset):
        """Upload an Electra One preset (given as a JSON string)
        """
        self.debug(1,'Uploading preset.')
        sysex_header = (0xF0, 0x00, 0x21, 0x45, 0x01, 0x01)
        sysex_preset = tuple([ ord(c) for c in preset ])
        sysex_close = (0xF7, )
        if not DUMP: # no need to write this to the log if the same thing is dumped
            self.debug(4,f'Preset = { preset }')
        self.send_midi(sysex_header + sysex_preset + sysex_close)
        
    def get_preset(self,device):
        """Get the preset for the specified device, either externally,
           predefined or else construct it on the fly.
        """
        device_name = get_device_name(device)
        self.debug(1,f'Getting preset for { device_name }.')
        preset_info = get_predefined_preset_info(device_name)
        if preset_info:
            self.debug(1,'Predefined preset found')
            return preset_info
        else:
            self.debug(1,'Constructing preset on the fly...')
            dumper = ElectraOneDumper(self, device_name, device.parameters)
            return dumper.get_preset()

    # === updating values ===

    def update_values(self):
        """Update the displayed values of the parameters in the
           (just uploaded) preset
        """
        self.debug(1,'Updating values.')
        update_values_for_device(self._assigned_device,self._preset_info,self)

    def build_midi_map(self, midi_map_handle):
        """Build a MIDI map for the currently selected device    
        """
        self.debug(1,'Building effect MIDI map.')
        build_midi_map_for_device(midi_map_handle, self._assigned_device, self._preset_info, self.debug)

    # === Others ===
    
    def update_display(self):
        """ Called every 100 ms; used to call update_values with a delay
        """
        if self._value_update_timer == 0:
            self.update_values()
        if self._value_update_timer >= 0:
            self._value_update_timer -= 1

    def dump_presetinfo(self,device,preset_info):
        """Dump the presetinfo: an ElectraOne JSON preset, and the MIDI CC map
        """
        # construct the folder to save in
        home = os.path.expanduser('~')
        path =  f'{ home }/{ LOCALDIR }/dumps'
        if not os.path.exists(path):                                        # try LOCALDIR as absolute directory
            path =  f'{ LOCALDIR }/dumps'
        if not os.path.exists(path):                                        # defaukt is HOME
            path = home
        device_name = get_device_name(device)
        fname = f'{ path }/{ device_name }.json'
        # dump the preset JSON string
        self.debug(1,f'dumping device: { device_name } in { fname }.')
        s = preset_info.get_preset()
        with open(fname,'w') as f:            
            f.write(s)
        # dump the cc-map
        fname = f'{ path }/{ device_name }.ccmap'
        with open(fname,'w') as f:
            f.write('{')
            comma = False                                                   # concatenate list items with a comma; don't write a comma before the first list entry
            for p in device.parameters:
                if comma:
                    f.write(',')
                comma = True
                ccinfo = preset_info.get_ccinfo_for_parameter(p)
                if ccinfo.is_mapped():
                    f.write(f"'{ p.original_name }': { ccinfo }\n")
                else:
                    f.write(f"'{ p.original_name }': None\n")
            f.write('}')

    # === handle device selection
    
    def lock_to_device(self, device):
        if device:
            self._assigned_device_locked = True
            self._assign_device(device)
            
    def unlock_from_device(self, device):
        if device and device == self._assigned_device:
            self._assigned_device_locked = False
            self._assign_device(self.song().appointed_device)


    def _assign_device(self, device):
        device_name = get_device_name(device)
        self.debug(1,f'Assigning device { device_name }')
        if device != self._assigned_device:
            self._assigned_device = device
            if device != None:
                self._preset_info = self.get_preset(device)
                if DUMP:
                    self.dump_presetinfo(device,self._preset_info)
                preset = self._preset_info.get_preset()
                self.upload_preset(preset)
                # set a delay depending on the length (~complexity) of the preset
                self._value_update_timer = int(len(preset)/200)
                self.request_rebuild_midi_map()                

    def _set_appointed_device(self, device):
        if not self._assigned_device_locked:
            self._assign_device(device)
        
    def disconnect(self):
        """Called right before we get disconnected from Live
        """
        self._device_appointer.disconnect()                
