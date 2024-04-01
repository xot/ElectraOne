# CCInfo
# - class to store information about a CC control 
#
# Part of ElectraOne.
#
# Ableton Live MIDI Remote Script for the Electra One
#
# Author: Jaap-henk Hoepman (info@xot.nl)
#
# Distributed under the MIT License, see LICENSE

# Boolean flag values indicating 7bit or 14bit CC parameters
IS_CC7 = False
IS_CC14 = True

# dummy CC parameter value to represent an unmapped CC
UNMAPPED_CC = -1

# Python imports
import ast

# local imports
from .config import MIDI_EFFECT_CHANNEL, UNMAPPED_ID
from .UniqueParameters import make_device_parameters_unique

class CCInfo:
    """Class storing the channel and parameter number of a CC mapping, and
       whether the associated controller on the E1 is 14bit (or not, in
       which case it is 7bit). Also records the index of that controller in
       the E1 preset.
    """

    def __init__(self, v):
        """Initialise with a tuple
           (control_id, MIDI_channel, is_cc14?, CC_parameter_no).
           Where is_cc14? is IS_CC7 when the parameter is 7bit, IS_CC14 if 14bit.
           Constructing from a tuple instead of a list of parameters, to allow
           Devices.py to contain plain tuples in the cc_map.
        
           control_id is either an integer (for plain controls) or a tuple
           (control_id,value_id) for controls that are part of an ADSR or
           similar. Internally always stored as a tuple, with value_id == 0
           for non-ADSR controls
        """
        assert type(v) is tuple, f'{v} should be tuple but is {type(v)}'
        (id, self._midi_channel, self._is_cc14, self._cc_no) = v
        if type(id) is int:
            assert id in range(-1,443), f'Control index {id} out of range.'
            self._control_id = (id,0)
        else:
            assert type(id) is tuple, f'Control id {id} should be an integer or a tuple.'
            (cid,vid) = id
            assert cid in range(-1,443), f'Control index {cid} out of range.'
            assert vid in range(11), f'Value index {vid} out of range.'
            self._control_id = id
        assert self._midi_channel in range(1,17), f'MIDI channel {self._midi_channel} out of range.'
        assert self._is_cc14 in [IS_CC7,IS_CC14], f'CC14 flag {self._is_cc14} out of range.'
        assert self._cc_no in range(-1,128), f'CC parameter number {self._cc_no} out of range.'
        
    def __repr__(self):
        """Return a string representation of CCInfo as a tuple of its values.
        """
        return f'({self._control_id},{self._midi_channel},{self._is_cc14},{self._cc_no})'
        
    def get_midi_channel(self):
        """Return the MIDI channel this object is mapped to (undefined if not mapped)
           - result: channel; int (1..16)
        """
        return self._midi_channel

    def is_cc14(self):
        """Return whether the object represents a 7 or 14 bit CC parameter 
           (undefiend when not mapped).
           - result: IC_CC14/True if 14 bit; ID_CC7/False if 7 bit;  bool
        """
        return self._is_cc14

    def get_cc_no(self):
        """Return the CC parameter number of this object.
           - result: the CC parameter number (-1 if not mapped); int (-1..127)
        """
        return self._cc_no

    def set_cc_no(self,cc_no):
        """Set the CC parameter number of this object.
           - cc_no: the CC parameter number (-1 if not mapped); int (-1..127)
        """
        assert cc_no in range(-1,128), f'CC-no out of range {cc_no}.'
        self._cc_no = cc_no
    
    def get_control_id(self):
        """Return the E1 preset control id of this object; always returned as a tuple!.
           - result: the control id; tuple (int,int) 
             If (-1,dc) then E1 will locally generate value to display; otherwise
             Ableton is expected to send value string to display
        """
        return self._control_id

    def set_control_id(self,id):
        """Set the E1 preset control id of this object.
           - id: value to set control id to; tuple of int,int
             If (-1,dc) then E1 will locally generate value to display; otherwise
             Ableton is expected to send value string to display
        """
        assert type(id) is tuple, f'Control id {id} should be tuple.'
        (cid,vid) = id
        assert cid in range(-1,443), f'Control index {cid} out of range.'
        assert vid in range(11), f'Value index {vid} out of range.'
        self._control_id = id

    def is_mapped(self):
        """Return whether object is mapped to a CC parameter at all.
           - result: whether mapped or not ; bool
        """
        return self._cc_no != UNMAPPED_CC

