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

# CCs (see DOCUMENTATION.md)
MASTER_PAN_CC = 0
MASTER_VOLUME_CC = 1
MASTER_CUE_VOLUME_CC = 2
MASTER_SOLO_CC = 9

class MasterController(GenericTrackController):
    """Manage the master track. Instantiates GenericTrackController
       with the correct data for the master track.
    """

    def __init__(self, c_instance):
        """Initialise the master track controller.
           - c_instance: Live interface object (see __init.py__)
        """
        GenericTrackController.__init__(self, c_instance)
        self._track = self.song().master_track
        # EQ device 
        self.add_eq_device(MASTER_EQ_DEVICE_NAME,MASTER_EQ_CC_MAP)
        # midi info
        self._midichannel = MIDI_MASTER_CHANNEL
        # sliders
        self._base_pan_cc = MASTER_PAN_CC
        self._base_volume_cc = MASTER_VOLUME_CC
        self._base_cue_volume_cc = MASTER_CUE_VOLUME_CC 
        self._base_sends_cc = None # not present on a master track
        # buttons
        self._base_mute_cc = None # not present on a master track
        self._base_arm_cc = None # not present on a master track
        self._base_solo_cue_cc = None # present, but somehow not mappable
        #
        self.add_listeners()
        self.init_cc_handlers()
        self.debug(0,'MasterController loaded.')

    def _my_cc(self,base_cc):
        """Return the actual MIDI CC number for this instance of a control,
           given the base MIDI CC number for the control. 
           - base_cc: base MIDI CC number; int
           - result: actual MIDI CC number; int
        """
        return base_cc
    
    
