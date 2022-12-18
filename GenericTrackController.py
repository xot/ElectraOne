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
# DOCUMENTATION
#
# General idea of this module:
#
# Proper device parameters (sliders only really) are mapped directly to
# their associated MIDI cc_no on a specific channel (see build_midi_map)
# using Live.MidiMap.map_midi_cc.
# From then on value updates from AND to the E1 are handled automatically.
# The only thing to do is call refresh_state() once (to send
# the values currently held by the device parameters are sent to the E1 to
# bring them in sync.
#
# For all other controlled elements we need handlers (to handle incoming data
# from the E1 controller) and listeners (to send updates to the E1 controleer)
#
# - Handlers (see: _init_cc_handlers, receive_midi, build_midi_map)
# Link a (MIDI_channel,cc_no) pair to a handler function that must be
# called whenever the specfied midi CC message (7bit only) is sent by the E1.
# Uses Live.MidiMap.forward_midi_cc (see build_midi_map)
# which causes the specified MIDI message to be received through Receive_midi.
# The handler is then called with the received value. 
#
# - Listeners (see: _add/remove_listeners):
# Register a function to call whenever a Live element that is controlled
# changes state. Used for Live elements that cannot be mapped to Midi directly
# using Live.MidiMap.map_midi_cc (because Ableton doesn't model them as true
# device parameters.
#
# This class is the base class for TrackController, MasterController and
# ReturnController. The idea being that all three share a similar structure
# (they are all 'tracks') except that each of them has slightly different
# features. Which features are present is indicated through the definition of
# the corresponding CC parameter value in the __init__ constructor of the
# subclass (where the value ```None``` indicates a feature is missing).
#
# The GenericTrackController expects the subclass to define a method
# _my_cc that derives the actual CC parameter number to use for a particular
# instance of an audio/midi track (TrackController) or a return track
# (ReturnController).
#
# It also expects the subclasses to define _init_cc_handlers to set
# self._CC_HANDLERS to the required handlers. (This roundabout way is necessary
# because these handlers may depend on the particular instance of the track
# they manage and therefore need to call _my_cc() to obtain the correct CC
# parameter number.
#
# Send controllers on audio/midi tracks, i.e those for which _sends_cc != None
# are assumed to listen to MIDI_SENDS_CHANNEL

# Ableton Live imports
import Live

