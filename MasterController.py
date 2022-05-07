# MasterController
# - control the master track
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
# Proper device parameters (sliders onlt really) are mapped directly to
# their associated MIDI cc_no on a specific channel (see build_midi_map)
# using Live.MidiMap.map_midi_cc.
# From then on value updates from AND to the E1 are handled automatically.
# The only thing to do is call _init_controller_values() once (to send
# the values currently held by the device parameters are sent to the E1 to
# birng them in sync.
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

# - Listeners (see: _add/remove_listeners):
# Register a function to call whenever a Live element that is controlled
# changes state. Used for Live elements that cannot be mapped to Midi directly
# using Live.MidiMap.map_midi_cc (because Ableton doesn't model them as true
# device parameters.



# Ableton Live imports
import Live

# Local imports
from .config import *
from .PresetInfo import PresetInfo
from .ElectraOneBase import ElectraOneBase
from .EffectController import build_midi_map_for_device, update_values_for_device

# CCs (see MixerController.py)
MASTER_PAN_CC = 0
MASTER_VOLUME_CC = 1
MASTER_CUE_VOLUME_CC = 2
MASTER_SOLO_CC = 9

# Change this to manage a different EQ like device on the master track
# TODO: move this to devices
#
# Specify the device.class_name here
MASTER_EQ_DEVICE_NAME = 'ChannelEq'
#
# Specify the CC-map here (like in Devices.py)
MASTER_EQ_CC_MAP = { # 'Device On': (MIDI_TRACKS_CHANNEL,0,-1)
              'Highpass On': (MIDI_MASTER_CHANNEL, 0, 8)
            , 'Low Gain': (MIDI_MASTER_CHANNEL, 1, 6)
            , 'Mid Gain': (MIDI_MASTER_CHANNEL, 1, 5)
            , 'Mid Freq': (MIDI_MASTER_CHANNEL, 1, 4)
            , 'High Gain': (MIDI_MASTER_CHANNEL, 1, 3)
            , 'Gain': (MIDI_MASTER_CHANNEL, 1, 7)
            }

class MasterController(ElectraOneBase):
    """Manage the master track.
    """

    def __init__(self, c_instance):
        ElectraOneBase.__init__(self, c_instance)
        self._add_listeners()
        self._init_cc_handlers()
        self.debug(0,'MasterController loaded.')

    # --- helper functions ---
    
    def _my_channel_eq(self):
        # Return a reference to the Channel EQ device on my track, if present.
        # None if not
        devices = self.song().master_track.devices
        for d in devices:
            if d.class_name == MASTER_EQ_DEVICE_NAME:
                self.debug(4,'ChannelEq (or similar) device found')
                return d
        return None

    def _my_channel_eq_preset_info(self):
        return PresetInfo('',MASTER_EQ_CC_MAP)

    def refresh_state(self):
        # send the values of the controlled elements to the E1 (to bring them in sync)
        # called (and initiated by MixerController)
        track = self.song().master_track
        self.send_parameter_as_cc14(track.mixer_device.panning, MIDI_MASTER_CHANNEL, MASTER_PAN_CC)
        self.send_parameter_as_cc14(track.mixer_device.volume, MIDI_MASTER_CHANNEL, MASTER_VOLUME_CC)
        self.send_parameter_as_cc14(track.mixer_device.cue_volume, MIDI_MASTER_CHANNEL, MASTER_CUE_VOLUME_CC)
        # send channel eq
        channel_eq = self._my_channel_eq()
        if channel_eq:
            preset_info = self._my_channel_eq_preset_info()
            update_values_for_device(channel_eq, preset_info,self)
                                  
    def update_display(self):
        pass
    
    def disconnect(self):
        # cleanup
        self._remove_listeners()

    # --- Listeners
            
    def _add_listeners(self):
        # add listeners for changes to Live elements
        pass

    def _remove_listeners(self):
        # remove all listeners added
        pass

    # --- Handlers ---
    
    def _init_cc_handlers(self):
        # define handlers for incpming midi events
        pass
    
    # --- MIDI ---
    
    def process_midi(self, midi_channel, cc_no, value):
        # receive incoming midi events and pass them to the correct handler
        pass
    
    def build_midi_map(self, script_handle, midi_map_handle):
        self.debug(2,'Building master track MIDI map.')
        track = self.song().master_track
        # TODO/FIXME: not clear how this is honoured in the Live.MidiMaap.map_midi_cc call
        needs_takeover = True
        map_mode = Live.MidiMap.MapMode.absolute_14_bit
        self.debug(3,f'Mapping master pan to CC { MASTER_PAN_CC } on MIDI channel { MIDI_MASTER_CHANNEL }')
        # Note: this function expects MIDI_CHANNEL -1
        Live.MidiMap.map_midi_cc(midi_map_handle, track.mixer_device.panning, MIDI_MASTER_CHANNEL-1, MASTER_PAN_CC, map_mode, not needs_takeover)
        Live.MidiMap.map_midi_cc(midi_map_handle, track.mixer_device.volume, MIDI_MASTER_CHANNEL-1, MASTER_VOLUME_CC, map_mode, not needs_takeover)
        Live.MidiMap.map_midi_cc(midi_map_handle, track.mixer_device.cue_volume, MIDI_MASTER_CHANNEL-1, MASTER_CUE_VOLUME_CC, map_mode, not needs_takeover)
        # build ChannelEq
        channel_eq = self._my_channel_eq()
        if channel_eq:
            build_midi_map_for_device(midi_map_handle, channel_eq, self._my_channel_eq_preset_info(), self.debug)
    
