# ElectrOne
#
# Ableton Live MIDI Remote Script for the Electra One
#
# Author: Jaap-henk Hoepman (info@xot.nl)
#
# Distributed under the MIT License, see LICENSE
#

# Ableton Live imports
from _Framework.ControlSurface import ControlSurface
from _Generic.util import DeviceAppointer
import Live

from .Devices import get_predefined_patch_info
from .ElectraOneDumper import PatchInfo, construct_json_patchinfo, MIDI_CHANNEL

# MIDI_CHANNEL = 11 : imported from .ElectraOneDumper

DEBUG = True

class ElectraOne(ControlSurface):
    u""" Remote control script for the Electra One """

    def __init__(self, c_instance):
        ControlSurface.__init__(self, c_instance)
        # TODO: check that indeed an Electra One is connected
        self.__c_instance = c_instance
        self._appointed_device = None
        self._patch_info = None
        self.log_message("ElectraOne loaded.")
        # register a device appointer;  _set_appointed_device will be called when appointed device changed
        # see _Generic/util.py
        self._device_appointer = DeviceAppointer(song=self.__c_instance.song(), appointed_device_setter=self._set_appointed_device)

    def debug(self,m):
        if DEBUG:
            self.log_message(m)
        
    # for debugging
    def receive_midi(self, midi_bytes):
        self.log_message(f'ElectraOne receiving MIDI { midi_bytes }')


    # see https://docs.electra.one/developers/midiimplementation.html#upload-a-preset
    # Upload the patch (a json string) to the Electro One
    # 0xF0 SysEx header byte
    # 0x00 0x21 0x45 Electra One MIDI manufacturer Id
    # 0x01 Upload data
    # 0x01 Preset file
    # preset-json-data bytes representing ascii bytes of the preset file
    # 0xF7 SysEx closing byte
    #
    # patch is the json patch as a string
    def upload_patch(self,patch):
        self.log_message("ElectraOne uploading patch.")
        sysex_header = (0xF0, 0x00, 0x21, 0x45, 0x01, 0x01)
        sysex_patch = tuple([ ord(c) for c in patch ])
        sysex_close = (0xF7, )
        # TODO: mustb be sent over ElectraOne CTRL MIDI port
        self.debug(f"Patch = { patch }")
        self.__c_instance.send_midi(sysex_header + sysex_patch + sysex_close)
        
    # Get the patch for the specified device, either externally, predefined or
    # else construct it on the fly
    def get_patch(self,device):
        device_name = device.class_name
        self.debug(f"ElectraOne getting patch for { device_name }.")
        patch_info = get_predefined_patch_info(device_name)
        if patch_info:
            self.debug('Predefined patch found')
            return patch_info
        else:
            self.debug('Constructing patch on the fly...')
            # use ElectraOneDumper to construct a patch on the fly
            return construct_json_patchinfo( device_name, device.parameters )

    # Update the displayed values of the parameters in the (just uploaded) patch
    def update_values(self):
        self.debug("ElectraOne updating values.")
        if self._appointed_device != None:
            parameters = self._appointed_device.parameters
            for (i,p) in enumerate(parameters):
                # the index of the parameter in the list as returned by the device is the default cc if no map specified for it
                cc_no = self._patch_info.get_cc_for_parameter(p.original_name)
                if cc_no:
                    cc_value = p.value
                    # FIXME TODO: upload the actual value
                
    # Build a MIDI map for the currently selected device    
    def build_midi_map(self, midi_map_handle):
        self.debug("ElectraOne building map.")
        if self._appointed_device != None:
            parameters = self._appointed_device.parameters
            # FIXME: not clear how this is honoured in the Live.MidiMap.map_midi_cc call
            needs_takeover = True
            for p in parameters:
                if p.is_quantized:
                    map_mode = Live.MidiMap.MapMode.absolute
                else:
                    map_mode = Live.MidiMap.MapMode.absolute_14_bit
                # the index of the parameter in the list as returned by the device is the default cc if no map specified for it
                cc_no = self._patch_info.get_cc_for_parameter(p.original_name)
                if cc_no:
                    # BUG: this call internally adds 1 to the specified MIDI channel!!!
                    self.debug(f"Mapping { p.original_name } to CC { cc_no } on MIDI channel { MIDI_CHANNEL }")
                    Live.MidiMap.map_midi_cc(midi_map_handle, p, MIDI_CHANNEL-1, cc_no, map_mode, not needs_takeover)
        
    def update_display(self):
        return

    def _set_appointed_device(self, device):
        self.debug(f'ElectraOne device appointed { device.class_name }')
        if device != self._appointed_device:
            self._appointed_device = device
            if device != None:
                self._patch_info = self.get_patch(device)
                self.upload_patch(self._patch_info.get_patch())
                self.update_values()
                self.__c_instance.request_rebuild_midi_map()                

            
    def disconnect(self):
        u"""Called right before we get disconnected from Live
        """
        self._device_appointer.disconnect()                
