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

# Ableton Live imports (TODO: remove, obsolote)
#from _Generic.util import DeviceAppointer

# Local imports
from .config import *
from .CCInfo import CCInfo
from .PresetInfo import PresetInfo
from .Devices import get_predefined_preset_info
from .ElectraOneBase import ElectraOneBase 
from .ElectraOneDumper import ElectraOneDumper
from .GenericDeviceController import GenericDeviceController

# Default LUA script to send along an effect preset. Programs the PATCH REQUEST
# button to send a special SysEx message (0xF0 0x00 0x21 0x45 0x7E 0x7E 0xF7)
# received by ElectraOne to swap the visible preset. As complex presets may have
# more than one device defined (an patch.onRequest sends a message out for
# every device), we use device.id to diversify the outgoing message.
# (Effect presets always have device.id = 1 as the first device)
#
# Also contains formatter functions used by presets generated on the fly
#
# TODO: remove patch.onRequest code when DISABLE_MIXER
DEFAULT_LUASCRIPT = """
info.setText("by www.xot.nl")

function patch.onRequest (device)
  print ("Patch Request pressed");
  if device.id == 1
    then midi.sendSysex(PORT_1, {0x00, 0x21, 0x45, 0x7E, 0x7E})
  end
end

values =  { }

function defaultFormatter(valueObject, value)
    local control = valueObject:getControl()
    local id = control:getId()
    local str = values[id]
    if str == nil then 
        return("")
    else
        return(str)
    end
end

function svu(id,valuestring)
    values[id] = valuestring
    local control = controls.get(id)
    if control:isVisible() then    
       control:setVisible(false)
       control:setVisible(true)
    end
end

function formatFloat (valueObject, value)
  return (string.format("%.2f",value/100))
end

function formatLargeFloat (valueObject, value)
  return (string.format("%.1f",value/10))
end

function formatdB (valueObject, value)
  return (string.format("%.1f dB",value/10))
end

function formatFreq (valueObject, value)
  return (string.format("%.1f Hz",value/10))
end

function formatPan (valueObject, value)
  if value < 0 then
    return (string.format("%iL", -value))
  elseif value == 0 then
    return "C"
  else
    return (string.format("%iR", value))
  end
end

function formatPercent (valueObject, value)
  return (string.format("%.1f %%",value/10))
end

function formatIntPercent (valueObject, value)
  return (string.format("%.0f %%",value/10))
end

function formatDegree (valueObject, value)
  return (string.format("%i *",value))
end

function formatSemitone (valueObject, value)
  return (string.format("%i st",value))
end

function formatDetune (valueObject, value)
  return (string.format("%i ct",value))
end

"""

# Note: the EffectController creates an instance of a GenericDeviceController
# to manage the currently assigned device. If uploading is delayed,
# self._assigned_device already points to the newly selected device, but
# self._assigned_device_controller is still None. Note that device
# deletion triggers device selection, so
# self._assigned_device_controller is updated (and no longer points to
# the now deleted device).

