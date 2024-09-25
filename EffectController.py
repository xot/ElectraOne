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

# Local imports
from .config import *
from .CCInfo import CCInfo
from .PresetInfo import PresetInfo
from .ElectraOneBase import ElectraOneBase 
from .ElectraOneDumper import ElectraOneDumper
from .GenericDeviceController import GenericDeviceController

# Note: the EffectController creates an instance of a GenericDeviceController
# to manage the currently assigned device. If uploading is delayed,
# self._assigned_device already points to the newly selected device, but
# self._assigned_device_controller is still None and 
# self._assigned_device_upload_delayed = True.  Note that device
# deletion triggers device selection, so
# self._assigned_device_controller is updated (and no longer points to
# the now deleted device). If no device is assigned, then self._assigned_device
# equal None 

class EffectController(ElectraOneBase):
    """Control the currently selected device.
    """

    def __init__(self, c_instance, devices):
        """Initialise an effect controller.
           (Typically called only once, after loading a song.)
           - c_instance: Live interface object (see __init.py__)
           - devices: info about predefined devices and default LUA script; Devices
        """
        ElectraOneBase.__init__(self, c_instance)
        self._devices = devices
        # referrence to the currently assigned device
        # (corresponds typically to the currently appointed device by Ableton)
        self._assigned_device = None
        # generic controller associated with assigned device
        # (only created for preset when actually uploaded)
        self._assigned_device_controller = None
        # set when device uploading is delayed (and upload most be done at
        # a later suitable time); initially true because the effect slot
        # initially does not have a preset uploaded (and may get selected
        # before any upload)
        self._assigned_device_upload_delayed = True
        # record if device is locked
        self._assigned_device_locked = False
        # listen to device appointment changes (the actual changes are
        # created by DeviceAppointer or by other remote scripts handling device
        # appointments)
        self.song().add_appointed_device_listener(self._handle_appointed_device_change)
        self.debug(0,'EffectController loaded.')

    # --- functions to check state ---

    def _slot_is_visible(self):
        """Returh whether the effect preset slot is currently visible on the E1
        """
        visible = (ElectraOneBase.current_visible_slot == EFFECT_PRESET_SLOT)
        self.debug(6,f'Effect controller is visible: {visible}')
        return visible
        
    def _assigned_device_is_uploaded(self):
        """Test whether the assigned device is actually uploaded
           - result: whether assigned device is uploaded; bool
        """
        flag = (not self._assigned_device_upload_delayed) and \
            ElectraOneBase.preset_upload_successful 
        self.debug(6,f'Assigned device is uploaded: { flag }')
        return flag
    
    def _assigned_device_is_visible(self):
        """Test whether the assigned device is actually uploaded and currently
           visible on the E1 (and that it is not an empty device)
           - result: whether assigned device is visble; bool
        """
        return self._assigned_device and \
            self._assigned_device_controller and \
            self._assigned_device_is_uploaded() and \
            self._slot_is_visible()
        
    # --- refresh / update ---
    
    def refresh_state(self):
        """Send the values of the controlled elements to the E1
           (to bring them in sync)
        """
        if self._assigned_device_is_visible():
            self.debug(1,'EffCont refreshing state.')
            self.midi_burst_on()
            self._assigned_device_controller.refresh_state()
            self.midi_burst_off()
            self.debug(1,'EffCont state refreshed.')
        else:
            self.debug(1,'EffCont not refreshing state (no effect selected or visible).')
            
    def update_display(self,tick):
        """Called every 100 ms; used to update values of controls whose
           string representation needs to be sent by Ableton.
           Also used to upload a pending preset.
           - tick: number of 100ms ticks since start (mod 1000)
        """
        self.debug(6,'EffCont update display; checkig upload status.')
        # Upload the assigned device preset if possible and needed
        if not self._assigned_device_is_uploaded():
            if self.is_ready() and self._slot_is_visible():
                self.debug(1,'Delayed device upload detected.')
                self._upload_device(self._assigned_device)
                self._assigned_device_upload_delayed = False
        # Update the display after the refresh period
        if self._assigned_device_is_visible() and ((tick % EFFECT_REFRESH_PERIOD) == 0):
            self.debug(6,'EffCont updating display.')
            self._assigned_device_controller.update_display()
            self.debug(6,'EffCont display updated.')

    def disconnect(self):
        """Called right before we get disconnected from Live
        """
        self.debug(1,'EffCont disconnecting.')
        self.remove_preset_from_slot(EFFECT_PRESET_SLOT)
        self.song().remove_appointed_device_listener(self._handle_appointed_device_change)

    def select(self):
        """Select the effect preset and upload the currently assigned device
           if necessary. (Warning: assumes E1 is ready)
        """
        self.debug(1,'Select Effect')
        if not self._assigned_device_is_uploaded():
            # also rebuilds midi map and causes state refresh
            self._upload_device(self._assigned_device)
            self._assigned_device_upload_delayed = False
        else:
            # will send a preset changed message in response which will trigger
            # a state refresh
            self.activate_preset_slot(EFFECT_PRESET_SLOT)
            
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
        
    # === Others ===

    def _get_preset_info(self, device):
        """Get the preset info for the specified device, either predefined or
           else construct it on the fly.
           If DUMP=True, construct the preset on the fly, and dump it.
           - device: device to get preset for; Live.Device.Device (!= None)
           - return (versioned_device_name,preset_info)
           where versioned_device_name is the version specific name of the
           device (e.g Echo.12.0) when a Live specific version preset is found
        """
        device_name = self.get_device_name(device)
        self.debug(3,f'Getting preset for { device_name }.')
        (versioned_device_name,preset_info) = self._devices.get_predefined_preset_info(device_name)
        if preset_info:
            self.debug(3,f'Predefined preset {versioned_device_name} found')
        if (not preset_info or DUMP):
            # construct a preset on the fly if none found or DUMP requested
            self.debug(3,'Constructing preset on the fly...')
            dumper = ElectraOneDumper(self.get_c_instance(), device)
            dump_preset_info = dumper.get_preset_info()
        if DUMP:
            dump_preset_info.dump(device, device_name, self.dumppath(), self.debug)
        if not preset_info:
            versioned_device_name = device_name
            preset_info = dump_preset_info
        # check preset integrity; any warnings will be reported in the log
        preset_info.validate(device, device_name, self.warning)
        return (versioned_device_name,preset_info)

    # --- handle device selection ---
    
    def lock_to_device(self, device):
        if device:
            self._assigned_device_locked = True
            self._assign_device(device)
            
    def unlock_from_device(self, device):
        if device and device == self._assigned_device:
            self._assigned_device_locked = False
            self._assign_device(self.song().appointed_device)

    def _upload_device(self,device):
        """Upload the currently assigned device to the effect preset slot on
           the E1 and create a device controller for it.
           - device: device to upload; Live.Device.Device
        """
        # upload an empty preset if None (eg when track deleted and no device appointed)
        if device:
            (versioned_device_name,preset_info) = self._get_preset_info(device)
            self.debug(1,f'Uploading device { versioned_device_name }.')
            cc_map = preset_info.get_cc_map()
            self._assigned_device_controller = GenericDeviceController(self._c_instance, device, cc_map)
            preset = preset_info.get_preset()
            # get the default lua script and append the preset specific lua script
            script = self._devices.get_default_lua_script()
            script += preset_info.get_lua_script()
        else:
            versioned_device_name = 'Empty'
            self._assigned_device_controller = None
            preset = '{"version":2,"name":"Empty","projectId":"l49eJksr7QcPZuqbF2rv","pages":[],"groups":[],"devices":[],"overlays":[],"controls":[]}'
            script = self._devices.get_default_lua_script()
        # upload preset: will also request midi map (which will also refresh state)
        # use versioned_device_name to (try to) look up correct preloaded preset on the E1
        self.upload_preset(EFFECT_PRESET_SLOT,versioned_device_name,preset,script)
        # if this upload fails, ElectraOneBase.preset_upload_successful will be
        # false; then update_display will try to upload again every 100ms (when
        # the E1 is ready, of course).
        
    def _assign_device(self, device):
        """Assign the device to the E1 effect preset. Upload it immediately if
           possible and needed.
           - device: device to assign; Live.Device.Device
        """
        self._assigned_device = device
        self._assigned_device_controller = None
        # upload preset if possible and needed: will also request midi map
        # (which will also refresh state)
        if self.is_ready() and \
           (SWITCH_TO_EFFECT_IMMEDIATELY or self._slot_is_visible()):
            self._upload_device(device)
            self._assigned_device_upload_delayed = False
        else:
            # If this happens, update_display will regularly check whether
            # device currently assigned device still needs uploading.
            self.debug(1,'Device upload delayed.')
            self._assigned_device_upload_delayed = True

    def _handle_appointed_device_change(self):
        """Handle an appointed device change: change the currently assigned
           device unless it is locked.
        """
        device = self.song().appointed_device
        device_name = self.get_device_name(device)
        if not self._assigned_device_locked:
            # Note: even if condition below is not true, Ableton rebuilds the
            # midi map and initiates a state refresh. As hot-swapping a device
            # apparently triggers a device appointment of the same device,
            # this (luckily) triggers the required state refresh
            if device != self._assigned_device:
                self.debug(0,f'Assignment of device {device_name} detected.')
                self._assign_device(device)
            else:
                self.debug(0,f'Appointed device {device_name} already assigned.')
        else:
            self.debug(0,f'Device appointment of {device_name} ignored because device locked.')
            
