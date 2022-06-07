# ElectraOne
#
# Ableton Live MIDI Remote Script for the Electra One
#
# Author: Jaap-henk Hoepman (info@xot.nl)
#
# Distributed under the MIT License, see LICENSE
#

# Python imports
import json
import threading
import time
import sys

# Local imports
from .ElectraOneBase import ElectraOneBase
from .EffectController import EffectController
from .MixerController import MixerController
from .config import *

# SysEx defines and helpers

CC_STATUS = 0xB0

# SysEx incoming commands

E1_SYSEX_PREFIX = (0xF0, 0x00, 0x21, 0x45)
E1_SYSEX_LOGMESSAGE = (0x7F, 0x00) # followed by json data and terminated by 0xF7
E1_SYSEX_PRESET_CHANGED = (0x7E, 0x02)  # followed by bank-number slot-number and terminated by 0xF7
E1_SYSEX_ACK = (0x7E, 0x01) # followed by two zero's (reserved) and terminated by 0xF7
E1_SYSEX_NACK = (0x7E, 0x00) # followed by two zero's (reserved) and terminated by 0xF7
E1_SYSEX_REQUEST_RESPONSE = (0x01, 0x7F) # followed by json data and terminated by 0xF7

SYSEX_TERMINATE = 0xF7

# Additional SysEx commands defined specifically for this remote script

# SysEx sent when pressing the PATCH REQUEST button on the E1
# (Actually will also send 0x7E 0x7E 0x01 etc if more than one
# device present in the patch; these are ignored)
E1_SYSEX_PATCH_REQUEST_PRESSED = (0x7E, 0x7E, 0x00) # terminated by 0xF7


# SysEx outgoing commands

E1_SYSEX_REQUEST = (0xF0, 0x00, 0x21, 0x45, 0x02, 0x7F, 0xF7)

def _is_sysex_preset_changed(midi_bytes):
    """Return true if the midi_bytes represent a sysex preset changed message
       - midi_bytes: incoming MIDI message; sequence of bytes
       - result: bool
    """
    return (len(midi_bytes) == 9) and \
           (midi_bytes[4:6] == E1_SYSEX_PRESET_CHANGED) and \
           (midi_bytes[8] == SYSEX_TERMINATE)

def _is_sysex_ack(midi_bytes):
    """Return true if the midi_bytes represent an ACK message
       - midi_bytes: incoming MIDI message; sequence of bytes
       - result: bool
    """
    return (len(midi_bytes) == 9) and \
           (midi_bytes[4:6] == E1_SYSEX_ACK) and \
           (midi_bytes[8] == SYSEX_TERMINATE)

def _is_sysex_nack(midi_bytes):
    """Return true if the midi_bytes represent a NACK message
       - midi_bytes: incoming MIDI message; sequence of bytes
       - result: bool
    """
    return (len(midi_bytes) == 9) and \
           (midi_bytes[4:6] == E1_SYSEX_NACK) and \
           (midi_bytes[8] == SYSEX_TERMINATE)

def _is_sysex_request_response(midi_bytes):
    """Return true if the midi_bytes represent a sysex request response message
       - midi_bytes: incoming MIDI message; sequence of bytes
       - result: bool
    """
    return (midi_bytes[4:6] == E1_SYSEX_REQUEST_RESPONSE) and \
           (midi_bytes[len(midi_bytes)-1] == SYSEX_TERMINATE)

def _is_sysex_logmessage(midi_bytes):
    """Return true if the midi_bytes represent a sysex log message
       - midi_bytes: incoming MIDI message; sequence of bytes
       - result: bool
    """
    return (midi_bytes[4:6] == E1_SYSEX_LOGMESSAGE) and \
           (midi_bytes[len(midi_bytes)-1] == SYSEX_TERMINATE)

