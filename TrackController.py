# TrackController
# - control one track
#
# Part of ElectraOne
#
# Ableton Live MIDI Remote Script for the Electra One
#
# Author: Jaap-henk Hoepman (info@xot.nl)
#
# Distributed under the MIT License, see LICENSE

# Ableton Live imports
#import Live

# Local imports
from .config import *
from .GenericTrackController import GenericTrackController

# CCs (see MixerController.py)
# These are base values, to which TRACKS_FACTOR is added for each next return track
PAN_CC = 0
VOLUME_CC = 5
MUTE_CC = 116   
SOLO_CUE_CC = 84
ARM_CC = 89

# Sends (on MIDI_SENDS_CHANNEL)
# The code in GenericTrackController assumes all sends are mapped after each
# other, ie with increments of NO_OF_TRACKS=5
SENDS_CC = 0  

# Change this to managa a different EQ like device on every track
# TODO: move this to Devices (but this modifying the ./makedevices script)
#
# Specify the device.class_name here
TRACK_EQ_DEVICE_NAME = 'ChannelEq'
#
# Specify the CC-map here (like in Devices.py)
# The only rule is that the actual cc_no for a parameter is obtained
# by adding the offset to the base defined here
TRACK_EQ_CC_MAP = { # 'Device On': (MIDI_TRACKS_CHANNEL,0,-1)
              'Highpass On': (MIDI_TRACKS_CHANNEL, 0, 121)
            , 'Low Gain': (MIDI_TRACKS_CHANNEL, 1, 25)
            , 'Mid Gain': (MIDI_TRACKS_CHANNEL, 1, 20)
            , 'Mid Freq': (MIDI_TRACKS_CHANNEL, 1, 15)
            , 'High Gain': (MIDI_TRACKS_CHANNEL, 1, 10)
            , 'Gain': (MIDI_TRACKS_CHANNEL, 0, 64)
            }

class TrackController(GenericTrackController):
    """Manage an audio or midi track.
    """
    
    def __init__(self, c_instance, idx, offset):
        """Initialise a return controller for track idx
        """
        GenericTrackController.__init__(self, c_instance)
        # keep reference of track because if tracks added/deleted, idx
        # points to a different track, which breaks _remove_listeners()
        self._track = self.song().visible_tracks[idx]
        # offset of this track relative to the first mapped track
        self._offset = offset
        self._eq_device_name = TRACK_EQ_DEVICE_NAME 
        self._eq_cc_map = TRACK_EQ_CC_MAP
        # midi info
        self._midichannel = MIDI_TRACKS_CHANNEL
        # sliders
        self._base_pan_cc = PAN_CC
        self._base_volume_cc = VOLUME_CC
        self._base_cue_volume_cc = None  # not present on a normal track
        self._sends_cc = 0 
        # buttons
        self._base_mute_cc = MUTE_CC
        if self._track.can_be_armed:
            self._base_arm_cc = ARM_CC
        else:
            self._base_arm_cc = None # group tracks cannot be armed
        self._base_solo_cue_cc = SOLO_CUE_CC 
        #
        self.add_listeners()
        self._init_cc_handlers()
        self.debug(0,'TrackController loaded.')

    def _refresh_track_name(self):
        # TODO: this may need to be updated with E1 firmware API changes
        # tracks page
        idx = self._offset+1
        command = f'local group = groups.get({idx})\n group:setLabel("{self._track.name}")'
        self._send_lua_command(command)
        # channel eq page
        idx = self._offset+9
        command = f'local group = groups.get({idx})\n group:setLabel("{self._track.name}")'
        self._send_lua_command(command)
        # sends page
        idx = self._offset+15
        command = f'local group = groups.get({idx})\n group:setLabel("{self._track.name}")'
        self._send_lua_command(command)

    def _my_cc(self,base_cc):
        # derive the actual cc_no from the assigned base CC and my index
        return base_cc + self._offset
    
    def _init_cc_handlers(self):
        # define handlers for incpming midi events
        self._CC_HANDLERS = {
                (MIDI_TRACKS_CHANNEL, self._my_cc(MUTE_CC) ) : self._handle_mute_button
              , (MIDI_TRACKS_CHANNEL, self._my_cc(SOLO_CUE_CC) ) : self._handle_solo_cue_button
              , (MIDI_TRACKS_CHANNEL, self._my_cc(ARM_CC) ) : self._handle_arm_button
        }

        
