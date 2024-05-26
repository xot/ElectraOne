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
from .ElectraOneBase import ElectraOneBase 
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
        # device selector index of this track
        self._devsel_idx = offset
        # session control first clip row
        self._first_row_index = 0
        # cache clip slot information already sent to E1 
        self._clipinfo = None 
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
        # Device selection only for E1 DAW
        if ElectraOneBase.E1_DAW:
            self._base_device_selection_cc = DEVICE_SELECTION_CC
        # 
        self.add_listeners()
        self.init_cc_handlers()
        self.debug(0,'TrackController loaded.')

    def _refresh_clips(self):
        """Update the clip information in the session control page for this track.
        """
        clipinfo = []
        # _track can also be a chain (that doesn't have clipslots)           
        if (type(self._track) == Live.Track.Track):
            for i in range(NO_OF_SESSION_ROWS):
                clipslot = self._track.clip_slots[self._first_row_index + i]
                if clipslot.has_clip:
                    clip = clipslot.clip
                    clipinfo.append(f'"{clip.name}"') # for LUA conversion
                    clipinfo.append(str(clip.color))
                else: # empty clipslot
                    clipinfo.append('""') # for LUA conversion
                    clipinfo.append('0')
        # Only send updates if necessary (this function is very frequently called
        # through update_display()
        if self._clipinfo != clipinfo:
            self.debug(3,f'Refreshing clip information for track {self._offset}')
            self.update_session_control(self._offset,clipinfo)
            self._clipinfo = clipinfo
        
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
    

        
