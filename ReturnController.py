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

# CCs (see DOCUMENTATION.md)
# These are base values, to which the returun index is added for each next return track
RETURNS_PAN_CC = 10 
RETURNS_VOLUME_CC = 16
RETURNS_MUTE_CC = 70
#

class ReturnController(GenericTrackController):
    """Manage a return track. Instantiates GenericTrackController
       with the correct data for a return track. One instance for
       each return track present. (At most six).
    """

 
    def __init__(self, c_instance, idx):
        """Initialise a return controller for return idx (starting at 0). 
           - c_instance: Live interface object (see __init.py__)
           - idx: index in the list of return tracks, 0=first; int
        """
        GenericTrackController.__init__(self, c_instance)
        self._idx = idx
        # keep reference of track because if returns added/deleted, idx
        # points to a different track, which breaks _remove_listeners()
        self._track = self.song().return_tracks[idx]
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
        """Change the track name displayed on the remote controller for
           this return track.
        """
        # return tracks page
        self.update_group_label(self._idx+20, self._track.name)
        # sends page
        self.update_controls_labels( { 6*self._idx + 73 + j for j in range(5) }, self._track.name) 
        
    def _my_cc(self,base_cc):
        """Return the actual MIDI CC number for this instance of a control,
           given the base MIDI CC number for the control. 
           - base_cc: base MIDI CC number; int
           - result: actual MIDI CC number; int
        """
        return base_cc + self._idx

    def _init_cc_handlers(self):
        """Define handlers for incoming MIDI CC messages.
           (Mute button only for the return track)
        """
        self._CC_HANDLERS = {
                (MIDI_MASTER_CHANNEL, self._my_cc(RETURNS_MUTE_CC) ) : self._handle_mute_button
            }