class EffectController(ElectraOneBase):
    """Control the currently selected device.
    """

    def __init__(self, c_instance):
        """Initialise an effect controller.
           (Typically called only once, after loading a song.)
           - c_instance: Live interface object (see __init.py__)
        """
        ElectraOneBase.__init__(self, c_instance)
        # referrence to the currently assigned device
        # (corresponds typically to the currently appointed device by Ableton
        self._assigned_device = None
        # generic controller associated with assigned device
        # (only created when preset actually uploaded, so
        # _assigned_device != None while _assigned_device_controller = None
        # indicates that the device still needs to be uploaded)
        self._assigned_device_controller = None
        self._assigned_device_locked = False
        # count calls to update_display since last actual update
        self._update_ticks = 0
        # listen to device appointment changes (the actual changes are
        # created by DeviceAppointer or by other remote scripts handling device
        # appointments)
        self.song().add_appointed_device_listener(self._handle_appointed_device_change)
        self.debug(0,'EffectController loaded.')

    def _assigned_device_is_uploaded(self):
        """Test whether the assigned device is actually uploaded
           - result: whether assigned device is uploaded; bool
        """
        flag = self._assigned_device and self._assigned_device_controller
        self.debug(5,f'Assigned device is uploaded: { flag }')
        return flag
    
    def _assigned_device_needs_uploading(self):
        """Test whether the assigned device still needs to be uploaded
           - result: whether assigned device needs to be uploaded; bool
        """
        flag = self._assigned_device and (self._assigned_device_controller == None)
        self.debug(5,f'Assigned device needs uploading: { flag }')
        return flag
    
    def _assigned_device_is_visible(self):
        """Test whether the assigned device is actually uploaded and currently
           selected.
           - result: whether assigned device is visble; bool
        """
        return self._assigned_device_is_uploaded() and \
              (ElectraOneBase.current_visible_slot == EFFECT_PRESET_SLOT)
        
    def refresh_state(self):
        """Send the values of the controlled elements to the E1
           (to bring them in sync)
        """
        if self._assigned_device_is_visible():
            self.debug(1,'EffCont refreshing state.')
            self._midi_burst_on()
            self._assigned_device_controller.refresh_state()
            self._midi_burst_off()
            self.debug(1,'EffCont state refreshed.')
        else:
            self.debug(1,'EffCont not refreshing state (no effect selected or visible).')
            
    # --- initialise values ---
    
    def update_display(self):
        """Called every 100 ms; used to update values of controls whose
           string representation needs to be sent by Ableton
        """
        # Upload the assigned device preset if 
        if self._assigned_device_needs_uploading():
            self._upload_assigned_device_if_possible_and_needed()
        # Update the display after the refresh period
        if self._assigned_device_is_visible() and (self._update_ticks == 0):
            self._assigned_device_controller.update_display()
        self._update_ticks = (self._update_ticks + 1) % EFFECT_REFRESH_PERIOD 
        
    def disconnect(self):
        """Called right before we get disconnected from Live
        """
        self._remove_preset_from_slot(EFFECT_PRESET_SLOT)
        self.song().remove_appointed_device_listener(self._handle_appointed_device_change)

    # --- MIDI ---

    def build_midi_map(self, midi_map_handle):
        """Build a MIDI map for the currently selected device    
        """
        self.debug(1,'EffCont building effect MIDI map.')
        # Check that a device is assigned and that assigned_device still exists.
        # (When it gets deleted, the reference to it becomes None.)
        if self._assigned_device_controller:
            self._assigned_device_controller.build_midi_map(midi_map_handle)
        self.debug(1,'EffCont effect MIDI map built.')
        self.refresh_state()
        
    # === Others ===

    def _get_preset_info(self, device):
        """Get the preset info for the specified device, either externally,
           predefined or else construct it on the fly.
        """
        device_name = self.get_device_name(device)
        self.debug(2,f'Getting preset for { device_name }.')
        preset_info = get_predefined_preset_info(device_name)
        if preset_info:
            self.debug(2,'Predefined preset found')
        else:
            self.debug(2,'Constructing preset on the fly...')
            dumper = ElectraOneDumper(self.get_c_instance(), device)
            preset_info = dumper.get_preset()
            if DUMP:
                self._dump_presetinfo(device,preset_info)
        # check preset integrity; any errors will be reported in the log
        error = preset_info.validate()
        if error:
            self.debug(2,f'Issues in preset found: {error}.')
        return preset_info
    
    # --- handling presets  ----
    
    def _dump_presetinfo(self, device, preset_info):
        """Dump the presetinfo: an ElectraOne JSON preset, and the MIDI CC map
        """
        device_name = self.get_device_name(device)
        # determine path to store the dumps in (created if it doesnt exist)
        path = self._ensure_in_libdir('dumps')
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

    def select(self):
        """Select the effect preset and upload the currently assigned device
           if necessary.
        """
        if self._assigned_device_needs_uploading():
            # also selects
            self._upload_assigned_device()
        else:
            self._select_preset_slot(EFFECT_PRESET_SLOT)
            
    def _upload_assigned_device(self):
        """Upload the currently assigned device to the effect preset slot on
           the E1 and create a device controller for it.
        """
        device = self._assigned_device
        device_name = self.get_device_name(device)
        self.debug(1,f'Uploading device { device_name }')
        preset_info = self._get_preset_info(device)
        self._assigned_device_controller = GenericDeviceController(self._c_instance, device, preset_info)
        preset = preset_info.get_preset()
        lua_script = preset_info.get_lua_script()
        # upload preset: will also request midi map (which will also refresh state)
        self.upload_preset(EFFECT_PRESET_SLOT,preset,DEFAULT_LUASCRIPT + lua_script)

    def _upload_assigned_device_if_possible_and_needed(self):
        """Upload the currently assigned device to the effect preset slot on
           the E1 if needed (and possible) and create a device controller for it.
        """
        if self.is_ready() and (SWITCH_TO_EFFECT_IMMEDIATELY or \
           (ElectraOneBase.current_visible_slot == EFFECT_PRESET_SLOT)):
            self._upload_assigned_device()
        else:
            self.debug(1,'Device upload delayed.')
        
    
    def _assign_device(self, device):
        """Assign the device to the E1 effect preset. Upload it immediately if
           possible and necessary.
           - device: device to assign; Live.Device.Device
        """
        if device != None:
            device_name = self.get_device_name(device)
            self.debug(1,f'Assigning device { device_name }')
            # Note: even if this is not the case, Ableton rebuilds the midi map
            # and initiates a state refresh. As hot-swapping a device
            # apparently triggers a device appointment of the same device,
            # this (luckily) triggers the required state refresh
            if device != self._assigned_device:
                self._assigned_device = device
                self._assigned_device_controller = None
                self._upload_assigned_device_if_possible_and_needed()
        else:
            # this does not happen (unfortunately)
            self._assigned_device = None
            self._assigned_device_controller = None
            self.debug(1,'Assigning an empty device.')
            # TODO: remove device preset from E1
            self._remove_preset_from_slot(EFFECT_PRESET_SLOT)

    def _handle_appointed_device_change(self):
        """Handle an appointed device change: change the currently assigned
           device unless it is locked.
        """
        device = self.song().appointed_device
        if not self._assigned_device_locked:
            self._assign_device(device)
        else:
            self.debug(1,'Device appointment ignored because device locked.')
            
