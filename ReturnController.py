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
from .ElectraOneBase import ElectraOneBase 
from .GenericTrackController import GenericTrackController

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
        # keep reference of track because if returns added/deleted, idx
        # points to a different track, which breaks _remove_listeners()
        self._track = self.song().return_tracks[idx]
        # index of this return track
        self._idx = idx
        # device selector index of this track
        self._devsel_idx = NO_OF_TRACKS + idx
        # EQ device info
        self._eq_device_name = None # not present on a return track
        self._eq_cc_map = None
        # midi info
        self._midichannel = MIDI_MASTER_CHANNEL
        # sliders
        self._base_pan_cc = RETURNS_PAN_CC
        self._base_volume_cc = RETURNS_VOLUME_CC
        self._base_cue_volume_cc = None  # not present on a return track
        self._base_sends_cc = None # not present on a return track
        # buttons
        self._base_mute_cc = RETURNS_MUTE_CC
        self._base_arm_cc = None # not present on a return track
        self._base_solo_cue_cc = RETURNS_SOLO_CUE_CC
        # Device selection only for E1 DAW
        if ElectraOneBase.E1_DAW:
            self._base_device_selection_cc = RM_DEVICE_SELECTION_CC
        #
        self.add_listeners()
        self.init_cc_handlers()
        self.debug(0,'ReturnController loaded.')
            
    def _refresh_track_name(self):
        """Change the track name displayed on the remote controller for
           this return track. Also updates the sends
        """
        self.update_return_sends_labels(self._idx,self._track.name)
        
    def _my_cc(self,base_cc):
        """Return the actual MIDI CC number for this instance of a control,
           given the base MIDI CC number for the control. 
           - base_cc: base MIDI CC number; int
           - result: actual MIDI CC number; int
        """
        return (base_cc + self._idx if base_cc != None else None)


