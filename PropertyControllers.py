# PropertyControllers
# - manage handlers and listeners for properties
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

class PropertyControllers:
    """Manage handlers and listeners for properties
    """

    def __init__(self,controller):
        self._LISTENERS = {}
        self._CC_HANDLERS = {}
        self._controller = controller

    def remove_listeners(self):
        self._controller.debug(3,'Deregistering property controllers.')
        for property in self._LISTENERS:
            (context,listener) = self._LISTENERS[property]
            if context != None:
                getattr(context,'remove_' + property + '_listener')(listener)

    # -- on/off properties
    
    def handle_on_off_property(self,context,property,reverse,value):
        self._controller.debug(3,f'Handling incoming {property} event with value {value}.')
        setattr(context,property,reverse ^ (value > 63))


    def on_off_property_listener(self,context,property,reverse,midi_channel,cc_no):
        value = 127 * (reverse ^ getattr(context,property)) # True = 127; False = 0
        self._controller.debug(3,f'{property} changed. Sending value {value}.')
        self._controller.send_midi_cc7(midi_channel, cc_no, value)

    def add_on_off_property(self,context,property,midi_channel,cc_no,reverse=False):
        """Add an on/off controller for a binary property controlled by a button
           on the E1, with specified channel and cc. CC value 127=on, 0=off.
        - controller: controller managing the property; subclass of ElecraOneBase
        - context: context of property; eg song or track
        - property: name of on/off property; string
        - channel: MIDI channel; int
        - cc: CC no; int
        - reverse: whether to reverse the value/stte; boolean
        """
        if cc_no != None:
            # add a cc handler for this property
            self._CC_HANDLERS[(midi_channel,cc_no)] = (lambda value: self.handle_on_off_property(context,property,reverse,value))
            # create a listener for this property
            listener = (lambda : self.on_off_property_listener(context,property,reverse,midi_channel,cc_no))
            # store it to remove it later and for refresh_state
            self._LISTENERS[property] = (context,listener)
            # add the listener now
            getattr(context,'add_' + property + '_listener')(listener)

    # -- list properties
    
    def handle_list_property(self,context,property,translation,value):
        if translation != None:
            value = translation[value]
        self._controller.debug(3,f'Handling incoming {property} event with value {value}.')
        setattr(context,property,value)


    def list_property_listener(self,context,property,translation,midi_channel,cc_no):
        value = getattr(context,property) # True = 127; False = 0
        if translation != None:
            value = translation.index(value)
        self._controller.debug(3,f'{property} changed. Sending value {value}.')
        self._controller.send_midi_cc7(midi_channel, cc_no, value)

    def add_list_property(self,context,property,midi_channel,cc_no,translation = None):
        """Add a list controller for a list property on the E1, with specified
           channel and cc. 
        - controller: controller managing the property; subclass of ElecraOneBase
        - context: context of property; eg song or track
        - property: name of list property; string
        - channel: MIDI channel; int
        - cc: CC no; int
        - translation: optional translation; list
        """
        if cc_no != None:
            # add a cc handler for this property
            self._CC_HANDLERS[(midi_channel,cc_no)] = (lambda value: self.handle_list_property(context,property,translation,value))
            # create a listener for this property
            listener = (lambda : self.list_property_listener(context,property,translation,midi_channel,cc_no))
            # store it to remove it later and for refresh
            self._LISTENERS[property] = (context,listener)
            # add the listener now
            getattr(context,'add_' + property + '_listener')(listener)
            
    def refresh(self):
        """Refresh the state of all registered properties on the E1
        """
        for property in self._LISTENERS:
            (context,listener) = self._LISTENERS[property]
            listener()

    def process_midi(self, midi_channel, cc_no, value):
        """Process incoming MIDI CC events for the properties registered here,
           if it matches any of them.
           - midi_channel: MIDI channel of incomming message; int (1..16)
           - cc_no: MIDI CC number; int (0..127)
           - value: incoming CC value; int (0..127)
           - returns: whether midi event processed by handler here; bool
        """
        if (midi_channel,cc_no) in self._CC_HANDLERS:
            self._controller.debug(5,f'Property controller: handler found for CC {cc_no} on MIDI channel {midi_channel}.')
            handler = self._CC_HANDLERS[(midi_channel,cc_no)]
            handler(value)
            return True
        else:
            return False

    def build_midi_map(self, script_handle, midi_map_handle):
        """Map all property controls on their associated MIDI CC numbers; make sure
           the right MIDI CC messages are forwarded to the remote script to be
           handled by the MIDI CC handlers defined here.
           - script_handle: reference to the main remote script class
               (whose receive_midi method will be called for any MIDI CC messages
               marked to be forwarded here)
           - midi_map_hanlde: MIDI map handle as passed to Ableton Live, to
               which MIDI mappings must be added.
        """
        self._controller.debug(3,'Building property controllers MIDI map.')
        # Map CCs to be forwarded as defined in MIXER_CC_HANDLERS
        for (midi_channel,cc_no) in self._CC_HANDLERS:
            self._controller.debug(4,f'PropertyControllers: setting up handler for CC {cc_no} on MIDI channel {midi_channel}')
            Live.MidiMap.forward_midi_cc(script_handle, midi_map_handle, midi_channel - 1, cc_no)
        
