# ElectraOne
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
from _Framework.ControlSurface import ControlSurface
from _Generic.util import DeviceAppointer
import Live

# Local imports
from .Devices import get_predefined_preset_info
from .ElectraOneDumper import PresetInfo, construct_json_presetinfo, cc_value_for_item_idx, MIDI_CHANNEL, is_cc14, get_cc
# from .ElecraOneDumper import *
from .config import *

class ElectraOne(ControlSurface):
    """Remote control script for the Electra One
    """

    def __init__(self, c_instance):
        ControlSurface.__init__(self, c_instance)
        # TODO: check that indeed an Electra One is connected
        self.__c_instance = c_instance
        self._appointed_device = None
        self._preset_info = None
        # register a device appointer;  _set_appointed_device will be called when appointed device changed
        # see _Generic/util.py
        self._device_appointer = DeviceAppointer(song=self.__c_instance.song(), appointed_device_setter=self._set_appointed_device)
        self.log_message('ElectraOne loaded.')

    def debug(self,m):
        """Write a debug message to the log, if debugging is enabled
        """
        if DEBUG:
            self.log_message(m)
        
    # for debugging
    def receive_midi(self, midi_bytes):
        self.debug(f'ElectraOne receiving MIDI { midi_bytes }')


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
        self.debug('ElectraOne uploading preset.')
        sysex_header = (0xF0, 0x00, 0x21, 0x45, 0x01, 0x01)
        sysex_preset = tuple([ ord(c) for c in preset ])
        sysex_close = (0xF7, )
        if not DUMP: # no need to write this to the log if the same thins is dumped
            self.debug(f'Preset = { preset }')
        self.__c_instance.send_midi(sysex_header + sysex_preset + sysex_close)
        
    def get_preset(self,device):
        """Get the preset for the specified device, either externally, predefined or
           else construct it on the fly.
        """
        device_name = device.class_name
        self.debug(f'ElectraOne getting preset for { device_name }.')
        preset_info = get_predefined_preset_info(device_name)
        if preset_info:
            self.debug('Predefined preset found')
            return preset_info
        else:
            self.debug('Constructing preset on the fly...')
            return construct_json_presetinfo( device_name, device.parameters )

    def cc_statusbyte(self):
        # status byte encodes MIDI_CHANNEL (-1!) in the least significant nibble
        CC_STATUS = 176
        return CC_STATUS + MIDI_CHANNEL - 1
    
    def send_midi_cc7(self,cc_no,value):
        """Send a 7bit MIDI CC
        """
        assert cc_no in range(128), f'CC no { cc_no } out of range'
        assert value in range(128), f'CC value { value } out of range'
        message = (self.cc_statusbyte(), cc_no, value )
        self.__c_instance.send_midi(message)
        
    def send_midi_cc14(self,cc_no,value):
        """Send a 14bit MIDI CC
        """        
        assert cc_no in range(128), f'CC no { cc_no } out of range'
        assert value in range(16384), f'CC value { value } out of range'
        lsb = value % 128
        msb = value // 128
        # a 14bit MIDI CC message is actually split into two messages:
        # one for the MSB and another for the LSB; the second uses cc_no+32
        message1 = (self.cc_statusbyte(), cc_no, msb)
        message2 = (self.cc_statusbyte(), 0x20 + cc_no, lsb)
        self.__c_instance.send_midi(message1)
        self.__c_instance.send_midi(message2)

    def send_value_as_cc(self,p,cc_info):
        """Send the value of a parameter using as a MIDI CC message
        """
        if is_cc14(cc_info):
            value = int(16383 * ((p.value - p.min) / (p.max - p.min)))
            self.send_midi_cc14(get_cc(cc_info),value)
        else:
            # for quantized parameters (always cc7) convert the index
            # value into the corresponding CC value
            if p.is_quantized:
                idx = int(p.value)
                value = cc_value_for_item_idx(idx,p.value_items)
            else:
                value = int(127 * ((p.value - p.min) / (p.max - p.min)))
            self.send_midi_cc7(get_cc(cc_info),value)

    def update_values(self):
        """Update the displayed values of the parameters in the
           (just uploaded) preset
        """
        self.debug('ElectraOne updating values.')
        if self._appointed_device != None:
            parameters = self._appointed_device.parameters
            for p in parameters:
                # the index of the parameter in the list as returned by the device is the default cc if no map specified for it
                cc_info = self._preset_info.get_cc_for_parameter(p.original_name)
                if cc_info:
                    self.send_value_as_cc(p,cc_info)
                
    def build_midi_map(self, midi_map_handle):
        """Build a MIDI map for the currently selected device    
        """
        self.debug('ElectraOne building map.')
        if self._appointed_device != None:
            parameters = self._appointed_device.parameters
            # TODO/FIXME: not clear how this is honoured in the Live.MidiMap.map_midi_cc call
            needs_takeover = True
            for p in parameters:                
                cc_info = self._preset_info.get_cc_for_parameter(p.original_name)
                if cc_info:
                    if is_cc14(cc_info):
                        map_mode = Live.MidiMap.MapMode.absolute_14_bit
                    else:
                        map_mode = Live.MidiMap.MapMode.absolute
                    cc_no = get_cc(cc_info)
                    # BUG: this call internally adds 1 to the specified MIDI channel!!!
                    self.debug(f'Mapping { p.original_name } to CC { cc_no } on MIDI channel { MIDI_CHANNEL }')
                    Live.MidiMap.map_midi_cc(midi_map_handle, p, MIDI_CHANNEL-1, cc_no, map_mode, not needs_takeover)

    def update_display(self):
        pass


    def dump_presetinfo(self,device,preset_info):
        """Dump the presetinfo: an ElectraOne JSON preset, and the MIDI CC map
        """
        device_name = device.class_name
        s = preset_info.get_preset()
        home = os.path.expanduser('~')
        path =  f'{ home }/{ LOCALDIR }/dumps'
        if not os.path.exists(path):
            path = home
        self.debug(f'dumping device: { device_name }.')
        fname = f'{ path }/{ device_name }.json'
        with open(fname,'w') as f:            
            f.write(s)
        fname = f'{ path }/{ device_name }.ccmap'
        with open(fname,'w') as f:
            comma = False
            f.write('{')
            for p in device.parameters:
                name = p.original_name
                cc = preset_info.get_cc_for_parameter(name)
                # also dump unassigned parameters (with value None)
                if comma:
                    f.write(',')
                comma = True
                f.write(f"'{ name }': { cc }\n")
            f.write('}')
                               
    def _set_appointed_device(self, device):
        self.debug(f'ElectraOne device appointed { device.class_name }')
        if device != self._appointed_device:
            self._appointed_device = device
            if device != None:
                self._preset_info = self.get_preset(device)
                if DUMP:
                    self.dump_presetinfo(device,self._preset_info)
                self.upload_preset(self._preset_info.get_preset())
                self.update_values()
                self.__c_instance.request_rebuild_midi_map()                

            
    def disconnect(self):
        """Called right before we get disconnected from Live
        """
        self._device_appointer.disconnect()                