# Local imports
from .config import *
from .PresetInfo import PresetInfo
from .CCInfo import UNMAPPED_ID
from .ElectraOneBase import ElectraOneBase
# TODO: new feature
#from .ValueListener import ValueListeners
from .GenericDeviceController import GenericDeviceController



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
        # EQ device info
        self._eq_device_controller = None # if None not present (ie all returns)
        # midi info
        self._midichannel = None
        # slider CC numbers
        self._base_pan_cc = None
        self._base_volume_cc = None
        self._base_cue_volume_cc = None  # if None, not present (ie all non master tracks)
        self._sends_cc = None # if None, not present (ie all non audio/midi tracks)
        # button CC numbers
        self._base_mute_cc = None # if None, not present (i.e. master track)
        self._base_arm_cc = None # if None, not present (i.e. groups and returns)
        self._base_solo_cue_cc = None # if None, not present (i.e. all non audio/midi tracks)
        # TODO new feature
        self._value_listeners = None
        #
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
        devices = self._track.devices
        for d in reversed(devices):
            if d.class_name == eq_device_name:
                self.debug(3,'ChannelEq (or similar) device found')
                return d
        return None

    def _my_channel_eq_preset_info(self, eq_cc_map):
        """Return the preset info associated with the Channel EQ Device on this
           track, filling in the correct MIDI CC numbers for this
           particular instance of the device using eq_cc_map as source
           for the base values.
           - eq_cc_map: ; dict of CCInfo
           - result: CC map in a preset info (with empty preset JSON string!); PresetInfo
        """
        cc_map = {}
        for p in eq_cc_map:
            (channel, is_cc14, cc_no) = eq_cc_map[p]
            # add the offset to the cc_no present in TRACK_EQ_CC_MAP
            cc_map[p] = (UNMAPPED_ID, channel, is_cc14, self._my_cc(cc_no))
        return PresetInfo('','',cc_map)

    def _refresh_track_name(self):
        """Change the track name displayed on the remote controller. To be
           overriden by subclass.
        """
        # Overriden by TrackController and ReturnController to rename track names
        pass

    def add_eq_device(self, eq_device_name, cc_map):
        device = self._my_channel_eq(eq_device_name)
        if device:
            preset_info = self._my_channel_eq_preset_info(cc_map)
            assert preset_info
            self._eq_device_controller = GenericDeviceController(self._c_instance, device, preset_info)
        else:
            self._eq_device_controller = None
        
    def refresh_state(self):
        """ Send the values of the controlled elements to the E1
           (to bring them in sync). Initiated by MixerController
        """
        self.debug(2,f'Refreshing state of track { self._track.name }.')
        track = self._track
        self._refresh_track_name()
        if self._base_mute_cc != None:
            self._on_mute_changed()
        if self._base_arm_cc != None:
            self._on_arm_changed()
        if self._base_solo_cue_cc != None:
            self._on_solo_cue_changed()
        # panning and volume always present
        self.send_parameter_as_cc14(track.mixer_device.panning, self._midichannel, self._my_cc(self._base_pan_cc))
        self.send_parameter_as_cc14(track.mixer_device.volume, self._midichannel, self._my_cc(self._base_volume_cc))
        if self._base_cue_volume_cc:  # master track only
            self.send_parameter_as_cc14(track.mixer_device.cue_volume, self._midichannel, self._my_cc(self._base_cue_volume_cc))
        # send sends
        if self._sends_cc != None: # audio/midi track only
            # note: if list is shorter, less sends included
            sends = track.mixer_device.sends[:MAX_NO_OF_SENDS]
            cc_no = self._my_cc(self._sends_cc)
            for send in sends:
                self.send_parameter_as_cc14(send,MIDI_SENDS_CHANNEL,cc_no)
                cc_no += NO_OF_TRACKS
        # send channel eq
        if self._eq_device_controller:
            self._eq_device_controller.refresh_state()
        # TODO: value listeners
        #if self._value_listeners:
        #    self._value_listeners.update_all()
        
    def update_display(self):
        """Update the display. (Does nothing.)        
        """
        pass
    
    def disconnect(self):
        """Disconnect the track; remove all listeners.
        """
        self._remove_listeners()

    # --- Listeners
    
    def add_listeners(self):
        """Add listeners for Mute, Arm, and Solo/Cue where relevant; these
           send changes to the UI elements in Live to the controller.
        """
        # (note: this needs to be called by the subclass, because
        # only the subclass defines _track!)
        self.debug(3,f'Adding listeners for track { self._track.name }')
        track = self._track
        if self._base_mute_cc != None:
            track.add_mute_listener(self._on_mute_changed)
        if self._base_arm_cc != None: 
            track.add_arm_listener(self._on_arm_changed)
        if self._base_solo_cue_cc != None:
            track.add_solo_listener(self._on_solo_cue_changed)
        track.add_name_listener(self._refresh_track_name)
        # TODO: add value listener data
        #self._value_listeners = ValueListeners(self)
        #self._value_listeners.add(track.mixer_device.volume, None)
        #self._value_listeners.add(track.mixer_device.panning, None)
        #if self._base_cue_volume_cc:  # master track only
        #    self._value_listeners.add(track.mixer_device.cue_volume, None)
        # get at most MAX_NO_OF_SENDS sends
        #sends = track.mixer_device.sends[:MAX_NO_OF_SENDS]
        #if self._sends_cc != None: # audio/midi tracks only
        #    for send in sends:
        #        self._value_listeners.add(send, None)
            
    def _remove_listeners(self):
        """Remove all listeners added.
        """
        track = self._track
        # track may already have been deleted
        if track:
            self.debug(3,f'Removing listeners for track { self._track.name }')
            if self._base_mute_cc != None:
                track.remove_mute_listener(self._on_mute_changed)
            if self._base_arm_cc != None:
                track.remove_arm_listener(self._on_arm_changed)
            if self._base_solo_cue_cc != None:
                track.remove_solo_listener(self._on_solo_cue_changed)
            if track.name_has_listener(self._refresh_track_name):
                track.remove_name_listener(self._refresh_track_name)
            # remove value listeners
            #if self._value_listeners:
            #    self._value_listeners.remove_all()
            #also delete eq device value listeners here, becuase we do
            #not get notified any other way
            if self._eq_device_controller:
                self._eq_device_controller.remove_listeners()

        
    def _on_mute_changed(self):
        """Send the new status of the Mute button to the controller using the
           right MIDI CC number (derived from self._base_mute_cc)
        """
        self.debug(3,'Mute changed.')
        assert self._base_mute_cc != None
        if self._track.mute:
            value = 0
        else:
            value = 127
        self.send_midi_cc7(self._midichannel, self._my_cc(self._base_mute_cc), value) 

    def _on_arm_changed(self):
        """Send the new status of the Arm button to the controller using the
           right MIDI CC number (derived from self._base_arm_cc)
        """
        self.debug(3,'Arm changed.')
        assert self._base_arm_cc != None
        if self._track.arm:
            value = 127
        else:
            value = 0
        self.send_midi_cc7(self._midichannel, self._my_cc(self._base_arm_cc), value)
    
    def _on_solo_cue_changed(self):
        """Send the new status of the Solo/Cue button to the controller using the
           right MIDI CC number (derived from self._base_solo_cue_cc)
        """
        self.debug(3,'Solo/Cue changed.')
        assert self._base_solo_cue_cc != None
        if self._track.solo:
            value = 127
        else:
            value = 0
        self.send_midi_cc7(self._midichannel, self._my_cc(self._base_solo_cue_cc), value)
    
    # --- Handlers ---
    
    def _init_cc_handlers(self):
        """Define handlers for incoming MIDI CC messages.
           (to be defined by subclass)
        """
        pass
    
    def _handle_mute_button(self,value):
        """Default handler for Mute button
           - value: incoming MIDI CC value; int
        """
        self.debug(2,f'Track { self._track.name } activation button action.')
        if self._base_mute_cc != None:
            self._track.mute = (value < 64)

    def _handle_arm_button(self,value):
        """Default handler for Arm button
           - value: incoming MIDI CC value; int
        """
        self.debug(2,f'Track { self._track.name } arm button action.')
        if self._base_arm_cc != None:
            self._track.arm = (value > 63)

    def _handle_solo_cue_button(self,value):
        """Default handler for Solo/Cue button
           - value: incoming MIDI CC value; int
        """
        self.debug(2,f'Track { self._track.name } solo/cue button action.')
        if self._base_solo_cue_cc != None:
            self._track.solo = (value > 63)

    # --- MIDI ---
    
    def process_midi(self, midi_channel, cc_no, value):
        """Process incoming MIDI CC events for this track, and pass them to
           the correct handler (defined by self._CC_HANDLERS as set up
           by the call to self._init_cc_handlers() )
           - midi_channel: MIDI channel of incomming message; int (1..16)
           - cc_no: MIDI CC number; int (0..127)
           - value: incoming CC value; int (0..127)
        """
        self.debug(5,f'GenericTrackControler: trying to process MIDI by track { self._track.name}.')
        if (midi_channel,cc_no) in self._CC_HANDLERS:
            self.debug(5,f'GenericTrackController: handler found for CC {cc_no} on MIDI channel {midi_channel}.')
            handler = self._CC_HANDLERS[(midi_channel,cc_no)]
            handler(value)

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
        self.debug(2,f'Building MIDI map of track { self._track.name }.')
        # Map button CCs to be forwarded as defined in MIXER_CC_HANDLERS
        for (midi_channel,cc_no) in self._CC_HANDLERS:
            self.debug(4,f'GenericTrackController: setting up handler for CC {cc_no} on MIDI channel {midi_channel}')
            Live.MidiMap.forward_midi_cc(script_handle, midi_map_handle, midi_channel - 1, cc_no)
        # map main sliders
        # TODO/FIXME: not clear how this is honoured in the Live.MidiMaap.map_midi_cc call
        needs_takeover = True
        map_mode = Live.MidiMap.MapMode.absolute_14_bit
        track = self._track
        self.debug(3,f'Mapping track { self._track.name } pan to CC { self._my_cc(self._base_pan_cc) } on MIDI channel { self._midichannel }')
        Live.MidiMap.map_midi_cc(midi_map_handle, track.mixer_device.panning, self._midichannel-1, self._my_cc(self._base_pan_cc), map_mode, not needs_takeover)
        self.debug(3,f'Mapping track { self._track.name } volume to CC { self._my_cc(self._base_volume_cc) } on MIDI channel { self._midichannel }')
        Live.MidiMap.map_midi_cc(midi_map_handle, track.mixer_device.volume, self._midichannel-1, self._my_cc(self._base_volume_cc), map_mode, not needs_takeover)
        if self._base_cue_volume_cc != None:  # master track only
            self.debug(3,f'Mapping track { self._track.name } cue volume to CC { self._my_cc(self._base_cue_volume_cc) } on MIDI channel { self._midichannel }')
            Live.MidiMap.map_midi_cc(midi_map_handle, track.mixer_device.cue_volume, self._midichannel-1, self._my_cc(self._base_cue_volume_cc), map_mode, not needs_takeover)
        # map sends (if present)
        if self._sends_cc != None:
            sends = track.mixer_device.sends[:MAX_NO_OF_SENDS] # never map more than MAX_NO_OF_SENDS
            cc_no = self._my_cc(self._sends_cc)
            for send in sends:
                self.debug(3,f'Mapping send to CC { cc_no } on MIDI channel { MIDI_SENDS_CHANNEL }')
                Live.MidiMap.map_midi_cc(midi_map_handle, send, MIDI_SENDS_CHANNEL-1, cc_no, map_mode, not needs_takeover)
                cc_no += NO_OF_TRACKS
        # map ChannelEq (if present)
        if self._eq_device_controller:
            self._eq_device_controller.build_midi_map(midi_map_handle)


   
        
   
