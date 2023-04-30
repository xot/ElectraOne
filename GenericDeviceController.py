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

class GenericDeviceController(ElectraOneBase):
    """Control devices (both selected ones and the ChannelEq devices
       in the mixer): build MIDI maps, refresh state
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
        # dictionary to keep track of string value updates
        self._values = { }

    def build_midi_map(self, midi_map_handle):
        """Build a MIDI map for the device    
           - midi_map_hanlde: MIDI map handle as passed to Ableton Live, to
               which MIDI mappings must be added.
        """
        # device may already be deleted while this controller still exists
        if not self._device:
            return
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
                self.debug(4,f'Mapping { p.original_name } ({p.name}) to CC { cc_no } on MIDI channel { midi_channel }')
                # Ableton internally numbers MIDI channels 0..15
                Live.MidiMap.map_midi_cc(midi_map_handle, p, midi_channel-1, cc_no, map_mode, not needs_takeover)
            else:
                self.debug(5,f'{ p.original_name } ({p.name}) not mapped.')

    def _refresh_parameter(self, p, ccinfo, force):
        """Update the displayed values for a single control on the E1. If force,
           MIDI CC is also updated, and possible string value update is always
           sent.
           (Assumes the device is visible!)
           - p: parameter; Live.DeviceParameter.DeviceParameter
           - ccinfo: information about the CC mapping; CCInfo
           - force: whether to always send the valuestr, or only if changed.
               Used to distinguish a state refresh from a value update; bool
        """
        # update MIDI value on the E1 if full refresh is requested
        if force:
            self.send_parameter_using_ccinfo(p,ccinfo)
        # update control with Ableton value string when mapped
        # as such, if forced or if the value changed since last update/refresh
        control_tuple = ccinfo.get_control_id()
        (control_id,value_id) = control_tuple
        if (control_id != UNMAPPED_ID) and USE_ABLETON_VALUES:
            pstr = str(p)
            # check whether sending the string value is really needed
            if force or \
               (control_tuple not in self._values) or \
               (self._values[control_tuple] != pstr):
                self._values[control_tuple] = pstr
                # translate any (significant) UNICODE characters in the string
                # to ASCII equivalents (E1 only understands ASCII)
                translation = { ord('♯') : ord('#') , ord('°') : ord('*') }
                pstr = pstr.translate(translation)
                self.debug(5,f'Value of {p.original_name} ({p.name}) (of parameter {id(p)}) updated to {pstr}.')
                self.send_value_update(control_id,value_id,pstr)
        
    def _refresh(self,full_refresh):
        """Refresh the state of the controls on the E1.

           If full_refresh, send MIDI CC updates for *all* parameters
           (brings MIDI info on E1 in sync with Ableton state) and update
           the string values for *all* controls whose string value must be
           determined by Ableton.

           If not full_refresh, only update the string values for controls
           whose value changed since the last _refresh
        
           (Assumes the device is visible!)
        
           - full_refresh: whether this is a full refresh: then MIDI CC values
             need to be refreshed too, and string value updates must always
             be sent; boolean
        """
        # device may already be deleted while this controller still exists
        if not self._device:
            return
        assert self._preset_info
        if full_refresh:
            self.debug(3,f'Full state refresh for device { self._device_name }')
        else:
            self.debug(3,f'Partial state refresh for device { self._device_name }')            
        # WARNING! Some devices have name clashes in their parameter list
        # so make sure only the first one is refreshed (to avoid continually
        # refreshing two parameters with the same name but different values;
        # the problem being that the CC map has only *one* entry for this para
        # meter name, so both parameters are mapped to the same control)
        # TODO: fix this in a more rigorous manner (seems to be hard...)
        refreshed = {}
        for p in self._device.parameters:
            if not p.original_name in refreshed:
                refreshed[p.original_name] = True
                ccinfo = self._preset_info.get_ccinfo_for_parameter(p)
                if ccinfo.is_mapped():
                    self._refresh_parameter(p,ccinfo,full_refresh)

    def refresh_state(self):
        """Update both the MIDI CC values and the displayed values for the
           device on the E1. (Assumes the device is visible!)
        """
        self._refresh(True)
        
    def update_display(self):
        """Called every 100 ms; used to update values for controls
           that want Ableton to set their value string. This way we do not
           need to register value change listeners for every parameter.
           (Assumes the device is visible!)
        """
        self._refresh(False)

