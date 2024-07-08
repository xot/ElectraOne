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

# local imports
from .ElectraOneBase import ElectraOneBase

class PropertyControllers(ElectraOneBase):
    """Manage handlers and listeners for properties
    """

    def __init__(self,c_instance):
        """Initialise.
           - c_instance: Live interface object (see __init.py__)
        """
        ElectraOneBase.__init__(self, c_instance)
        # create empty dictionary of listeners (indexed by property names)
        # used to send value updated as MIDI CC messages when a property
        # cahgnes value, or when refresh_state() is called
        self._LISTENERS = {}
        # create empty dictionary of handlers (indexed by (channel,cc) tuples)
        # used to handle incoming MIDI CC messages that control a property
        # (see process_midi() and build_midi_map()
        self._CC_HANDLERS = {}

    def disconnect(self):
        """Disconnect; remove listeners registered for all properties.
        """
        self.debug(2,'Deregistering property controllers.')
        for property in self._LISTENERS:
            (context,listener) = self._LISTENERS[property]
            if context != None:
                getattr(context,'remove_' + property + '_listener')(listener)

    # -- Genereric properties
    
    def add_property(self,context,property,midi_channel,cc_no,handler,listener):
        """Add an on/off controller for a generic property.
        - context: context of property; eg song or track
        - property: name of on/off property; string
        - midi_channel: MIDI channel; int
        - cc_NO: CC parameter number; int (nothing added if None)
        - handler: handles incoming CC events; function (lambda value: x)
        - listener: listens to property changs and sends CC updates; function (lambda : x)
        """
        if cc_no != None:
            self.debug(2,f'Adding property {property}.')
            # add a cc handler for this property
            if handler != None:
                self._CC_HANDLERS[(midi_channel,cc_no)] = handler
            # add a listener for this property, and store it to remove it
            # later; also used by refresh_state
            if listener != None:
                self._LISTENERS[property] = (context,listener)
                # add the listener now
                getattr(context,'add_' + property + '_listener')(listener)
                
    # -- on/off properties
    
    def _handle_on_off_property(self,context,property,reverse,value):
        self.debug(3,f'Handling incoming {property} event with value {value}.')
        setattr(context,property,reverse ^ (value > 63))


    def _on_off_property_listener(self,context,property,reverse,midi_channel,cc_no):
        value = 127 * (reverse ^ getattr(context,property)) # True = 127; False = 0
        self.debug(4,f'{property} changed. Sending value {value}.')
        self.send_midi_cc7(midi_channel, cc_no, value)

    def add_on_off_property(self,context,property,midi_channel,cc_no,reverse=False):
        """Add an on/off controller for a binary property controlled by a button
           on the E1, with specified channel and cc. CC value 127=on, 0=off.
        - context: context of property; eg song or track
        - property: name of on/off property; string
        - MIDI_channel: MIDI channel; int
        - cc_no: CC parameter number; int (nothing added if None)
        - reverse: whether to reverse the value/state; boolean
        """
        handler = (lambda value: self._handle_on_off_property(context,property,reverse,value))
        listener = (lambda : self._on_off_property_listener(context,property,reverse,midi_channel,cc_no))
        self.add_property(context,property,midi_channel,cc_no,handler,listener)
            
    # -- list properties
    
    def _handle_list_property(self,context,property,translation,value):
        if translation != None:
            value = translation[value]
        self.debug(3,f'Handling incoming {property} event with value {value}.')
        setattr(context,property,value)


    def _list_property_listener(self,context,property,translation,midi_channel,cc_no):
        value = getattr(context,property) 
        if translation != None:
            value = translation.index(value)
        self.debug(3,f'{property} changed. Sending value {value}.')
        self.send_midi_cc7(midi_channel, cc_no, value)

    def add_list_property(self,context,property,midi_channel,cc_no,translation = None):
        """Add a list controller for a list property on the E1, with specified
           channel and cc. 
        - context: context of property; eg song or track
        - property: name of list property; string
        - midi_channel: MIDI channel; int
        - cc_no: CC parameter number; int (nothing added if None)
        - translation: optional translation from MIDI CC values to property values; list
        """
        handler = (lambda value: self._handle_list_property(context,property,translation,value))
        listener = (lambda : self._list_property_listener(context,property,translation,midi_channel,cc_no))
        self.add_property(context,property,midi_channel,cc_no,handler,listener)

    # --
    
    def refresh_state(self):
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
            self.debug(5,f'Property controller: handler found for CC {cc_no} on MIDI channel {midi_channel}.')
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
        self.debug(2,'Building property controllers MIDI map.')
        # Map CCs to be forwarded as defined in self._CC_HANDLERS
        for (midi_channel,cc_no) in self._CC_HANDLERS:
            self.debug(3,f'PropertyControllers: setting up handler for CC {cc_no} on MIDI channel {midi_channel}')
            Live.MidiMap.forward_midi_cc(script_handle, midi_map_handle, midi_channel - 1, cc_no)
        
