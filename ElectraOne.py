# ElectraOne
# - Main class, implementing Control Script interface expected by Live
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
from .ElectraOneBase import ElectraOneBase, get_cc_midichannel, is_cc_statusbyte, hexify, ACK_RECEIVED, NACK_RECEIVED
from .EffectController import EffectController
from .MixerController import MixerController
from .DeviceAppointer import DeviceAppointer
from .config import *
from .versioninfo import COMMITDATE

# SysEx defines and helpers

SYSEX_TERMINATE = 0xF7

# SysEx incoming commands (as defined by the E1 firmware)
# All SysEx commands start with E1_SYSEX_PREFIX and are terminated by SYSEX_TERMINATE

E1_SYSEX_PREFIX = (0xF0, 0x00, 0x21, 0x45)

E1_SYSEX_LOGMESSAGE = (0x7F, 0x00) # followed by json data 
E1_SYSEX_PRESET_CHANGED = (0x7E, 0x02)  # followed by bank-number slot-number
E1_SYSEX_ACK = (0x7E, 0x01) # followed by two zero's (reserved) 
E1_SYSEX_NACK = (0x7E, 0x00) # followed by two zero's (reserved)
E1_SYSEX_REQUEST_RESPONSE = (0x01, 0x7F) # followed by json data 

# SysEx incomming command when the PATCH REQUEST button on the E1 has been pressed 
# (User-defined in effect patch LUA script, see DEFAULT_LUASCRIPT in EffectController.py)

E1_SYSEX_PATCH_REQUEST_PRESSED = (0x7E, 0x7E) # no data

# SysEx outgoing commands (as defined by the E1 firmware)

E1_SYSEX_REQUEST = (0xF0, 0x00, 0x21, 0x45, 0x02, 0x7F, 0xF7)

def _match_sysex(midi_bytes,pattern):
    """Match (byte 4 and 5 of) an incoming sysex message with a
       pattern (see constants defined above) to determine its type.
       - midi_bytes: incoming MIDI message; sequence of bytes
       - pattern: pattern to match; sequence of exactly two bytes
       - result: true if matched; bool
    """
    return (midi_bytes[4:6] == pattern) and \
           (midi_bytes[len(midi_bytes)-1] == SYSEX_TERMINATE)


# --- ElectraOne class


