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
import Live

# Local imports
from .config import *
from .GenericTrackController import GenericTrackController

class TrackController(GenericTrackController):
    """Manage an audio or midi track. Instantiates GenericTrackController
       with the correct data for the track. At most five instances, one
       for each track present.
    """
    
    def __init__(self, c_instance, track, offset):
        """Initialise a track controller for track idx.
           - c_instance: Live interface object (see __init.py__)
           - track: reference to the actual track
           - offset: offset of this track realtive to the first mapped track; int
        """
        GenericTrackController.__init__(self, c_instance)
        self._track = track
        # offset of this track relative to the first mapped track
        self._offset = offset
        # EQ device
        self.add_eq_device(TRACK_EQ_DEVICE_NAME,TRACK_EQ_CC_MAP) 
        # midi info
        self._midichannel = MIDI_TRACKS_CHANNEL
        # sliders
        self._base_pan_cc = PAN_CC
        self._base_volume_cc = VOLUME_CC
        self._base_cue_volume_cc = None  # not present on a normal track
        self._base_sends_cc = SENDS_CC
        # buttons
        self._base_mute_cc = MUTE_CC
        # _track can also be a chain
        if (type(self._track) == Live.Track.Track) and self._track.can_be_armed:
            self._base_arm_cc = ARM_CC
        else:
            self._base_arm_cc = None # group tracks and chains cannot be armed
        self._base_solo_cue_cc = SOLO_CUE_CC 
        self._base_device_selection_cc = DEVICE_SELECTION_CC
        # 
        self.add_listeners()
        self.init_cc_handlers()
        self.debug(0,'TrackController loaded.')

    def _update_devices_info(self):
        # Update device selectors for track on the remote controller.
        # TODO: update fails initially: it is sent; but display  not updated
        if self._base_device_selection_cc != None:
            # get and store the list of devices
            self._devices = self.get_track_devices_flat(self._track)
            # update the selector on the E1
            devicenames = [d.name for d in self._devices]
            self.update_device_selector_for_track(self._offset,devicenames)
            
    def _refresh_track_name(self):
        """Change the track name displayed on the remote controller for
           this return track.
        """
        self.update_track_labels(self._offset,self._track.name)

    def _my_cc(self,base_cc):
        """Return the actual MIDI CC number for this instance of a control,
           given the base MIDI CC number for the control. 
           - base_cc: base MIDI CC number; int
           - result: actual MIDI CC number; int
        """
        return base_cc + self._offset
    

        
