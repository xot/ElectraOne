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


# Default LUA script to send along an effect preset. Programs the PATCH REQUEST
# button to send a special SysEx message (0xF0 0x00 0x21 0x45 0x7E 0x7E 0x00 0xF7)
# received by ElectraOne to swap the visible preset. As complex presets may have
# more than one device defined (an patch.onRequest sends a message out for
# every device), we use device.id to diversify the outgoing message.
# (Effect presets always have device.id = 1 as the first device)
#
# Also contains formatter functions used by presets generated on the fly
DEFAULT_LUASCRIPT = """
function patch.onRequest (device)
  print ("Patch Request pressed");
  midi.sendSysex(PORT_1, {0x00, 0x21, 0x45, 0x7E, 0x7E, device.id - 1})
end

function formatPan (valueObject, value)
  if value < 0 
    then return (string.format("%iL", -value))
    else return (string.format("%iR", value))
  end
end
"""

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
def update_values_for_device(device, preset_info, sender_object):
    # Internal function to update the displayed values for a device, also
    # used by TrackController and MasterController too to map the
    # ChannelEq device. Uses preset_info to get the CCInfo for device
    # parameters.
    if device and preset_info:
        for p in device.parameters:
            ccinfo = preset_info.get_ccinfo_for_parameter(p)
            if ccinfo.is_mapped():
                sender_object.send_parameter_using_ccinfo(p,ccinfo)

                
class EffectController(ElectraOneBase):
    """Remote control script for the Electra One
    """

    def __init__(self, c_instance):
        ElectraOneBase.__init__(self, c_instance)
        self._assigned_device = None
        self._assigned_device_locked = False
        self._preset_info = None
        # register a device appointer;  _set_appointed_device will be called when appointed device changed
        # see _Generic/util.py
        #
        # Note (2022-05-21): this appears to IMMEDIATELY call self._set_appointed_device
        self._device_appointer = DeviceAppointer(song=self.song(), appointed_device_setter=self._set_appointed_device)
        self.debug(0,'EffectController loaded.')

    def refresh_state(self):
        # send the values of the controlled elements to the E1 (to bring them in sync)
        if ElectraOneBase.current_visible_slot == EFFECT_PRESET_SLOT:
            self.debug(2,'EffCont refreshing state.')
            update_values_for_device(self._assigned_device,self._preset_info,self)
        else:
            self.debug(2,'EffCont not refreshing state (effect not visible).')
            
    # --- initialise values ---
    
    def update_display(self):
        """ Called every 100 ms; used to call update_values with a delay
        """
        pass
    
    def disconnect(self):
        """Called right before we get disconnected from Live
        """
        self._remove_preset_from_slot(EFFECT_PRESET_SLOT)
        self._device_appointer.disconnect()                

    # --- MIDI ---

    def build_midi_map(self, midi_map_handle):
        """Build a MIDI map for the currently selected device    
        """
        self.debug(1,'EffCont building effect MIDI map.')
        build_midi_map_for_device(midi_map_handle, self._assigned_device, self._preset_info, self.debug)
        self.refresh_state()
        
    # === Others ===

    def _get_preset(self,device):
        """Get the preset for the specified device, either externally,
           predefined or else construct it on the fly.
        """
        device_name = get_device_name(device)
        self.debug(2,f'Getting preset for { device_name }.')
        preset_info = get_predefined_preset_info(device_name)
        if preset_info:
            self.debug(2,'Predefined preset found')
        else:
            self.debug(2,'Constructing preset on the fly...')
            dumper = ElectraOneDumper(self.get_c_instance(), device_name, device.parameters)
            preset_info = dumper.get_preset()
        # check preset integrity; ny errors will be reported in the log
        error = preset_info.validate()
        if error:
            self.debug(2,f'Issues in preset found: {error}.')
        return preset_info
    
    # --- handling presets  ----
    
    def _dump_presetinfo(self,device,preset_info):
        """Dump the presetinfo: an ElectraOne JSON preset, and the MIDI CC map
        """
        device_name = get_device_name(device)
        path = self._find_libdir('/dumps')
        # dump the preset JSON string
        fname = f'{ path }/{ device_name }.epr'
        self.debug(2,f'dumping device: { device_name } in { fname }.')
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

    # --- handle device selection ---
    
    def lock_to_device(self, device):
        if device:
            self._assigned_device_locked = True
            self._assign_device(device)
            
    def unlock_from_device(self, device):
        if device and device == self._assigned_device:
            self._assigned_device_locked = False
            self._assign_device(self.song().appointed_device)


    def _assign_device(self, device):
        if device != None:
            device_name = get_device_name(device)
            self.debug(1,f'Assigning device { device_name }')
            if device != self._assigned_device:
                self._assigned_device = device
                self._preset_info = self._get_preset(device)
                if DUMP:
                    self._dump_presetinfo(device,self._preset_info)
                preset = self._preset_info.get_preset()
                # upload preset: will also request midi map (which will also refresh state)
                self.upload_preset(EFFECT_PRESET_SLOT,preset,DEFAULT_LUASCRIPT)
            else:
                self.debug(1,'Device already assigned.')
        else:
            self.debug(1,'Assigning an empty device.')
                
    def _set_appointed_device(self, device):
        if (not ElectraOneBase.preset_uploading) and (not self._assigned_device_locked):
            self._assign_device(device)
        
