# DeviceAppointer
# - Handle device appointment: keep track of track changes, and make/keep the
#   currently selected device there the appointed device
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


# TODO: how does this interfere with device appointment by other control surfaces
class DeviceAppointer(ElectraOneBase):
    """Maintain the currently selected device on the currently selected track
       as the appointed device.
    """

    def __init__(self, c_instance):
        """Initialise the device apointer
           (Must be called only once, after loading a song.)
           - c_instance: Live interface object (see __init.py__)
        """
        ElectraOneBase.__init__(self, c_instance)
        # register the track selection listener (will in turn listen to device
        # selections)
        view = self.song().view
        view.add_selected_track_listener(self._handle_selected_track_change)
        # initially no track selected
        self._selected_track = None
        # this triggers initial device appointment
        self._handle_selected_track_change()
        self.debug(0,'DeviceAppointer loaded.')
        
    def _handle_selected_track_change(self):
        """Handle a track selection change: make the currently selected device
           appointed, and add a listener for device selection changes on
           this track. 
        """
        track = self.song().view.selected_track
        # song may not contain any tracks
        if track:
            prev_track = self._selected_track
            # check if selection changed
            if track != prev_track:
                # remove device selection listener from previously selected
                # track if necessary
                if prev_track:
                    self.debug(3,f'Track { prev_track.name } deselected. Removing selected device listener')
                    if prev_track.view.selected_device_has_listener(self._handle_selected_device_change):
                        prev_track.view.remove_selected_device_listener(self._handle_selected_device_change)
                # add device selection listener to currently selected track
                self._selected_track = track
                self.debug(3,f'Track { track.name } selected. Adding selected device listener')
                track.view.add_selected_device_listener(self._handle_selected_device_change)
                # appoint device if needed
                if APPOINT_ON_TRACK_CHANGE:
                    self._handle_selected_device_change()            
            else:
                self.debug(3,f'Track { track.name } already selected. Ignoring.')
            
    def _handle_selected_device_change(self):
        """Handle a device selection change: make the currently selected device
           appointed.
        """
        # get selected device from currently selected track
        track = self.song().view.selected_track
        # song may not contain any tracks
        if track:
            device = track.view.selected_device
            if device:
                device_name = self.get_device_name(device)
                self.debug(3,f'Device { device_name } selected. Now appoint it.')
            else:
                self.debug(3,f'No device selected. Now unappoint it.')
            if self.song().appointed_device != device:
                self.debug(3,f'\ Set as appointed device (unappointed if none).')
                # this will trigger the _handle_appointed_device_change
                # listener registered by EffectController
                self.song().appointed_device = device
            else:
                self.debug(3,f'\ Appointed device not changed.')                
        