def _is_sysex_patch_request_pressed(midi_bytes):
    """Return true if the midi_bytes represent a sysex patch request
       pressed message (not an official E1 sysex message, but one defined in
       the lua scripts sent with the mixer/device presets, and sent
       when pressing the PATCH REQUEST button on the E1
       - midi_bytes: incoming MIDI message; sequence of bytes
       - result: bool
    """
    return (midi_bytes[4:7] == E1_SYSEX_PATCH_REQUEST_PRESSED) and \
           (midi_bytes[7] == SYSEX_TERMINATE)

# --- ElectraOne class


class ElectraOne(ElectraOneBase):
    """Remote control script for the Electra One. Initialises an
       EffectController that handles the currently selected Effect/Instrument
       and a MixerController that handles the currently selected tracks volumes
       and sends, as well as the global transports and master volume.
    """

    def __init__(self, c_instance):
        check_configuration()
        ElectraOneBase.__init__(self, c_instance)
        # 'close' the interface until E1 detected.
        self._E1_connected = False # do this outside thread because thread may not even execute first statement before finishing
        # start a thread to detect the E1, if found thread will complete the
        # initialisation calling self._mixer_controller = MixerController(c_instance)
        # and self._effect_controller = EffectController(c_instance)
        self.debug(1,'Setting up connection.')
        self._connection_thread = threading.Thread(target=self._connect_E1)
        self._connection_thread.start()
        self.debug(1,'Waiting for connection...')

    def _connect_E1(self):
        """To be called as a thread. Send out request for information
           repeatedly to detect E1. Once detected, complete initialisation
           of the remote script and (re)activate the interface.
        """
        # should anything happen inside this thread, make sure we write to debug
        try:
            if DETECT_E1:
                self.debug(2,'Connection thread: detecting E1...')
                self._request_response_received = False
                self.send_midi(E1_SYSEX_REQUEST)
                time.sleep(0.5)
                # wait until _do_request_response called
                while not self._request_response_received:
                    self.send_midi(E1_SYSEX_REQUEST)
                    time.sleep(0.5)
                self.debug(2,'Connection thread: E1 found')
            else:
                self.debug(2,'Connection thread skipping detection.')
            # complete the initialisation
            c_instance = self.get_c_instance()
            # note: any requests to rebuild the MIDI map triggered by these
            # two calls are ignored because the interface is still closed
            self._mixer_controller = MixerController(c_instance) 
            self._effect_controller = EffectController(c_instance)
            self.log_message('ElectraOne remote script loaded.')
            # re-open the interface
            self._E1_connected = True
            # when opening a song without any devices selected, make sure
            # the MIDI map is built
            if self._effect_controller._assigned_device == None:
                self.request_rebuild_midi_map()                
        except:
            self.debug(1,f'Exception occured {sys.exc_info()}')

    def _reset(self):
        """Reset the remote script.
        """
        # TODO: get a device selected...
        self._E1_connected = True
        ElectraOneBase.preset_uploading = False
        self._effect_controller._assigned_device_locked = False
        self._effect_controller._assigned_device = None
        self._effect_controller._preset_info = None
        self._effect_controller._set_appointed_device(self.song().appointed_device)
     
    def _is_ready(self):
        """Return whether the remote script is ready to process
           request or not (ie whether the E1 is connected and no preset
           upload is in progress.
           - result: bool
        """
        ready = self._E1_connected and not ElectraOneBase.preset_uploading
        # self.debug(6,f'Is ready? {ready} (pu: {ElectraOneBase.preset_uploading}, ar: {ElectraOneBase.ack_received}, rrr: {self._request_response_received})')
        return ready
    
    def suggest_input_port(self):
        """Tell Live the name of the preferred input port name.
           result: str
        """
        return 'Electra Controller (Electra Port 1)'

    def suggest_output_port(self):
        """Tell Live the name of the preferred output port name.
           result: str
        """
        return 'Electra Controller (Electra Port 1)'

    def can_lock_to_devices(self):
        """Live can ask the script whether it can be locked to devices
           result: bool
        """
        return True

    def lock_to_device(self, device):
        """Live can tell the script to lock to a given device
           result: bool
        """
        if self._is_ready():
            self.debug(1,'Main lock to device called.')
            self._effect_controller.lock_to_device(device)
        else:
            self.debug(1,'Main lock ignored because E1 not ready.') 

    def unlock_from_device(self, device):
        """Live can tell the script to unlock from a given device
           result: bool
        """
        if self._is_ready():
            self.debug(1,'Main unlock called.') 
            self._effect_controller.unlock_from_device(device)
        else:
            self.debug(1,'Main unlock ignored because E1 not ready.') 

    def toggle_lock(self):
        """Live can tell the script to toggle the script's lock on devices
        """
        # Weird; why is Ableton relegating this to the script?
        if self._is_ready():
            self.debug(1,'Main toggle lock called.') 
            self.get_c_instance().toggle_lock()
        else:
            self.debug(1,'Main toggle lock ignored because E1 not ready.') 

    def _process_midi_cc(self, midi_bytes):
        """Process incoming MIDI CC message. Ignore if interface not ready.
           - midi_bytes: incoming MIDI CC message; sequence of bytes
        """
        if self._is_ready():
            (status,cc_no,value) = midi_bytes
            midi_channel = status - CC_STATUS + 1
            self._mixer_controller.process_midi(midi_channel,cc_no,value)
        else:
            self.debug(3,'Process MIDI CC ignored because E1 not ready.') 

    def _do_preset_changed(self, midi_bytes):
        """Handle a preset changed message
           - midi_bytes: incoming MIDI SysEx message; sequence of bytes
        """
        selected_slot = midi_bytes[6:8]
        self.debug(3,f'Preset {selected_slot} selected on the E1')
        # process resets even when not ready
        if selected_slot == RESET_SLOT:
            self.debug(1,'Remote script reset requested.')
            ElectraOneBase.current_visible_slot = selected_slot
            self._reset()
        elif self._is_ready():
            if (selected_slot == MIXER_PRESET_SLOT):
                self.debug(3,'Mixer preset selected: starting refresh.')
                ElectraOneBase.current_visible_slot = selected_slot
                self._mixer_controller.refresh_state()
            elif (selected_slot == EFFECT_PRESET_SLOT):  
                self.debug(3,'Effect preset selected: starting refresh.')
                ElectraOneBase.current_visible_slot = selected_slot
                self._effect_controller.refresh_state()
            else:
                self.debug(3,'Other preset selected (ignoring)')                
        else:
            self.debug(3,'Preset changed ignored because E1 not ready.') 

    def _do_ack(self, midi_bytes):
        """Handle an ACK message.
           - midi_bytes: incoming MIDI SysEx message; sequence of bytes
        """
        self.debug(3,f'ACK received (uploading?: {ElectraOneBase.preset_uploading}).')
        ElectraOneBase.ack_received = True
        
    def _do_nack(self, midi_bytes):
        """Handle a NACK message. 
           - midi_bytes: incoming MIDI SysEx message; sequence of bytes
        """
        # TODO: handle NACks
        self.debug(3,f'NACK received (uploading?: {ElectraOneBase.preset_uploading}).')

    def _do_request_response(self, midi_bytes):
        """Handle a request response message: record it as received
           - midi_bytes: incoming MIDI SysEx message; sequence of bytes
        """
        json_bytes = midi_bytes[6:-1] # all bytes after the command, except the terminator byte 
        json_str = ''.join(chr(c) for c in json_bytes)
        self.debug(3,f'Request response received: {json_str}' )
        # json_dict = json.loads(json_str)
        self._request_response_received = True

    def _do_logmessage(self, midi_bytes):
        """Handle a log message: write it to the log file
           - midi_bytes: incoming MIDI SysEx message; sequence of bytes
        """
        text_bytes = midi_bytes[6:-1] # all bytes after the command, except the terminator byte 
        text_str = ''.join(chr(c) for c in text_bytes)
        self.debug(3,f'Log message received: {text_str}' )

    def _do_sysex_patch_request_pressed(self):
        """Handle a patch request pressed message: swap the visible preset
           - midi_bytes: incoming MIDI SysEx message; sequence of bytes
        """
        if self._is_ready():
            self.debug(3,f'Patch request received')
            if ElectraOneBase.current_visible_slot == MIXER_PRESET_SLOT:
                new_slot = EFFECT_PRESET_SLOT
            else:
                new_slot = MIXER_PRESET_SLOT
            # will set ElectraOneBase.current_visible_slot
            # and E1 will send a preset change message in response which will
            # trigger dO_preset_changed() and hence cause a state refresh 
            self._select_preset_slot(new_slot)
            # TODO: really shoudl wait for an ACK! but this is a bit complex
            # because the ACK  is only sent AFTER the preset changed message
            time.sleep(0.5)
        else:
            self.debug(3,'Patch request ignored because E1 not ready.')
        
    def _process_midi_sysex(self, midi_bytes):
        """Process incoming MIDI SysEx message.
           - midi_bytes: incoming MIDI SysEx message; sequence of bytes
        """
        if _is_sysex_preset_changed(midi_bytes):
            self._do_preset_changed(midi_bytes)
        elif _is_sysex_nack(midi_bytes):
            self._do_nack(midi_bytes)
        elif _is_sysex_ack(midi_bytes):
            self._do_ack(midi_bytes)
        elif _is_sysex_request_response(midi_bytes):
            self._do_request_response(midi_bytes)
        elif _is_sysex_logmessage(midi_bytes):
            self._do_logmessage(midi_bytes)
        elif _is_sysex_patch_request_pressed(midi_bytes):
            self._do_sysex_patch_request_pressed()
        else:
            self.debug(5,f'SysEx ignored: { midi_bytes }.')
            
    def receive_midi(self, midi_bytes):
        """MIDI messages are only received through this function, when
           explicitly forwarded in 'build_midi_map' using
           Live.MidiMap.forward_midi_cc().
        """
        self.debug(5,f'Main receive MIDI called. Incoming bytes (first 10): { midi_bytes[:10] }')
        if ((midi_bytes[0] & 0xF0) == CC_STATUS) and (len(midi_bytes) == 3):
            # is a CC
            self._process_midi_cc(midi_bytes)
        elif midi_bytes[0:4] == E1_SYSEX_PREFIX:
            # is a SysEx from the E1
            self._process_midi_sysex(midi_bytes)
        else:
            self.debug(2,'Unexpected MIDI bytes not processed.')

    def build_midi_map(self, midi_map_handle):
        """Build all MIDI maps. Ignore if interface not ready.
        """
        if self._is_ready():
            self.debug(1,'Main build midi map called.') 
            self._effect_controller.build_midi_map(midi_map_handle)
            self._mixer_controller.build_midi_map(self.get_c_instance().handle(),midi_map_handle)
        else:
            self.debug(1,'Main build midi map ignored because E1 not ready.')
        
    def refresh_state(self):
        """Appears to be called by Live when it thinks the state of the
           remote controller needs to be updated. This doesn't appear
           to happen often...  (At least not when devices or tracks are
           added/deleted). Ignore if interface not ready.
        """
        if self._is_ready():
            self.debug(1,'Main refresh state called.') 
            self._effect_controller.refresh_state()
            self._mixer_controller.refresh_state()
        else:
            self.debug(1,'Main refresh state ignored because E1 not ready.')

    def update_display(self):
        """ Called every 100 ms. Ignore if interface not ready.
        """
        if self._is_ready():
            self.debug(6,'Main update display called.') 
            self._effect_controller.update_display()
            self._mixer_controller.update_display()
        else:
            self.debug(6,'Main update display ignored because E1 not ready.')
            
    def connect_script_instances(self,instanciated_scripts):
        """ Called by the Application as soon as all scripts are initialized.
            You can connect yourself to other running scripts here.
        """
        self.debug(1,'Main connect script instances called.') 
        pass

    def disconnect(self):
        """Called right before we get disconnected from Live. Ignore if
           connecting to E1 failed.
        """
        if self._E1_connected:
            self.debug(1,'Main disconnect called.') 
            self._effect_controller.disconnect()
            self._mixer_controller.disconnect()
        else:
            self.debug(1,'Main disconnect ignored because E1 not connected.')