class ElectraOne(ElectraOneBase):
    """Remote control script for the Electra One.

       Implements the API Live expects remote control scripts to have.

       Detects whether E1 is present.
    
       Initialises
       - an EffectController that handles the currently selected
         Effect/Instrument, and
       - a MixerController that handles the currently selected tracks volumes
         and sends, as well as the global transports and master volume. 
    """

            
    def __init__(self, c_instance):
        # make sure that all configuration constants make sense
        check_configuration()
        ElectraOneBase.__init__(self, c_instance)
        # 'close' the interface until E1 detected.
        ElectraOneBase.E1_connected = False # do this outside thread because thread may not even execute first statement before finishing
        # start a thread to detect the E1, if found thread will complete the
        # initialisation, setting:
        # - self._mixer_controller = MixerController(c_instance) and
        # - self._effect_controller = EffectController(c_instance)
        # and opening the interface so the remote script becomes active
        self._mixer_controller = None
        self._effect_controller = None
        self.debug(1,f'ElectraOne Remote Script version of { COMMITDATE }.')
        self.debug(1,'Setting up connection.')
        self._connection_thread = threading.Thread(target=self._connect_E1)
        self._connection_thread.start()
        self.debug(1,'Waiting for connection...')
        # connection thread still running of course, so any calls to refresh the
        # state or to rebuild the MIDI map are ignored.
        
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
                # repeatedly request response until it is received 
                # (E1_SYSEX_REQUEST_RESPONSE, see _do_request_response called)
                while not self._request_response_received:
                    self.send_midi(E1_SYSEX_REQUEST)
                    time.sleep(0.5)
                self.debug(2,'Connection thread: E1 found')
            else:
                self.debug(2,'Connection thread skipping detection.')
            # complete the initialisation
            self.setup_fast_sysex()
            self.setup_logging()
            c_instance = self.get_c_instance()
            self.log_message('ElectraOne remote script loaded.')
            # re-open the interface
            ElectraOneBase.E1_connected = True                
            if CONTROL_MODE != CONTROL_EFFECT_ONLY:
                self._mixer_controller = MixerController(c_instance)
            # The upload thread for the appointed device (if any) will request
            # the MIDI map to be rebuilt
            if CONTROL_MODE != CONTROL_MIXER_ONLY:
                self._effect_controller = EffectController(c_instance)
                self._device_appointer = DeviceAppointer(c_instance)
                # if a track and a device is selected it is appointed; a little
                # sleep allows the thread to be interrupted so the appointed
                # device listener registered by EffectController picks up this
                # appointment and sets thge assigned device.
                time.sleep(0.1)
            # initialise the visible prest
            # (the E1 will send a preset changed message in response; this will
            # refresh the state but not rebuild the midi map)
            if CONTROL_MODE == CONTROL_EITHER:
                self._mixer_controller.select()
            elif CONTROL_MODE == CONTROL_EFFECT_ONLY:
                self._effect_controller.select()
            elif CONTROL_MODE == CONTROL_BOTH:
                self._effect_controller.select()
                self._mixer_controller.visible = True
            self.request_rebuild_midi_map()
        except:
            self.debug(1,f'Exception occured {sys.exc_info()}')

    def _reset(self):
        """Reset the remote script.
        """
        # TODO: get a device selected...
        ElectraOneBase.E1_connected = True
        ElectraOneBase.preset_uploading = False
        if self._effect_controller:
            self._effect_controller._assigned_device_locked = False
            self._effect_controller._assigned_device = None
            self._effect_controller._preset_info = None
            self._effect_controller._set_appointed_device(self.song().appointed_device)
     
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
        if self.is_ready() and self._effect_controller:
            self.debug(1,'Main lock to device called.')
            self._effect_controller.lock_to_device(device)
        else:
            self.debug(1,'Main lock ignored because E1 not ready.') 

    def unlock_from_device(self, device):
        """Live can tell the script to unlock from a given device
           result: bool
        """
        if self.is_ready() and self._effect_controller:
            self.debug(1,'Main unlock called.') 
            self._effect_controller.unlock_from_device(device)
        else:
            self.debug(1,'Main unlock ignored because E1 not ready.') 

    def toggle_lock(self):
        """Live can tell the script to toggle the script's lock on devices
        """
        # Weird; why is Ableton relegating this to the script?
        if self.is_ready():
            self.debug(1,'Main toggle lock called.') 
            self.get_c_instance().toggle_lock()
        else:
            self.debug(1,'Main toggle lock ignored because E1 not ready.') 

    def _process_midi_cc(self, midi_bytes):
        """Process incoming MIDI CC message and forward to the
           MixerController only. (EffectController never registers CC_HANDLERS.)
           Ignore if interface not ready.
           - midi_bytes: incoming MIDI CC message; sequence of bytes
        """
        if self.is_ready() and self._mixer_controller:
            (status,cc_no,value) = midi_bytes
            midi_channel = get_cc_midichannel(status)
            self._mixer_controller.process_midi(midi_channel,cc_no,value)
        else:
            self.debug(3,'Process MIDI CC ignored because E1 not ready or mixer not active.') 

    def _do_ack(self, midi_bytes):
        """Handle an ACK message.
           - midi_bytes: incoming MIDI SysEx message; sequence of bytes
        """
        if ElectraOneBase.acks_pending > 0:
            ElectraOneBase.acks_pending -= 1
        ElectraOneBase.ack_or_nack_received = ACK_RECEIVED
        self.debug(3,f'ACK received (acks still pending: {ElectraOneBase.acks_pending}, uploading?: {ElectraOneBase.preset_uploading}).')
        
    def _do_nack(self, midi_bytes):
        """Handle a NACK message. 
           - midi_bytes: incoming MIDI SysEx message; sequence of bytes
        """
        if ElectraOneBase.acks_pending > 0:
            ElectraOneBase.acks_pending -= 1
        ElectraOneBase.ack_or_nack_received = NACK_RECEIVED
        self.debug(3,f'NACK received (acks still pending: {ElectraOneBase.acks_pending}, uploading?: {ElectraOneBase.preset_uploading}).')

    def _do_request_response(self, midi_bytes):
        """Handle a request response message: record it as received
           - midi_bytes: incoming MIDI SysEx message; sequence of bytes
        """
        json_bytes = midi_bytes[6:-1] # all bytes after the command, except the terminator byte 
        json_str = ''.join(chr(c) for c in json_bytes) # convert bytes to a string
        self.debug(3,f'Request response received: {json_str}' )
        # get the version
        json_dict = json.loads(json_str)
        self.set_version(json_dict["versionText"])
        self._request_response_received = True

    def _do_logmessage(self, midi_bytes):
        """Handle a log message: write it to the log file
           - midi_bytes: incoming MIDI SysEx message; sequence of bytes
        """
        text_bytes = midi_bytes[6:-1] # all bytes after the command, except the terminator byte 
        text_str = ''.join(chr(c) for c in text_bytes) # convert bytes to a string
        self.debug(3,f'Log message received: {text_str}' )

    def _do_preset_changed(self, midi_bytes):
        """Handle a preset changed message
           - midi_bytes: incoming MIDI SysEx message; sequence of bytes
        """
        # TODO: deal with selecting slots different than mixer/preset
        # and when in CONTROL_BOTH mode
        selected_slot = midi_bytes[6:8]
        self.debug(3,f'Preset {selected_slot} selected on the E1')
        # premeptively make both controllers invisible when using only one E1
        # (TODO: doesn't work because preset change message is sent on CTRL)
        if self._mixer_controller and (CONTROL_MODE != CONTROL_BOTH): 
            self._mixer_controller.visible = False
        if self._effect_controller and (CONTROL_MODE != CONTROL_BOTH): 
            self._effect_controller.visible = False
        # process resets even when not ready
        # (TODO: doesn't work because preset change message is sent on CTRL)
        if selected_slot == RESET_SLOT:
            self.debug(1,'Remote script reset requested.')
            self._reset()
        # ignore preset switches in CONTROL_BOTH mode
        elif self.is_ready() and (CONTROL_MODE != CONTROL_BOTH):
            if (selected_slot == MIXER_PRESET_SLOT) and self._mixer_controller:
                self.debug(3,'Mixer preset selected: starting refresh.')
                self._mixer_controller.visible = True
                self._mixer_controller.refresh_state()
            elif (selected_slot == EFFECT_PRESET_SLOT) and self._effect_controller:  
                self.debug(3,'Effect preset selected: starting refresh.')
                # TODO: if device not uploaded yet (eg initially)
                # then state not refreshed; somehow code assumes that this
                # function is only called in response to a preset changed
                # message sent after a patch request message (which
                # selects the preset slot and uploads a preset if needed)
                self._effect_controller.visible = True
                self._effect_controller.refresh_state()
            else:
                self.debug(3,'Other preset selected (ignoring)')                
        else:
            self.debug(3,'Preset changed ignored because E1 not ready  or CONTROL_MODE != CONTROL_EITHER.') 

    def _do_sysex_patch_request_pressed(self):
        """Handle a patch request pressed message: swap the visible preset
           - midi_bytes: incoming MIDI SysEx message; sequence of bytes
        """
        # ignore patch request presses when mode is not CONTROL_EITHER
        if self.is_ready() and (CONTROL_MODE == CONTROL_EITHER):
            # if CONTROL_MODE == CONTROL_EITHER both _mixer_controller()
            # and _effect_controller() are guaranteed to exist
            self.debug(3,f'Patch request received')
            if self._mixer_controller.visible:
                # E1 will send a preset change message in response which will
                # trigger do_preset_changed() and hence cause a state refresh.
                # We use that as an implicit ACK.
                self._effect_controller.select()
                self._mixer_controller.visible = False
            else:
                self._mixer_controller.select()
                self._effect_controller.visible = False
        else:
            self.debug(3,'Patch request ignored because E1 not ready or CONTROL_MODE != CONTROL_EITHER.')
        
    def _process_midi_sysex(self, midi_bytes):
        """Process incoming MIDI SysEx message.
           - midi_bytes: incoming MIDI SysEx message; sequence of bytes
        """
        if _match_sysex(midi_bytes,E1_SYSEX_PRESET_CHANGED):
            self._do_preset_changed(midi_bytes)
        elif _match_sysex(midi_bytes,E1_SYSEX_NACK):
            self._do_nack(midi_bytes)
        elif _match_sysex(midi_bytes,E1_SYSEX_ACK):
            self._do_ack(midi_bytes)
        elif _match_sysex(midi_bytes,E1_SYSEX_REQUEST_RESPONSE):
            self._do_request_response(midi_bytes)
        elif _match_sysex(midi_bytes,E1_SYSEX_LOGMESSAGE):
            self._do_logmessage(midi_bytes)
        elif _match_sysex(midi_bytes,E1_SYSEX_PATCH_REQUEST_PRESSED):
            self._do_sysex_patch_request_pressed()
        else:
            self.debug(5,f'SysEx ignored: { hexify(midi_bytes) }.')
            
    def receive_midi(self, midi_bytes):
        """MIDI messages are only received through this function, when
           explicitly forwarded in 'build_midi_map' using
           Live.MidiMap.forward_midi_cc(). Incoming SysExs are always passed
           to this function
           - midi_bytes: the MIDI message; sequence of bytes
        """
        self.debug(5,f'Main receive MIDI called. Incoming bytes (first 10): { hexify(midi_bytes[:10]) }')
        if is_cc_statusbyte(midi_bytes[0]) and (len(midi_bytes) == 3):
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
        if self.is_ready():
            self.debug(1,'Main build midi map called.')
            if self._effect_controller:
                self._effect_controller.build_midi_map(midi_map_handle)
            if self._mixer_controller:
                self._mixer_controller.build_midi_map(self.get_c_instance().handle(),midi_map_handle)
        else:
            self.debug(1,'Main build midi map ignored because E1 not ready.')
        
    def refresh_state(self):
        """Appears to be called by Live when it thinks the state of the
           remote controller needs to be updated. This doesn't appear
           to happen often...  (At least not when devices or tracks are
           added/deleted). Ignore if interface not ready.
        """
        if self.is_ready():
            self.debug(1,'Main refresh state called.')
            if self._effect_controller:
                self._effect_controller.refresh_state()
            if self._mixer_controller:
                self._mixer_controller.refresh_state()
        else:
            self.debug(1,'Main refresh state ignored because E1 not ready.')

    def update_display(self):
        """ Called every 100 ms. Ignore if interface not ready.
        """
        if self.is_ready():
            self.debug(6,'Main update display called.') 
            if self._effect_controller:
                self._effect_controller.update_display()
            if self._mixer_controller:
                self._mixer_controller.update_display()
        else:
            self.debug(6,'Main update display ignored because E1 not ready.')
            
    def connect_script_instances(self,instanciated_scripts):
        """ Called by Live as soon as all scripts are initialized.
            You can connect yourself to other running scripts here.
        """
        self.debug(1,'Main connect script instances called.') 
        pass

    def disconnect(self):
        """Called right before we get disconnected from Live. Ignore if
           connecting to E1 failed.
        """
        if ElectraOneBase.E1_connected:
            self.debug(1,'Main disconnect called.') 
            if self._effect_controller:
                self._effect_controller.disconnect()
            if self._mixer_controller:
                self._mixer_controller.disconnect()
        else:
            self.debug(1,'Main disconnect ignored because E1 not connected.')


