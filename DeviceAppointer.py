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
        self.debug(0,'DeviceAppointer initialised.')
        
    def _handle_selected_track_change(self):
        """Handle a track selection change: make the currently selected device
           appointed, and add a listener for device selection changes on
           this track. 
        """
        # This even works for chains in drum or instrument racks
        track = self.song().view.selected_track
        # song may not contain any tracks
        if track:
            prev_track = self._selected_track
            # check if selection changed
            if track != prev_track:
                # remove device selection listener from previously selected
                # track if necessary
                if prev_track:
                    self.debug(2,f'Track { prev_track.name } deselected. Removing selected device listener')
                    if prev_track.view.selected_device_has_listener(self._handle_selected_device_change):
                        prev_track.view.remove_selected_device_listener(self._handle_selected_device_change)
                # add device selection listener to currently selected track
                self._selected_track = track
                self.debug(2,f'Track { track.name } selected. Adding selected device listener')
                track.view.add_selected_device_listener(self._handle_selected_device_change)
                # appoint device if needed
                if APPOINT_ON_TRACK_CHANGE:
                    # get and store the list of devices
                    devices = self.get_track_devices_flat(track)
                    # appoint preferred device (whose name starts with !) instead
                    # of selected device
                    # TODO: skip appointment and instruct EffectController
                    # directly to control this device (and leave apoointed device
                    # so other control surface can still control that)
                    preferred = [d for d in devices if d.name[0] == '!']
                    if len(preferred) > 0:
                        device = preferred[0]
                    else:
                        device = track.view.selected_device
                    self._appoint_device(device)
                else:
                    self.debug(2,'No device appointment when selected track changes.')
            else:
                self.debug(2,f'Track { track.name } already selected. Ignoring.')

    def _appoint_device(self,device):
        """Appoint the specified device
           - device: device to appoint; Live.Device.Device (!= None)
        """
        device_name = self.get_device_name(device)
        self.debug(0,f'Device { device_name } selected. Now appoint it.')
        # TODO: when deleting track, device = None;
        # but apparently self.song().appointed_device is also None
        # because the device it pointed to is gone
        #
        # Q: how to trigger  _handle_appointed_device_change?
        # (assigning None to self.song().appointed_device doesn't work
        if (not device) or (self.song().appointed_device != device):
            self.debug(1,f'\\ Set as appointed device (unappointed if None).')
            # this will trigger the _handle_appointed_device_change
            # listener registered by EffectController
            self.song().appointed_device = device
        else:
            self.debug(1,f'\\ Appointed device not changed.')                
                
    def _handle_selected_device_change(self):
        """Handle a device selection change: make the currently selected device
           appointed.
        """
        # get currently selected track
        track = self.song().view.selected_track
        # song may not contain any tracks
        if track:
            # get currently selected device from currently selected track
            device = track.view.selected_device
            self._appoint_device(device)
        
