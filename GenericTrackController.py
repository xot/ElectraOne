# GenericTrackController
# - Most of the functionality to control a audio/midi track, return track or
#   the master track.
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
from .config import *
from .CCInfo import CCMap, CCInfo
from .ElectraOneBase import ElectraOneBase
from .GenericDeviceController import GenericDeviceController
from .PropertyControllers import PropertyControllers

class GenericTrackController(ElectraOneBase):
    """Generic class to manage a track. To be subclassed to handle normal
       tracks, return tracks and the master track.
    """
    
    def __init__(self, c_instance):
        """Initialise a generic track controller.
           - c_instance: Live interface object (see __init.py__)
        """
        ElectraOneBase.__init__(self, c_instance)
        # actual initialisations to be provided by derived classes;
        # None indicates a fearture is not present.
        self._track = None
        # device selector index of this track
        # 0..NO_OF_TRACKS-1 for tracks, NO_OF_TRACKS..NO_OF_TRACKS+MAX_NO_OF_SENDS-1 for sends
        # NO_OF_TRACKS+MAX_NO_OF_SENDS for master
        self._devsel_idx = None
        # current list of selectable devices, favourites first
        self._devices = None
        # session control first clip row  (only for tracks)
        self._first_row_index = None
        # EQ device info
        self._eq_device = None
        self._eq_device_controller = None # if None not present (ie all returns)
        # midi info
        self._midichannel = None
        # slider CC numbers
        self._base_pan_cc = None
        self._base_volume_cc = None
        self._base_cue_volume_cc = None  # if None, not present (ie all non master tracks)
        self._base_sends_cc = None # if None, not present (ie all non audio/midi tracks)
        # button CC numbers
        self._base_mute_cc = None # if None, not present (i.e. master track)
        self._base_arm_cc = None # if None, not present (i.e. groups and returns)
        self._base_solo_cue_cc = None # if None, not present (i.e. all non audio/midi tracks)
        # device selection CC numbers
        self._base_device_selection_cc = None # if None, not present.
        # set up property controllers for the buttons
        # (actual controllers set up in add_listeners)
        self._property_controllers = PropertyControllers(c_instance)
        self.debug(0,'GenericTrackController loaded.')

        
    # --- helper functions ---

    def _my_cc(self,base_cc):
        """Return the actual MIDI CC number for this instance of a control,
           given the base MIDI CC number for the control. To be defined by
           the subclass.
           - base_cc: base MIDI CC number; int
           - result: actual MIDI CC number; int
        """
        pass

    def _my_channel_eq(self, eq_device_name):
        """ Get a reference to the Channel EQ device (or similar; determined
            by the value of eq_device_name) on this track, if present.
            None if not found.
            - eq_device_name: ; str
            - result: reference to the device ; Live.Device.Device 
        """
        self.debug(4,f'Looking for equaliser device with name {eq_device_name}')
        devices = self._track.devices
        for d in reversed(devices):
            if d.class_name == eq_device_name:
                self.debug(4,'Found an equaliser device to be controlled.')
                return d
        return None

    def _my_channel_eq_cc_map(self, eq_cc_map):
        """Return the CC map associated with the Channel EQ Device on this
           track, filling in the correct MIDI CC numbers for this
           particular instance of the device using eq_cc_map as source
           for the base values.
           - eq_cc_map: ; dict of CCInfo
           - result: CC map; CCMap
        """
        cc_map = CCMap({})
        for p in eq_cc_map:
            (channel_id, channel, is_cc14, cc_no) = eq_cc_map[p]
            # adjust the CC
            cc_map.map_name(p, CCInfo((channel_id, channel, is_cc14, self._my_cc(cc_no))))
        return cc_map
    
    def add_eq_device(self, eq_device_name, eq_cc_map):
        """Add a equaliser device to be managed by the mixer preset.
           - eq_device_name: class name of the equaliser device, used to locate
             the device on the track; str
           - eq_cc_map: information about the CC mapping (like in Devices.py); dict of CCInfo
        """
        # initialise the name and ccmap to use for this type of track; see
        # _handle_device_change
        self._eq_device_name = eq_device_name
        self._eq_cc_map = eq_cc_map
        # find the equaliser device on the track
        self._eq_device = self._my_channel_eq(eq_device_name)
        if self._eq_device:
            cc_map = self._my_channel_eq_cc_map(eq_cc_map)
            self._eq_device_controller = GenericDeviceController(self._c_instance, self._eq_device, cc_map)
        else:
            self._eq_device_controller = None
        
    def _update_devices_info(self):
        # Update device selectors for track on the remote controller.
        if self._base_device_selection_cc != None:
            # get and store the list of devices
            devices = self.get_track_devices_flat(self._track)
            # prioritse devices with names that start with #
            self._devices = [d for d in devices if d.name[0] == '#'] + \
                [d for d in devices if d.name[0] != '#'] 
    
    def _handle_device_change(self):
        """Check whether the eq device for this track was changed/added/removed
           and if so, update the eq device controller and force a MIDI remap
           and state refresh; also update the list of devices for device selection
        """
        self.debug(3,f'Handle device change on track {self._track.name}.')
        # reconstruct the list of devices for device selection
        self._update_devices_info()
        # find the equaliser device on the track
        device = self._my_channel_eq(self._eq_device_name)
        # and if it changed, force an update
        # (note: if an existing eq-device is deleted, self._eq_device ALSO
        # becomes None, so we detect this by testing self._eq_device_controller)
        if (device != self._eq_device) or \
           (not device and self._eq_device_controller):
            self.debug(3,'EQ device change detected.')
            # we can use _eq_device_name and _eq_cc_map because add_eq_device already called earlier
            self.add_eq_device(self._eq_device_name,self._eq_cc_map) # also removes any previous eq device controller
            self.request_rebuild_midi_map() # also refreshes state

    def _refresh_track_name(self):
        """Change the track name displayed on the remote controller. To be
           overriden by subclass to correctly set track name.
        """
        pass

    def _refresh_clips(self):
        """Update the clip information in the session control page for this track.
           To be overriden by subclass.
        """
        pass
    
    def refresh_state(self):
        """ Send the values of the controlled elements to the E1
           (to bring them in sync). Initiated by MixerController
        """
        self.debug(3,f'Refreshing state of track { self._track.name }.')
        track = self._track
        self._refresh_track_name()
        self._update_devices_info()
        # update the selector on the E1
        devicenames = [d.name for d in self._devices]
        self.update_device_selector_for(self._devsel_idx,devicenames)
        self._property_controllers.refresh_state()
        # panning and volume always present
        self.send_parameter_as_cc14(track.mixer_device.panning, self._midichannel, self._my_cc(self._base_pan_cc))
        self.send_parameter_as_cc14(track.mixer_device.volume, self._midichannel, self._my_cc(self._base_volume_cc))
        if self._base_cue_volume_cc:  # master track only
            self.send_parameter_as_cc14(track.mixer_device.cue_volume, self._midichannel, self._my_cc(self._base_cue_volume_cc))
        # send sends
        if self._base_sends_cc != None: # audio/midi track only
            # note: if list is shorter, less sends included
            sends = track.mixer_device.sends[:MAX_NO_OF_SENDS]
            cc_no = self._my_cc(self._base_sends_cc)
            for send in sends:
                self.send_parameter_as_cc14(send,MIDI_SENDS_CHANNEL,cc_no)
                cc_no += NO_OF_TRACKS
        # send channel eq
        if self._eq_device_controller:
            self._eq_device_controller.refresh_state()
        # session control clips
        self._refresh_clips()
        
    def update_display(self):
        """Update the display (called every 100ms).
           Used to update the clip slot information in the session control page,
           partially because track.add_clip_slots_listener does not work (as I expected)
           and also to ensure that all changes are always sent to the E1.
        """
        self._refresh_clips()
    
    def disconnect(self):
        """Disconnect the track; remove all listeners.
        """
        self._remove_listeners()
        self._property_controllers.disconnect()

    # --- Listeners
    
    def add_listeners(self):
        """Add listeners for Mute, Arm, and Solo/Cue where relevant; these
           send changes to the UI elements in Live to the controller.
        """
        # (note: this needs to be called by the subclass, because
        # only the subclass defines _track!)
        self.debug(3,f'Adding listeners for track { self._track.name }')
        track = self._track
        self._property_controllers.add_on_off_property(track,'mute',self._midichannel,self._my_cc(self._base_mute_cc),True)
        self._property_controllers.add_on_off_property(track,'solo',self._midichannel,self._my_cc(self._base_solo_cue_cc))
        self._property_controllers.add_on_off_property(track,'arm',self._midichannel,self._my_cc(self._base_arm_cc))
        if ElectraOneBase.E1_DAW:
            self._update_devices_info()
            self._property_controllers.add_property(track,'device_selector',self._midichannel,self._my_cc(self._base_device_selection_cc),self._handle_device_selection,None)        
        track.add_name_listener(self._refresh_track_name)
        track.add_devices_listener(self._handle_device_change)
            
    def _remove_listeners(self):
        """Remove all listeners added.
        """
        track = self._track
        # track may already have been deleted
        if track:
            self.debug(3,f'Removing listeners for track { self._track.name }')
            if track.name_has_listener(self._refresh_track_name):
                track.remove_name_listener(self._refresh_track_name)
            if track.devices_has_listener(self._handle_device_change):
                track.remove_devices_listener(self._handle_device_change)
                
    # --- Special handlers ---
    
    def _handle_device_selection(self,value):
        """Default handler for handling device selection
           - value: incoming MIDI CC value; int
        """
        self.debug(4,f'Track { self._track.name } device selection action (value: {value}).')
        assert self._base_device_selection_cc != None, 'Bad device selection handler.'
        if (self._devices != None) and (value in range(len(self._devices))):
            # display the selected device; this also appoints the device
            self.song().view.select_device(self._devices[value])

        
    # --- MIDI ---
    
    def process_midi(self, midi_channel, cc_no, value):
        """Process incoming MIDI CC events for this track, and pass them to
           the correct handler (defined through _property_controllers() )
           - midi_channel: MIDI channel of incomming message; int (1..16)
           - cc_no: MIDI CC number; int (0..127)
           - value: incoming CC value; int (0..127)
           - returns: whether midi event processed by handler here; bool
        """
        self.debug(5,f'GenericTrackControler: trying to process MIDI by track { self._track.name}.')
        return self._property_controllers.process_midi(midi_channel,cc_no,value)

    def build_midi_map(self, script_handle, midi_map_handle):
        """Map all track controls on their associated MIDI CC numbers; either
           map them completely (Live handles all MIDI automatically) or make sure
           the right MIDI CC messages are forwarded to the remote script to be
           handled by the MIDI CC handlers defined here.
           - script_handle: reference to the main remote script class
               (whose receive_midi method will be called for any MIDI CC messages
               marked to be forwarded here)
           - midi_map_hanlde: MIDI map handle as passed to Ableton Live, to
               which MIDI mappings must be added.
        """
        self.debug(3,f'Building MIDI map of track { self._track.name }.')
        # Map property CCs to be forwarded
        self._property_controllers.build_midi_map(script_handle,midi_map_handle)
        # map main sliders
        # TODO/FIXME: not clear how this is honoured in the Live.MidiMaap.map_midi_cc call
        needs_takeover = True
        map_mode = Live.MidiMap.MapMode.absolute_14_bit
        track = self._track
        self.debug(4,f'Mapping track { self._track.name } pan to CC { self._my_cc(self._base_pan_cc) } on MIDI channel { self._midichannel }')
        Live.MidiMap.map_midi_cc(midi_map_handle, track.mixer_device.panning, self._midichannel-1, self._my_cc(self._base_pan_cc), map_mode, not needs_takeover)
        self.debug(4,f'Mapping track { self._track.name } volume to CC { self._my_cc(self._base_volume_cc) } on MIDI channel { self._midichannel }')
        Live.MidiMap.map_midi_cc(midi_map_handle, track.mixer_device.volume, self._midichannel-1, self._my_cc(self._base_volume_cc), map_mode, not needs_takeover)
        if self._base_cue_volume_cc != None:  # master track only
            self.debug(4,f'Mapping track { self._track.name } cue volume to CC { self._my_cc(self._base_cue_volume_cc) } on MIDI channel { self._midichannel }')
            Live.MidiMap.map_midi_cc(midi_map_handle, track.mixer_device.cue_volume, self._midichannel-1, self._my_cc(self._base_cue_volume_cc), map_mode, not needs_takeover)
        # map sends (if present): send i for this track is mapped to
        # cc = base_send_cc (for this track) + i * NO_OF_TRACKS
        if self._base_sends_cc != None:
            sends = track.mixer_device.sends[:MAX_NO_OF_SENDS] # never map more than MAX_NO_OF_SENDS
            cc_no = self._my_cc(self._base_sends_cc)
            for send in sends:
                self.debug(4,f'Mapping send to CC { cc_no } on MIDI channel { MIDI_SENDS_CHANNEL }')
                Live.MidiMap.map_midi_cc(midi_map_handle, send, MIDI_SENDS_CHANNEL-1, cc_no, map_mode, not needs_takeover)
                cc_no += NO_OF_TRACKS
        # map ChannelEq (if present)
        if self._eq_device_controller:
            self._eq_device_controller.build_midi_map(midi_map_handle)


   
        
   