# CCInfo object for an unmapped parameter
UNMAPPED_CCINFO = CCInfo((UNMAPPED_ID,MIDI_EFFECT_CHANNEL,IS_CC7,UNMAPPED_CC))


class CCMap ( dict ) :
    """Class storing a CC map: a dictionary indexed by parameter.original_name
       returning the CCInfo for this parameter.
    """

    def __init__(self,cc_map):
        """Initialise from a dictionary mapping parameter.original_name to CCInfo
           - cc_map: dictionary; dict
        """
        # Parse first into a dictionary if cc_map is a string
        if type(cc_map) is str:
            cc_map = ast.literal_eval(cc_map)
        # we could simply do dict.__init__(self,cc_map), but this is safer, checking
        # all entries in the dict
        dict.__init__(self,{})
        for par_name in cc_map:
            value = cc_map[par_name]
            # skip None entries
            if value != None:                
                if type(value) is tuple:
                    ccinfo = CCInfo(value)
                else:
                    assert type(value) == CCInfo, f'{value} should be of type CCInfo'
                    ccinfo = value 
                self[par_name] = ccinfo

    def map(self,parameter,ccinfo):
        """Map the parameter using ccinfo
           - parameter: Ableton Live parameter; Live.DeviceParameter.DeviceParameter
           - ccinfo: ; CCInfo
        """
        assert (parameter.original_name not in self), f'Map: {parameter.original_name} already mapped'
        assert type(ccinfo) == CCInfo, f'{ccinfo} should be of type CCInfo'
        self[parameter.original_name] = ccinfo

    def map_name(self,parameter_name,ccinfo):
        """Map the parameter name using ccinfo
           - parameter_name: string
           - ccinfo: ; CCInfo
        """
        assert (parameter_name not in self), f'Map: {parameter_name} already mapped'
        assert type(ccinfo) == CCInfo, f'{ccinfo} should be of type CCInfo'
        self[parameter_name] = ccinfo
        
    def update(self,parameter,ccinfo):
        """Update the parameter using ccinfo
           - parameter: Ableton Live parameter; Live.DeviceParameter.DeviceParameter
           - ccinfo: ; CCInfo
        """
        assert (parameter.original_name in self), f'Update: {parameter.original_name} not yet mapped'
        assert type(ccinfo) == CCInfo, f'{ccinfo} should be of type CCInfo'
        self[parameter.original_name] = ccinfo

    def is_mapped(self,parameter):
        """Return whether the parameter is mapped in this CC map
           - parameter: Ableton Live parameter; Live.DeviceParameter.DeviceParameter
           - result: whether mapped or not; bool
        """
        return (parameter.original_name in self)
    
    def get_cc_info(self,parameter):
        """Return the MIDI CC parameter info assigned to the device parameter
           - parameter: Ableton Live parameter; Live.DeviceParameter.DeviceParameter
           - result: a CCInfo object describing the assignment, or
             UNMAPPED_CCINFO if not mapped.
        """
        if parameter.original_name in self:
            v = self[parameter.original_name]
            assert type(v) == CCInfo, f'{v} should be of type CCInfo'
            return v 
        else:
            return UNMAPPED_CCINFO

    def validate(self, device, device_name, warning):
        """Check for internal consistency of ccmap and warn for any unmapped
           or badly mapped parameters;
           this may (for example) indicate that Live added or renamed
           parameters the last time a preset was constructed 
           (Note that there are actually valid reasons to have several device
            parameters mapped to the same control/CC)
           - device: device to which this CCMap belongs
           - device_name: name of the device
           - warning: function to call to write any warnings
        """
        # check CC map consistency
        seen = []
        for cc_info in self.values():
            channel = cc_info.get_midi_channel()
            if channel not in range(1,17):
                warning(f'Bad MIDI channel {channel} in CC map.')
            cc_no = cc_info.get_cc_no()
            if cc_no not in range(0,128):
                warning(f'Bad MIDI CC parameter {cc_no} in CC map.')
            seeing = (channel, cc_no)
            if seeing in seen:
                warning(f'Duplicate {seeing} in CC map.')
            else:
                seen.append(seeing)
        # check parameter mappings
        device_parameters = make_device_parameters_unique(device)
        pnames = [p.original_name for p in device_parameters]
        ccnames = self.keys()
        for name in pnames:
            if not name in ccnames:
                warning(f'Unmapped parameter {name} found for {device_name}!')
        for name in ccnames:
            if not name in pnames:
                warning(f'Mapped parameter {name} does not exist for {device_name}!')
