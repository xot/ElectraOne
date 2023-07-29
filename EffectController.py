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
from .Devices import get_predefined_preset_info
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
# equal None and an empty preset (teken froma  devicd with name "Empty")

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
        # (corresponds typically to the currently appointed device by Ableton)
        self._assigned_device = None
        # generic controller associated with assigned device
        # (only created when preset actually uploaded, so
        # _assigned_device != None while _assigned_device_controller = None
        # indicates that the device still needs to be uploaded)
        self._assigned_device_controller = None
        # set when device uploading is delayed (and upload most be done at
        # a later suitable time); initially true because the effect slot
        # initially does not have a preset uploaded (and may get selected
        # before any upload)
        self._assigned_device_upload_delayed = True
        # record if device is locked
        self._assigned_device_locked = False
        # count calls to update_display since last actual update
        self._update_ticks = 0
        # listen to device appointment changes (the actual changes are
        # created by DeviceAppointer or by other remote scripts handling device
        # appointments)
        self.song().add_appointed_device_listener(self._handle_appointed_device_change)
        self.debug(0,'EffectController loaded.')

    def _slot_is_visible(self):
        """Returh whether the effect preset slot is currently visible on the E1
        """
        visible = (CONTROL_MODE == CONTROL_BOTH) or \
             (ElectraOneBase.current_visible_slot == EFFECT_PRESET_SLOT)
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
            self._assigned_device_is_uploaded() and \
            self._slot_is_visible()
        
    def refresh_state(self):
        """Send the values of the controlled elements to the E1
           (to bring them in sync)
        """
        if self._assigned_device_is_visible():
            self.debug(2,'EffCont refreshing state.')
            self.effect_midi_burst_on()
            self._assigned_device_controller.refresh_state()
            self.effect_midi_burst_off()
            self.debug(2,'EffCont state refreshed.')
        else:
            self.debug(2,'EffCont not refreshing state (no effect selected or visible).')
            
    # --- initialise values ---
    
    def update_display(self):
        """Called every 100 ms; used to update values of controls whose
           string representation needs to be sent by Ableton
        """
        self.debug(6,'EffCont update display; checkig upload status.')
        # Upload the assigned device preset if 
        if not self._assigned_device_is_uploaded():
            self._upload_assigned_device_if_possible_and_needed()
        # Update the display after the refresh period
        if self._assigned_device_is_visible() and (self._update_ticks == 0):
            self.debug(6,'EffCont updating display.')
            self._assigned_device_controller.update_display()
            self.debug(6,'EffCont display updated.')
        self._update_ticks = (self._update_ticks + 1) % EFFECT_REFRESH_PERIOD 
        
    def disconnect(self):
        """Called right before we get disconnected from Live
        """
        self.remove_preset_from_slot(EFFECT_PRESET_SLOT)
        self.song().remove_appointed_device_listener(self._handle_appointed_device_change)

    # --- MIDI ---

    def build_midi_map(self, midi_map_handle):
        """Build a MIDI map for the currently selected device    
        """
        self.debug(2,'EffCont building effect MIDI map.')
        # Check that a device is assigned and that assigned_device still exists.
        # (When it gets deleted, the reference to it becomes None.)
        if self._assigned_device_controller:
            self._assigned_device_controller.build_midi_map(midi_map_handle)
        self.debug(2,'EffCont effect MIDI map built.')
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
            # TODO: this should be done in DeviceDumper
            # get the default lua script from the Empty device
            empty_preset_info = get_predefined_preset_info('Empty')
            preset_info._lua_script = empty_preset_info.get_lua_script()
            if DUMP:
                # determine path to store the dumps in (created if it doesnt exist)
                path = self._ensure_in_libdir('dumps')
                device_name = self.get_device_name(device)
                preset_info.dump(device,device_name,path,self.debug)
        # check preset integrity; any warnings will be reported in the log
        preset_info.validate(device, device_name, self.warning)
        return preset_info

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
           if necessary. (Warning: assumes E1 is ready)
        """
        self.debug(2,'Select Effect')
        if not self._assigned_device_is_uploaded():
            # also rebuilds midi map and causes state refresh
            self._upload_assigned_device()
        else:
            # will send a preset changed message in response which will trigger
            # a state refresh
            self.activate_preset_slot(EFFECT_PRESET_SLOT)
            
    def _upload_assigned_device(self):
        """Upload the currently assigned device to the effect preset slot on
           the E1 and create a device controller for it.
        """
        device = self._assigned_device
        # TODO: we get the (complex) preset from DEVICES.py even if
        # it is already preloaded on the E1; luckily we do not construct
        # the preset on the fly unneccessarily (as it is then  also not
        # preloaded); we do validate though...
        if device:
            device_name = self.get_device_name(device)
            self.debug(2,f'Uploading device { device_name }')
            preset_info = self._get_preset_info(device)
            cc_map = preset_info.get_cc_map()
            self._assigned_device_controller = GenericDeviceController(self._c_instance, device, cc_map)
        else:
            device_name = 'Empty'
            self.debug(2,'Uploading empty device')
            # 'Empty' guaranteed to exist
            preset_info = get_predefined_preset_info(device_name)
        preset = preset_info.get_preset()
        script = preset_info.get_lua_script() 
        # upload preset: will also request midi map (which will also refresh state)
        self.upload_preset(EFFECT_PRESET_SLOT,device_name,preset,script)
        self._assigned_device_upload_delayed = False
        # if this upload fails, ElectraOneBase.preset_upload_successful will be
        # false; then update_display will try to upload again every 100ms (when
        # the E1 is ready, of course).
        
    def _upload_assigned_device_if_possible_and_needed(self):
        """Upload the currently assigned device to the effect preset slot on
           the E1 if needed (and possible) and create a device controller for it.
        """
        if self.is_ready() and \
           (SWITCH_TO_EFFECT_IMMEDIATELY or self._slot_is_visible()):
            self._upload_assigned_device()
        else:
            # If this happens, update_display will regularly check whether
            # device currently assigned device still needs uploading.
            self.debug(2,'Device upload delayed.')
            self._assigned_device_upload_delayed = True
        
    def _assign_device(self, device):
        """Assign the device to the E1 effect preset. Upload it immediately if
           possible and necessary.
           - device: device to assign; Live.Device.Device
        """
        # If device == None then no device appointed
        if device != None:
            device_name = self.get_device_name(device)
            self.debug(2,f'Assignment of device { device_name } detected')
            # Note: even if this is not the case, Ableton rebuilds the midi map
            # and initiates a state refresh. As hot-swapping a device
            # apparently triggers a device appointment of the same device,
            # this (luckily) triggers the required state refresh
            if device != self._assigned_device:
                self.debug(2,f'Assigning new device { device_name }')
                self._assigned_device = device
                self._assigned_device_controller = None
                # upload preset: will also request midi map (which will also refresh state)                
                self._upload_assigned_device_if_possible_and_needed()
        else:
            # assigns the empty device (needed to install some LUA script
            # when comamnds need to be forwarded to a mixer when
            # in CONTROL_BOTH_MODE 
            self._assigned_device = None
            self._assigned_device_controller = None
            self.debug(2,'Assigning an empty device.')
            # upload preset: will also request midi map (which will also refresh state)
            self._upload_assigned_device_if_possible_and_needed()
            
    def _handle_appointed_device_change(self):
        """Handle an appointed device change: change the currently assigned
           device unless it is locked.
        """
        device = self.song().appointed_device
        if not self._assigned_device_locked:
            self._assign_device(device)
        else:
            self.debug(2,'Device appointment ignored because device locked.')
            
