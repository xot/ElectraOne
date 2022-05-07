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

# Local imports
from .config import *
from .GenericTrackController import GenericTrackController

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

class MasterController(GenericTrackController):
    """Manage the master track.
    """

    def __init__(self, c_instance):
        GenericTrackController.__init__(self, c_instance)
        self._track = self.song().master_track
        self._name = f'Master track'
        # EQ device info
        self._eq_device_name = MASTER_EQ_DEVICE_NAME # if None not present (ie all returns)
        self._eq_cc_map = MASTER_EQ_CC_MAP
        # midi info
        self._midichannel = MIDI_MASTER_CHANNEL
        # sliders
        self._base_pan_cc = MASTER_PAN_CC
        self._base_volume_cc = MASTER_VOLUME_CC
        self._base_cue_volume_cc = MASTER_CUE_VOLUME_CC  # if None, not present (ie all non master tracks)
        self._sends_cc = None # if None, not present (ie all non audio/midi tracks)
        # buttons
        self._base_mute_cc = None # if None, not present (i.e. master track)
        self._base_arm_cc = None # if None, not present (i.e. groups and returns)
        self._base_solo_cue_cc = None # if None, not present (i.e. all non audio/midi tracks)
        #
        self._add_listeners()
        self._init_cc_handlers()
        self.debug(0,'MasterController loaded.')

    def _my_cc(self,base_cc):
        # derive the actual cc_no from the assigned base CC and my index
        return base_cc
    
    def _init_cc_handlers(self):
        # define handlers for incpming midi events
        self._CC_HANDLERS = {}

    
