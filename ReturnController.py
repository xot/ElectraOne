# ReturnController
# - control one return track
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
# These are base values, to which the returun index is added for each next return track
RETURNS_PAN_CC = 10 
RETURNS_VOLUME_CC = 16
RETURNS_MUTE_CC = 70
#

class ReturnController(GenericTrackController):
    """Manage a return track.
    """
 
    def __init__(self, c_instance, idx):
        """Initialise a return controller for return idx (starting at 0). 
        """
        GenericTrackController.__init__(self, c_instance)
        self._idx = idx
        # keep reference of track because if returns added/deleted, idx
        # points to a different track, which breaks _remove_listeners()
        self._track = self.song().return_tracks[idx]
        self._name = self._track.name 
        # EQ device info
        self._eq_device_name = None # not present on a return track
        self._eq_cc_map = None
        # midi info
        self._midichannel = MIDI_MASTER_CHANNEL
        # sliders
        self._base_pan_cc = RETURNS_PAN_CC
        self._base_volume_cc = RETURNS_VOLUME_CC
        self._base_cue_volume_cc = None  # not present on a return track
        self._sends_cc = None # not present on a return track
        # buttons
        self._base_mute_cc = RETURNS_MUTE_CC
        self._base_arm_cc = None # not present on a return track
        self._base_solo_cue_cc = None # not present on a return track
        #
        self.add_listeners()
        self._init_cc_handlers()
        self.debug(0,'ReturnController loaded.')

    def _refresh_track_name(self):
        # TODO: this may need to be updated with E1 firmware API changes
        # return tracks page
        idx = self._idx+20
        command = f'local group = groups.get({idx})\n group:setLabel("{self._name}")'
        self._send_lua_command(command)
        # TODO: update control name on send page as well: enable after bug fix of firmware
        # send A (idx 0) = id 73 - 77; send B = 79 - 83; etc
        idx = 73 + 6 * self._idx
        # command = f'for i = {idx}, {idx}+4 do\n local control = controls.get(i)\n control:setName("{self._name}")\n end'
        self._send_lua_command(command)
        
    def _my_cc(self,base_cc):
        # derive the actual cc_no from the assigned base CC and my index
        return base_cc + self._idx

    def _init_cc_handlers(self):
        # define handlers for incpming midi events
        self._CC_HANDLERS = {
                (MIDI_MASTER_CHANNEL, self._my_cc(RETURNS_MUTE_CC) ) : self._handle_mute_button
            }

