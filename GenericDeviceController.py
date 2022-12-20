# GenericDevoceController
# - Control devices (both selected ones and the ChannelEq devices in the mixer)
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
import Live

# Local imports
from .config import USE_ABLETON_VALUES
from .CCInfo import CCInfo, UNMAPPED_ID
from .PresetInfo import PresetInfo
from .ElectraOneBase import ElectraOneBase 

# --- helper functions

class GenericDeviceController(ElectraOneBase):
    """Control devices (both selected ones and the ChannelEq devices
       in the mixer): build MIDI maps, add value listeners, refresh state
    """

    def __init__(self, c_instance, device, preset_info):
        """Create a new device controller for the device and the
           associated preset information. It is assumed the preset is already
           present on the E1 or will be uploaded there shortly
           (with controls matching the description in PresetInfo)
           - c_instance: Live interface object (see __init.py__)
           - device: the device; Live.Device.Device
           - preset_info: the preset information; PresetInfo
        """
        ElectraOneBase.__init__(self, c_instance)
        self._device = device
        self._device_name = self.get_device_name(self._device)
        self._preset_info = preset_info
        # keep track of values that changed since last refresh_state / update_dsiplay
        self._values = { }

    def build_midi_map(self, midi_map_handle):
        """Build a MIDI map for the device    
           - midi_map_hanlde: MIDI map handle as passed to Ableton Live, to
               which MIDI mappings must be added.
        """
        assert self._device
        assert self._preset_info
        self.debug(3,f'Building MIDI map for device { self._device_name }')
        parameters = self._device.parameters
        # TODO/FIXME: not clear how this is honoured in the Live.MidiMap.map_midi_cc call
        needs_takeover = True
        for p in parameters:                
            ccinfo = self._preset_info.get_ccinfo_for_parameter(p)
            if ccinfo.is_mapped():
                if ccinfo.is_cc14():
                    map_mode = Live.MidiMap.MapMode.absolute_14_bit
                else:
                    map_mode = Live.MidiMap.MapMode.absolute
                cc_no = ccinfo.get_cc_no()
                midi_channel = ccinfo.get_midi_channel()
                # BUG: this call internally adds 1 to the specified MIDI channel!!!
                self.debug(4,f'Mapping { p.original_name } to CC { cc_no } on MIDI channel { midi_channel }')
                Live.MidiMap.map_midi_cc(midi_map_handle, p, midi_channel-1, cc_no, map_mode, not needs_takeover)

    def refresh_state(self):
        """Update both the MIDI CC values and the displayed values for the device
           on the E1. (Assumes the device is visible!)
        """
        # TODO Visibility matters for the displayed values (probably)
        # and whether preset upload finished
        assert self._device
        assert self._preset_info
        for p in self._device.parameters:
            ccinfo = self._preset_info.get_ccinfo_for_parameter(p)
            if ccinfo.is_mapped():
                # update MIDI value on the E1
                self.send_parameter_using_ccinfo(p,ccinfo)
                control_id = ccinfo.get_control_id()
                # update controls wiht Ableton value string when required
                if (control_id != UNMAPPED_ID) and USE_ABLETON_VALUES:
                    pstr = str(p)
                    self._values[control_id] = pstr
                    self.debug(5,f'Value of {p.original_name} refreshed to {pstr}.')
                    # ONLY SEND VALUE WHEN DEVICE IS VISIBLE!
                    self.send_value_update(control_id, pstr)

    def update_display(self):
        """ Called every 100 ms; used to update values for controls
            that want Ableton to set their value string
        """
        for p in self._device.parameters:
            ccinfo = self._preset_info.get_ccinfo_for_parameter(p)
            if ccinfo.is_mapped():
                control_id = ccinfo.get_control_id()
                if (control_id != UNMAPPED_ID) and USE_ABLETON_VALUES:
                    pstr = str(p)
                    # check if control value string changed since last refresh/update
                    if (control_id in self._values) and \
                       (self._values[control_id] != pstr):
                        self._values[control_id] = pstr
                        self.debug(5,f'Value of {p.original_name} updated to {pstr}.')
                        # ONLY SEND VALUE WHEN DEVICE IS VISIBLE!
                        self.send_value_update(control_id, pstr)

    def disconnect(self):
        """Disconnect the device; remove all listeners.
        """
        pass

    # --- Listeners
    
    def add_listeners(self):
        """Add value listeners for all (slider) parameters of the device.
        """
        pass

    def remove_listeners(self):
        """Remove all value listeners added.
        """
        pass
