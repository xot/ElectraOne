# ElectraOne
# - Main class, implementing Control Script interface expected by Live
#
# Ableton Live MIDI Remote Script for the Electra One
#
# Author: Jaap-henk Hoepman (info@xot.nl)
#
# Distributed under the MIT License, see LICENSE
#

import Live

# Python imports
import json
import threading
import time
import sys

# Local imports
from .E1Midi import parse_cc, is_cc, parse_E1_sysex, is_E1_sysex, hexify, E1_SYSEX_LOGMESSAGE, E1_SYSEX_PRESET_CHANGED, E1_SYSEX_ACK, E1_SYSEX_NACK, E1_SYSEX_REQUEST_RESPONSE, E1_SYSEX_PATCH_REQUEST_PRESSED 
from .ElectraOneBase import ElectraOneBase, ACK_RECEIVED, NACK_RECEIVED
from .EffectController import EffectController
from .MixerController import MixerController
from .DeviceAppointer import DeviceAppointer
from .Devices import Devices
from .config import *
from .versioninfo import COMMITDATE

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
        self.debug(0,f'ElectraOne Remote Script version of { COMMITDATE }.')
        # set live version
        live_major_version = Live.Application.get_application().get_major_version()
        live_minor_version = Live.Application.get_application().get_minor_version()
        live_bugfix_version = Live.Application.get_application().get_bugfix_version()
        ElectraOneBase.LIVE_VERSION = (live_major_version,live_minor_version,live_bugfix_version)
        self.debug(1,f'Live version {ElectraOneBase.LIVE_VERSION}.')
        # load information about predefined devices and the default LUA script
        # (We do this here because at this point in time the remote script
        # gets more resources to initialise, apparently.)
        self.devices = Devices(c_instance)
        # 'close' the interface until E1 detected.
        ElectraOneBase.E1_connected = False # do this outside thread because
        # thread may not even execute first statement before finishing
        #
        # start a thread to detect the E1, if found thread will complete the
        # initialisation, setting:
        # - self._mixer_controller = MixerController(c_instance) and
        # - self._effect_controller = EffectController(c_instance,self.devices)
        # and opening the interface so the remote script becomes active
        self._mixer_controller = None
        self._effect_controller = None
        self.debug(0,'Setting up connection.')
        self._connection_thread = threading.Thread(target=self._connect_E1)
        self._connection_thread.start()
        self.debug(0,'Waiting for connection...')
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
                sleep = 0.5
                attempts = 0
                self.debug(2,'Connection thread: detecting E1...')
                self._request_response_received = False
                # repeatedly request response until it is received 
                # (E1_SYSEX_REQUEST_RESPONSE, see _do_request_response called)
                # Note that the 1st response to this request is sent back
                # immediately but not caught by the remote script
                #  (this is because the init() isnt finished yet!)
                # stop trying after 30 times
                #
                # note that _do_request_response_called() sets the firmware and hardware version
                while (not self._request_response_received) and (attempts < 30):
                    self.send_e1_request()
                    time.sleep(sleep)
                    sleep = sleep*1.5 # sleep progressively longer
                    attempts +=1 
                if not self._request_response_received:
                    self.debug(2,'Connection thread aborts detection.')
                    return
                self.debug(2,'Connection thread detected an E1.')
            else:
                self.debug(2,'Connection thread skipping detection.')
            if DETECT_E1 and not ElectraOneBase.E1_version_supported:
                self.debug(2,'Connection thread: this E1 not supported.')
                return
            # complete the initialisation
            self.setup_fast_sysex()
            self.setup_logging()
            c_instance = self.get_c_instance()
            if CONTROL_MODE != CONTROL_EFFECT_ONLY:
                self._mixer_controller = MixerController(c_instance)
            # The upload thread for the appointed device (if any) will request
            # the MIDI map to be rebuilt
            if CONTROL_MODE != CONTROL_MIXER_ONLY:
                self._effect_controller = EffectController(c_instance,self.devices)
                self._device_appointer = DeviceAppointer(c_instance)
                # if a track and a device is selected it is appointed; a little
                # sleep allows the thread to be interrupted so the appointed
                # device listener registered by EffectController picks up this
                # appointment and sets the assigned device. TODO: this does
                # not always work!
                # Note: the interface is still closed, so no actual uploading
                # will take place yet.
                time.sleep(0.1)
            self.log_message('ElectraOne remote script loaded.')
            # re-open the interface
            ElectraOneBase.E1_connected = True                
            # initialise the visible prest
            # (the E1 will send a preset changed message in response; this will
            # refresh the state but not rebuild the midi map)
            if (CONTROL_MODE == CONTROL_MIXER_ONLY) or \
               ((CONTROL_MODE == CONTROL_EITHER) and \
                not (SWITCH_TO_EFFECT_IMMEDIATELY and \
                    (self._effect_controller._assigned_device != None))):
                self._mixer_controller.select()
            else:
                self._effect_controller.select()
            self.request_rebuild_midi_map()
        except:
            self.debug(1,f'Exception occured {sys.exc_info()}')

    def _reset(self):
        """Reset the remote script.
        """
        ElectraOneBase.E1_connected = True
        ElectraOneBase.preset_uploading = False
        if self._effect_controller:
            self._effect_controller._assigned_device_locked = False
            self._effect_controller._assigned_device = None
            self._effect_controller._preset_info = None
            self._effect_controller._handle_appointed_device_change()
     
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

    def suggest_map_mode(self, cc_no, channel):
        """Live can ask the script to suggest a map mode for the given CC
        """
        self.debug(5,f'Asking MIDI map mode suggestion for {channel}:{cc_no}.')
        return Live.MidiMap.MapMode.absolute
    
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

    def _process_midi_cc(self, midimsg):
        """Process incoming MIDI CC message and forward to the
           MixerController only. (EffectController never registers CC_HANDLERS.)
           Ignore if interface not ready.
           - midimsg: incoming MIDI CC message; sequence of bytes
        """
        self.debug(2,'Processing incoming CC.')
        if self.is_ready() and self._mixer_controller:
            (channel,cc_no,value) = parse_cc(midimsg)
            self._mixer_controller.process_midi(channel,cc_no,value)
        else:
            self.debug(3,'Process MIDI CC ignored because E1 not ready or mixer not active.') 

    def _do_ack(self):
        """Handle an ACK message.
        """
        if ElectraOneBase.acks_pending > 0:
            ElectraOneBase.acks_pending -= 1
            self.debug(3,f'ACK received (acks still pending: {ElectraOneBase.acks_pending}, uploading?: {ElectraOneBase.preset_uploading}).')
        else:
            self.debug(1,f'Warning: Unexpected ACK received, uploading?: {ElectraOneBase.preset_uploading}).')            
        ElectraOneBase.ack_or_nack_received = ACK_RECEIVED
        
    def _do_nack(self):
        """Handle a NACK message. 
        """
        if ElectraOneBase.acks_pending > 0:
            ElectraOneBase.acks_pending -= 1
            self.debug(3,f'NACK received (acks still pending: {ElectraOneBase.acks_pending}, uploading?: {ElectraOneBase.preset_uploading}).')
        else:
            self.debug(1,f'Warning: Unexpected NACK received, uploading?: {ElectraOneBase.preset_uploading}).')
        ElectraOneBase.ack_or_nack_received = NACK_RECEIVED

    def _do_request_response(self, json_bytes):
        """Handle a request response message: record it as received
           - json_bytes: incoming MIDI SysEx data; sequence of bytes
        """
        json_str = ''.join(chr(c) for c in json_bytes) # convert bytes to a string
        self.debug(3,f'Request response received: {json_str}' )
        # get the version
        json_dict = json.loads(json_str)
        self.set_version(json_dict["versionSeq"],json_dict["hwRevision"])
        self._request_response_received = True

    def _do_logmessage(self, text_bytes):
        """Handle a log message: write it to the log file
           - text_bytes: incoming MIDI SysEx data; sequence of bytes
        """
        text_str = ''.join(chr(c) for c in text_bytes) # convert bytes to a string
        self.debug(3,f'Log message received: {text_str}' )

    def _do_preset_changed(self, selected_slot):
        """Handle a preset changed message
           - selected_slot: incoming MIDI SysEx data; sequence of 2 bytes
        """
        assert len(selected_slot) == 2, f'Wrong data {selected_slot} in preset changed message.'
        self.debug(3,f'Preset {selected_slot} selected on the E1')
        ElectraOneBase.current_visible_slot = selected_slot
        if selected_slot == RESET_SLOT:
            self.debug(1,'Remote script reset requested.')
            self._reset()
        # ignore preset switches in CONTROL_BOTH mode
        elif self.is_ready() and (CONTROL_MODE != CONTROL_BOTH):
            if (selected_slot == MIXER_PRESET_SLOT) and self._mixer_controller:
                self.debug(3,'Mixer preset selected: starting refresh.')
                self._mixer_controller.refresh_state()
            elif (selected_slot == EFFECT_PRESET_SLOT) and self._effect_controller:  
                self.debug(3,'Effect preset selected: starting refresh.')
                self._effect_controller.refresh_state()
            else:
                self.debug(3,'Other preset selected (ignoring)')
        else:
            self.debug(3,'Preset changed ignored because E1 not ready or CONTROL_MODE != CONTROL_EITHER.') 

    def _do_sysex_patch_request_pressed(self):
        """Handle a patch request pressed message: swap the visible preset
           - midimsg: incoming MIDI SysEx message; sequence of bytes
        """
        # ignore patch request presses when mode is not CONTROL_EITHER
        if self.is_ready() and (CONTROL_MODE == CONTROL_EITHER):
            # if CONTROL_MODE == CONTROL_EITHER both _mixer_controller()
            # and _effect_controller() are guaranteed to exist
            self.debug(3,f'Patch request received')
            if (ElectraOneBase.current_visible_slot == MIXER_PRESET_SLOT): 
                # E1 will send a preset change message in response which will
                # trigger do_preset_changed() and hence cause a state refresh.
                # We use that as an implicit ACK.
                self._effect_controller.select()
            else:
                self._mixer_controller.select()
        else:
            self.debug(3,'Patch request ignored because E1 not ready or CONTROL_MODE != CONTROL_EITHER.')
        
    def _process_midi_sysex(self, midimsg):
        """Process incoming MIDI SysEx message.
           - midimsg: incoming MIDI SysEx message; sequence of bytes
        """
        self.debug(2,'Processing incoming SysEx.')
        (command,data) = parse_E1_sysex(midimsg)
        if command == E1_SYSEX_PRESET_CHANGED:
            self._do_preset_changed(data)
        elif command == E1_SYSEX_NACK:
            self._do_nack()
        elif command ==E1_SYSEX_ACK:
            self._do_ack()
        elif command == E1_SYSEX_REQUEST_RESPONSE:
            self._do_request_response(data)
        elif command == E1_SYSEX_LOGMESSAGE:
            self._do_logmessage(data)
        elif command == E1_SYSEX_PATCH_REQUEST_PRESSED:
            self._do_sysex_patch_request_pressed()
        else:
            self.debug(5,f'SysEx ignored: { hexify(midimsg) }.')
            
    def receive_midi(self, midimsg):
        """MIDI messages are only received through this function, when
           explicitly forwarded in 'build_midi_map' using
           Live.MidiMap.forward_midi_cc(). Incoming SysExs are always passed
           to this function
           - midimsg: the MIDI message; sequence of bytes
        """
        self.debug(1,'Main receive MIDI called.')
        self.debug(5,f'Main receive MIDI called. Incoming bytes (first 10): { hexify(midimsg[:10]) }')
        if is_cc(midimsg):
            self._process_midi_cc(midimsg)
        elif is_E1_sysex(midimsg):
            self._process_midi_sysex(midimsg)
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
            # TODO: make sure request is processed at some point

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
        """Called right before we get disconnected from Live.
        """
        self.debug(1,'Main disconnect called.') 
        if ElectraOneBase.E1_connected:
            if self._effect_controller:
                self._effect_controller.disconnect()
            if self._mixer_controller:
                self._mixer_controller.disconnect()
        else:
            # TODO: kill possibly still running E1 detection thread here
            # (but this is apparently not easy, so we leave it for now.)
            pass


