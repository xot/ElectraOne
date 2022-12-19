# ElectrOneDumper
# - code to construct E1 presets for an Ableton Live device on the fly 
#
# Part of ElectraOne.
#
# Ableton Live MIDI Remote Script for the Electra One
#
# Author: Jaap-henk Hoepman (info@xot.nl)
#
# Distributed under the MIT License, see LICENSE
#
# DOCUMENTATION:
#
# By default all quantized parameters use 7-bit absolute CC values
# while all non quantized parameters (ie faders) are assigned
# 14-bit absolute values. This is the way presets are dumped.
#
# However, when loading user-cureated presets (eg the ones stored in
# Devices.py), this assignment can be overridden using the cc-map. 
#
# Parameters with only on or off values do not get an overlay and are
# represented on the ElectraOne as (toggle) pads.
#
# Other quantised parameters are represented on the ElectraOne as lists, for
# which a separate overlay with all possible values is created.
#
# Note that the CC map serves two different goals: in a *dumped* preset, you
# want to have *all* parameters even those without a CC map; but in a preset
# you *upload* you only want to include parameters that are actually mapped
# in order not to surprise the users).
# Currently, the CC-map contains *all* parameters (also unmapped ones,
# indicated by None) while the on-the-fly constructed preset uploaded to the
# E1 does not contain them. 

# Note: parameter.name used as the visible name for a parameter, and
# parameter.original_name used to index cc_map (because .original_name
# is guaranteed not to change so mappings remain consistent).


# Python imports
import io, random, string

# Ableton Live imports
from _Generic.Devices import *

# Local imports
from .config import *
from .ElectraOneBase import ElectraOneBase, cc_value_for_item_idx
from .CCInfo import CCInfo, UNMAPPED_CC, UNMAPPED_ID, IS_CC7, IS_CC14
from .PresetInfo import PresetInfo

# --- constants

# Electra One MIDI Port to use
MIDI_PORT = 1

# Electra One JSON file format version constructed 
VERSION = 2

# ElectraOne display parameters
PARAMETERS_PER_PAGE = 3 * 12
CONTROLSETS_PER_PAGE = 3
SLOTS_PER_ROW = 6

# Bounds constants: the width and height of a control on the ElectraOne display
WIDTH = 146
HEIGHT = 56
XCOORDS = [0,170,340,510,680,850]
YCOORDS = [40,128,216,304,392,480]

# maximum values in a preset
MAX_NAME_LEN = 14
MAX_DEVICE_ID = 16
MAX_ID = 432
MAX_PAGE_ID = 12
MAX_OVERLAY_ID = 51
MAX_CONTROLSET_ID = CONTROLSETS_PER_PAGE
MAX_POT_ID = (PARAMETERS_PER_PAGE // CONTROLSETS_PER_PAGE)


# Devices for which to ignore ORDER_DEVICEDICT
# e.g. racks, or else any mapped macros will not be shown in a generated preset
ORDER_DEVICEDICT_IGNORE = ['AudioEffectGroupDevice',
                      'MidiEffectGroupDevice',
                      'InstrumentGroupDevice',
                      'DrumGroupDevice']

# Devices for which to ignore ORDER_SORTED
# e.g. racks, or else order of mapped macros will not correspond with order
# in Live
ORDER_SORTED_IGNORE = ['AudioEffectGroupDevice',
                      'MidiEffectGroupDevice',
                      'InstrumentGroupDevice',
                      'DrumGroupDevice']

# --- output sanity checks

# check/truncate name
def _check_name(name):
    # TODO log truncation
    return name[:MAX_NAME_LEN]

def _check_id(id):
    assert (1 <= id) and (id <= MAX_ID), f'{ id } exceeds max number of IDs ({ MAX_ID }).'
    return id

def _check_deviceid(id):
    assert (1 <= id) and (id <= MAX_DEVICE_ID), f'{ id } exceeds max number of device IDs ({ MAX_DEVICE_ID }).'
    return id

def _check_midichannel(channel):
    assert channel in range(1,17), f'MIDI channel { channel } not in range.'
    return channel

def _check_pageid(id):
    assert (1 <= id) and (id <= MAX_PAGE_ID), f'{ id } exceeds max number of pages ({ MAX_PAGE_ID }).'
    return id

def _check_overlayid(id):
    assert (1 <= id) and (id <= MAX_OVERLAY_ID), f'{ id } exceeds max number of overlays ({ MAX_OVERLAY_ID }).'
    return id

# This is more strict than the Electra One documentation requires
def _check_controlset(id):
    assert (1 <= id) and (id <= MAX_CONTROLSET_ID), f'{ id } exceeds max number of controlsets ({ MAX_CONTROLSET_ID }).'
    return id

def _check_pot(id):
    assert id in range(1,MAX_POT_ID+1), f'{ id } exceeds max number of pots ({ MAX_POT_ID }).'
    return id
    

# --- utility functions

def device_idx_for_midi_channel(midi_channel):
    """Return the device id to use in the preset for the specified MIDI channel
       (deviceId 1 contains the first (lowest) MIDI channel).
    """
    return 1 + midi_channel - MIDI_EFFECT_CHANNEL

def _is_on_off_parameter(p):
    """Return whether the parameter has the values "Off" and "On" only.
        - p: parameter; Live.DeviceParameter.DeviceParameter
    """
    if not p.is_quantized:
        return False
    values = p.value_items
    if (len(values) != 2):
        return False
    else:
        return ( (str(values[0]) == "Off") and (str(values[1]) == "On"))

def _needs_overlay(p):
    """Return whether the parameter needs an overlay to be generated
       (that enumerates all the values in the list, and that will be attached
       to the parameter in the 'controls' section of the same parameter.
        - p: parameter; Live.DeviceParameter.DeviceParameter
    """
    return p.is_quantized and (not _is_on_off_parameter(p))

# --- functions to determine fader types

# The only reliable way to determine the type and the range of values for
# a parameter is to use Ableton's str_for_value function. This function
# returns a string with the following structure
#   <valuestring><space><valuetype>.
# Untyped values only return
#   <valuestring>.
# Examples:
# 100 %
# -4.00
# 5 ms
# On
# -inf dB
# 3.7 Hz
#
# Note: Sometimes the space separator is missing.
# Pan values are written 50L.. 50R *without* the space; the same is true
# for phase parameters, e.g. 360°; I've also seen 22.0k for kHz
def _get_par_value_info(p,v):
    """ Return the number part and its type for value v of parameter p
        (using the string representation of the value of a parameter as
        reported by Ableton)
        - p: parameter; Live.DeviceParameter.DeviceParameter
        - v: value; float
        - result: tuple of the number (int or float) part and the type,
          both as strings; (str,str)
    """
    value_as_str = p.str_for_value(v)                                         # get value as a string
    i = 0
    # skip leading spaces (string guaranteed not to be empty)
    while value_as_str[i] == ' ':
        i += 1
    (number_part,sep,type) = value_as_str[i:].partition(' ')                      # split at the first space
    # detect special cases:
    if number_part[-1] == '°':
        return (number_part[:-1],'°')
    elif number_part[-1] == 'L':
        return (number_part[:-1],'L')
    elif number_part[-1] == 'R':
        return (number_part[:-1],'R')
    elif number_part[-1] == 'k':
        return (number_part[:-1],'kHz')
    elif (len(type) > 0) and (type[0]==':'):
        return (type[2:],':')
    else:
        return (number_part,type)

def _get_par_min_max(p, factor):
    """Return the minimum and maximum value for parameter p as reported
       by live, scaled by a factor, and cast to an integer.
       Use factor to create a reasonable range of integers to represent
       a float value (e.g. use 10 for a volume/dB fader); the integer
       value is converted back to a float, dividing out the same factor,
       with an appropriate formatter function by the E1 preset.
       - p: parameter; Live.DeviceParameter.DeviceParameter
       - factor: multiplication factor; int
       - result: tuple of minimum and maximum integer values; (int,int)
    """
    (vmin_str,mintype) = _get_par_value_info(p,p.min)
    (vmax_str,maxtype) = _get_par_value_info(p,p.max)
    vmin = int(factor * float(vmin_str))
    vmax = int(factor * float(vmax_str))
    return (vmin,vmax)
        
def _strip_plusminus(v):
    """Strip any leading plus or minus sign from a value string
       - v; string
    """
    if (len(v) > 0) and (v[0] in [ '-', '+']):
        return v[1:]
    else:
        return v

def _is_float_str(s):
    """Return whether string represents a float and not an integer
       - s; string
    """
    for c in s:
        if not c.isdigit() and c != '.':
            return False
    return True
        
# type strings that (typically) indicate a non-integer valued parameter
# TODO: what is the ":" type???
NON_INT_TYPES = ['dB', '%', 'Hz', 'kHz', 's', 'ms', 'L', 'R', '°', ':']

# Determine whether the parameter is integer
def _is_int_parameter(p):
    """Return whether parameter has (only) integer values
       - parameter; Live.DeviceParameter.DeviceParameter
    """
    (min_number_part, min_type) = _get_par_value_info(p,p.min)
    min_number_part = _strip_plusminus(min_number_part)
    (max_number_part, max_type) = _get_par_value_info(p,p.max)
    max_number_part = _strip_plusminus(max_number_part)
    return min_number_part.isnumeric() and max_number_part.isnumeric() and \
       (min_type not in NON_INT_TYPES) and (max_type not in NON_INT_TYPES)

def _wants_cc14(p):
    """Return whether a parameter wants a 14bit CC fader or not.
       (Faders that are not mapped to integer parameters want CC14.)
       - parameter; Live.DeviceParameter.DeviceParameter
    """
    # TODO: int parameter with a large range
    # (but smaller than 127) should be mapped to a CC14
    # NON_INT_TYPES partially deals with this
    return (not p.is_quantized) and (not _is_int_parameter(p))                 # not quantized parameters are always faders

# --- types of faders

def _is_pan(p):
    (min_number_part, min_type) = _get_par_value_info(p,p.min)
    return min_type == 'L'

def _is_percent(p):
    (min_number_part, min_type) = _get_par_value_info(p,p.min)
    return min_type == '%'

def _is_degree(p):
    (min_number_part, min_type) = _get_par_value_info(p,p.min)
    return min_type == '°'

def _is_semitone(p):
    (min_number_part, min_type) = _get_par_value_info(p,p.min)
    return min_type == 'st'

def _is_detune(p):
    (min_number_part, min_type) = _get_par_value_info(p,p.min)
    return min_type == 'ct'

def _is_symmetric_dB(p):
    (min_number_part, min_type) = _get_par_value_info(p,p.min)
    min_number_part = _strip_plusminus(min_number_part)
    (max_number_part, max_type) = _get_par_value_info(p,p.max)    
    max_number_part = _strip_plusminus(max_number_part)
    return min_type == 'dB' and (min_number_part == max_number_part)

def _is_untyped_float(p):
    (min_number_part, min_type) = _get_par_value_info(p,p.min)
    min_number_part = _strip_plusminus(min_number_part)
    (max_number_part, max_type) = _get_par_value_info(p,p.max)    
    max_number_part = _strip_plusminus(max_number_part)
    return (min_type == '') and (max_type == '') and \
           _is_float_str(min_number_part) and _is_float_str(max_number_part)

           
class ElectraOneDumper(io.StringIO, ElectraOneBase):
    """ElectraOneDumper extends the StringIO class; this allows the gradual
       construction of a long JSOPN preset string by appending to it.
       (This is (much) more efficient than concatenating immutable strings.)
    """

    def _append(self, *elements):
        """Append the (string representation) of the elements to the output
        """
        for e in elements:
            self.write(str(e))

    def _append_comma(self,flag):
        """Append a comma if flag; return true.
           Use as:
           flag = false
           ...
           flag = _append_comma(flag)
        """
        if flag:
            self._append(',')
        return True
                        
    def _append_json_pages(self, parameters) :
        """Append the necessary number of pages (and their names).
           - parameters: the list of parameters in the preset.
        """
        # WARNING: this code assumes all parameters are included in the preset
        # (Also wrong once we start auto-detecting ADSRs)
        self._append(',"pages":[')
        pagecount = 1 + (len(parameters) // PARAMETERS_PER_PAGE)
        flag = False
        for i in range(1,pagecount+1):
            flag = self._append_comma(flag)
            self._append( f'{{"id":{ _check_pageid(i) },"name":"Page { i }"}}')
        self._append(']')

    def _append_json_devices(self, cc_map):
        """Append the necessary number of devices
           - cc_map: the CC map constructed for the preset.
        """
        self._append(',"devices":[')
        channels = { c.get_midi_channel() for c in cc_map.values() }
        flag = False
        for channel in channels:
            flag = self._append_comma(flag)
            device_id = device_idx_for_midi_channel(channel)
            # double {{ to escape { in f-string
            self._append( f'{{"id":{ _check_deviceid(device_id) }'
                        ,  ',"name":"Generic MIDI"'
                        , f',"port":{ MIDI_PORT }'
                        , f',"channel":{ _check_midichannel(channel) }'
                        ,  '}'
                         )
        self._append(']')
        
    def _append_json_overlay_item(self, label, index, cc_value):
        """Append an overlay item.
           - label: the text to show as value ; str
           - index: the index of this value; int, 0..no. of items-1
           - value: the CC value corresponding to this value; int
        """
        self._append(f'{{"label":"{ label }"' # {{ = {
                   , f',"index":{ index }'
                   , f',"value":{ cc_value }'
                   ,  '}'
                   )

    def _append_json_overlay_items(self, value_items):
        """Append the overlay items. Corresponding CC values are computed
           based on the length of value_items and the position in this list.
           - value_items: list of value items as strings; list of str
        """
        self._append(',"items":[')
        flag = False
        for (idx,item) in enumerate(value_items):
            assert (len(value_items) <= 127), f'Too many overly items { len(value_items) }.'
            item_cc_value = cc_value_for_item_idx(idx, value_items)
            assert (0 <= item_cc_value) and (item_cc_value <= 127), f'MIDI CC value out of range { item_cc_value }.'
            flag = self._append_comma(flag)
            self._append_json_overlay_item(item, idx, item_cc_value)
        self._append(']')

    def _append_json_overlay(self, idx, parameter):
        """Append an overlay for the values associated with a quantised
           parameter. The mapping between overlay index and parameter name
           is stored in self._overlay_map (so the overlay index can later be
           retrieved when dumping the actual control for the parameter).
           - idx: the index of the overlay to construct
           - parameter; Live.DeviceParameter.DeviceParameter
        """
        self._overlay_map[parameter.original_name] = idx
        # {{ to escape { in f string
        self._append(f'{{"id":{ _check_overlayid(idx) }')
        self._append_json_overlay_items(parameter.value_items)
        self._append('}')

    def _append_json_overlays(self, parameters, cc_map):
        """Append the necessary overlays for all quantised parameters (that
           are not simple Off-On parameters (those are handled as toggle
           buttons). The overlays are used later when constructing the actual
           controls.
           - parameters: list of all parameters in the device; list of Live.DeviceParameter.DeviceParameter
           - cc_map: CC map for all parameters in the device; 
        """
        self._append(',"overlays":[')
        overlay_idx = 1
        flag = False
        for p in parameters:
            if p.original_name in cc_map:
                cc_info = cc_map[p.original_name]
                if cc_info.is_mapped() and _needs_overlay(p):
                    flag = self._append_comma(flag)
                    self._append_json_overlay(overlay_idx,p)
                    overlay_idx += 1
        self._append(']')

    def _append_json_bounds(self, idx):
        """Append the bounds information for a control with index idx in the preset.
           Use XCOORDS and YCOORDS to retrieve the actual x/y coordinates of the
           bounding box.
           - idx: control index; int.
        """
        
        idx = idx % PARAMETERS_PER_PAGE
        # (0,0) is top left slot; layout controls left -> right, top -> bottom
        x = idx % SLOTS_PER_ROW
        y = idx // SLOTS_PER_ROW
        self._append( f',"bounds":[{ XCOORDS[x] },{ YCOORDS[y] },{ WIDTH },{ HEIGHT }]' )

    def _append_json_toggle(self, cc_info):
        """Append a toggle pad for an on/off valued list.
           - cc_info; CC mapping info for the control; CCInfo
        """
        device_id = device_idx_for_midi_channel(cc_info.get_midi_channel())
        self._append( ',"type":"pad"'
                   , ',"mode":"toggle"'
                   , ',"values":[{"message":{"type":"cc7"'
                   ,                       ',"offValue": 0'
                   ,                       ',"onValue": 127'
                   ,                      f',"parameterNumber":{ cc_info.get_cc_no() }'
                   ,                      f',"deviceId":{ device_id }'
                   ,                       '}' 
                   ,            ',"id":"value"'
                   ,            '}]'
                   )

    def _append_json_list(self, overlay_idx, cc_info):
        """Append a list control, with values as specified in the overlay.
           - overlay_idx: index of the overlay generated for this list; int
           - cc_info; CC mapping info for the control; CCInfo
        """
        device_id = device_idx_for_midi_channel(cc_info.get_midi_channel())
        self._append( ',"type":"list"'
                   ,  ',"values":[{"message":{"type":"cc7"' 
                   ,                       f',"parameterNumber":{ cc_info.get_cc_no() } '
                   ,                       f',"deviceId":{ device_id }'
                   ,                        '}' 
                   ,            f',"overlayId":{ _check_overlayid(overlay_idx) }'
                   ,             ',"id":"value"'
                   ,             '}]'
                   )

    def _append_json_generic_fader(self, cc_info, thin
                                  ,vmin, vmax, formatter):
        """Append a fader (generic constructor).
           - cc_info: channel, cc_no, is_cc14 information; CCInfo
           - thin: whether to use a thin variant; bool
           - vmin: minimum value; int (or None if not used)
           - vmax: maximum value; int 
           - formatter: name of LUA formatter function; str (None if not used)
             (see EffectController DEFAULT_LUASCRIPT for possible values)
           If vmin != None, vmin and vmax specify the minimal and maximal value
           for the fader as used by the E1 to compute and display its current
           value (possibly using the formatter function if specified) based on
           its MIDI value/position. These min and max values must be
           integers.
        """
        self.debug(5,f'Generic fader {cc_info.is_cc14()}, {vmin}, {vmax}, {formatter}')
        device_id = device_idx_for_midi_channel(cc_info.get_midi_channel())
        self._append(    ',"type":"fader"')
        if thin: 
            self._append(',"variant": "thin"')
        min = 0
        if cc_info.is_cc14():
            max = 16383
            self._append(',"values":['
                        ,   '{"message":{"type":"cc14"'
                        ,              ',"lsbFirst":false'
                        )
        else:
            max = 127        
            self._append(',"type":"fader"' 
                        ,',"values":['
                        ,  '{"message":{"type":"cc7"'
                        )
        self._append(                 f',"parameterNumber":{ cc_info.get_cc_no() }'
                    ,                 f',"deviceId":{ device_id }'
                    ,                 f',"min":{ min }'
                    ,                 f',"max":{ max }'
                    ,                  '}'
                    )
        if vmin != None:
            self._append(  f',"min":{ vmin }'
                        ,  f',"max":{ vmax }'
                        )
        if formatter != None:
            self._append(  f',"formatter":"{ formatter }"' )
        self._append(       ',"id":"value"'
                    ,       '}'
                    ,     ']'
                    )

    def _append_json_symmetric_dB_fader(self, id, p, cc_info):
        """Append a fader showing symmetric dB values.
           - id: id of the control
           - parameter: parameter for which to construct a control; Live.DeviceParameter.DeviceParameter
           - cc_info: CC information for the parameter/control; CCInfo
        """
        (vmin,vmax) = _get_par_min_max(p,10)
        self._append_json_generic_fader(cc_info, True, vmin, vmax,"formatdB")
            
    def _append_json_pan_fader(self, id, p, cc_info):
        """Append a PAN fader.
           - id: id of the control
           - parameter: parameter for which to construct a control; Live.DeviceParameter.DeviceParameter
           - cc_info: CC information for the parameter/control; CCInfo
        """
        (vmin,vmax) = _get_par_min_max(p,1)
        # p.min typically equals 50L, so vmin=50
        self._append_json_generic_fader(cc_info, True, -vmin, vmax, "formatPan")

    def _append_json_percent_fader(self, id, p, cc_info):
        """Append a percentage fader.
           - id: id of the control
           - parameter: parameter for which to construct a control; Live.DeviceParameter.DeviceParameter
           - cc_info: CC information for the parameter/control; CCInfo
        """
        (vmin,vmax) = _get_par_min_max(p,10)
        self._append_json_generic_fader(cc_info, True, vmin, vmax,"formatPercent")

    def _append_json_degree_fader(self, id, p, cc_info):
        """Append a (phase)degree fader.
           - id: id of the control
           - parameter: parameter for which to construct a control; Live.DeviceParameter.DeviceParameter
           - cc_info: CC information for the parameter/control; CCInfo
        """
        (vmin,vmax) = _get_par_min_max(p,1)
        self._append_json_generic_fader(cc_info, True, vmin, vmax,"formatDegree")

    def _append_json_semitone_fader(self, id, p, cc_info):
        """Append a semitone fader.
           - id: id of the control
           - parameter: parameter for which to construct a control; Live.DeviceParameter.DeviceParameter
           - cc_info: CC information for the parameter/control; CCInfo
        """
        (vmin,vmax) = _get_par_min_max(p,1)
        self._append_json_generic_fader(cc_info, True, vmin, vmax,"formatSemitone")

    def _append_json_detune_fader(self, id, p, cc_info):
        """Append a detune fader.
           - id: id of the control
           - parameter: parameter for which to construct a control; Live.DeviceParameter.DeviceParameter
           - cc_info: CC information for the parameter/control; CCInfo
        """
        (vmin,vmax) = _get_par_min_max(p,1)
        self._append_json_generic_fader(cc_info, True, vmin, vmax, "formatDetune")
        
    def _append_json_int_fader(self, id, p, cc_info):
        """Append an integer valued, untyped, fader.
           - id: id of the control
           - parameter: parameter for which to construct a control; Live.DeviceParameter.DeviceParameter
           - cc_info: CC information for the parameter/control, control_id
             is set to id if the parameter needs to be sent value strings
             generated by Ableton live; CCInfo
        """
        (vmin,vmax) = _get_par_min_max(p,1)
        if USE_ABLETON_VALUES:
            self._append_json_generic_fader(cc_info, True, vmin, vmax, "defaultFormatter")
            cc_info.set_control_id(id+1)
        else:
            self._append_json_generic_fader(cc_info, True, vmin, vmax, None)
            
    def _append_json_float_fader(self, id, p, cc_info):
        """Append a float valued, untyped, fader.
           - id: id of the control
           - parameter: parameter for which to construct a control; Live.DeviceParameter.DeviceParameter
           - cc_info: CC information for the parameter/control; CCInfo
        """
        (vmin,vmax) = _get_par_min_max(p,100)
        if vmax > 1000:
            self._append_json_generic_fader(cc_info, True, vmin/10, vmax/10,"formatLargeFloat")
        else:
            self._append_json_generic_fader(cc_info, True, vmin, vmax,"formatFloat")
        
    def _append_json_plain_fader(self, id, p, cc_info):
        """Append a plain fader, showing no values.
           - id: id of the control
           - parameter: parameter for which to construct a control; Live.DeviceParameter.DeviceParameter
           - cc_info: CC information for the parameter/control, control_id
             is set to id if the parameter needs to be sent value strings
             generated by Ableton live; CCInfo
        """
        if USE_ABLETON_VALUES:
            self._append_json_generic_fader(cc_info, True, None, None, "defaultFormatter")
            cc_info.set_control_id(id+1)
        else:
            self._append_json_generic_fader(cc_info, False, None, None, None)
            
    def _append_json_fader(self, id, parameter, cc_info):
        """Append a fader (depending on the parameter type)
           - id: id of the control
           - parameter: parameter for which to construct a control; Live.DeviceParameter.DeviceParameter
           - cc_info: CC information for the parameter/control. MAY BE MODIFIED:
             control_id is set to id if the parameter needs to be sent
             value strings generated by Ableton live
             (see GenericDeviceController.py); CCInfo
        """
        if _is_pan(parameter):
            self._append_json_pan_fader(id,parameter,cc_info)
        elif _is_percent(parameter):
            self._append_json_percent_fader(id,parameter,cc_info)
        elif _is_degree(parameter):
            self._append_json_degree_fader(id,parameter,cc_info)
        elif _is_semitone(parameter):
            self._append_json_semitone_fader(id,parameter,cc_info)
        elif _is_detune(parameter):
            self._append_json_detune_fader(id,parameter,cc_info)
        elif _is_symmetric_dB(parameter):
            self._append_json_symmetric_dB_fader(id,parameter,cc_info)            
        elif _is_int_parameter(parameter):
            self._append_json_int_fader(id,parameter,cc_info)            
        elif _is_untyped_float(parameter):
            self._append_json_float_fader(id,parameter,cc_info)            
        else:
            self._append_json_plain_fader(id,parameter,cc_info)
        
    def _append_json_control(self, id, parameter, cc_info):
        """Append a control (depending on the parameter type: a fader, list or
           on/off toggle pad) to the preset.
           - id: id of the control, starting at 0 (on the E1, ids start at 1!),
             also determines the position of the control in the preset; int
           - parameter: parameter for which to construct a control; Live.DeviceParameter.DeviceParameter
           - cc_info: CC information for the parameter/control. MAY BE MODIFIED:
             control_id is set to id if the parameter needs to be sent
             value strings generated by Ableton live
             (see GenericDeviceController.py); CCInfo
        """
        self.debug(3,f'Appending JSON control for {parameter.name}.')
        page = 1 + (id // PARAMETERS_PER_PAGE)
        controlset = 1 + ((id % PARAMETERS_PER_PAGE) // (PARAMETERS_PER_PAGE // CONTROLSETS_PER_PAGE))
        pot = 1 + (id % (PARAMETERS_PER_PAGE // CONTROLSETS_PER_PAGE))
        self._append( f'{{"id":{ _check_id(id+1) }'
                  , f',"name":"{ _check_name(parameter.name) }"'
                  ,  ',"visible":true' 
                  , f',"color":"{ PRESET_COLOR }"' 
                  , f',"pageId":{ _check_pageid(page) }'
                  , f',"controlSetId":{ _check_controlset(controlset) }'
                  , f',"inputs":[{{"potId":{ _check_pot(pot) },"valueId":"value"}}]'
                  )
        self._append_json_bounds(id)
        if _needs_overlay(parameter):
            overlay_id = self._overlay_map[parameter.original_name]
            self._append_json_list(overlay_id,cc_info)
        elif _is_on_off_parameter(parameter):
            self._append_json_toggle(cc_info)
        else:
            self._append_json_fader(id,parameter,cc_info)
        self._append('}')

    def _append_json_controls(self, parameters, cc_map):
        """Append the controls to the preset. Parameters that do not have a
           CC assigned (i.e. not in cc_map, or with UNMAPPED_CCINFO in the
           cc_map) are skipped.
           (To create a full dump, set MAX_CC7_PARAMETERS,
           MAX_CC14_PARAMETERS and MAX_MIDI_EFFECT_CHANNELS generously).
           - parameter: parameters for which to construct a control;
             list of Live.DeviceParameter.DeviceParameter
           - cc_map: CC information for the parameters/control. MAY BE MODIFIED:
             control_id is set if the associated parameter needs to be sent
             value strings generated by Ableton live
             (see GenericDeviceController.py); dict of CCInfo
        """
        self._append(',"controls":[')
        id = 0  # control identifier
        flag = False
        for p in parameters:
            if p.original_name in cc_map:
                cc_info = cc_map[p.original_name]
                if cc_info.is_mapped():
                    flag = self._append_comma(flag)
                    self._append_json_control(id,p,cc_info)
                    id += 1
        self._append(']')

    def _construct_json_preset(self, device_name, parameters, cc_map):
        """Construct a Electra One JSON preset for the given list of Ableton Live 
           Device/Instrument parameters using the info in the supplied cc_map
           to determine the neccessary MIDI CC info. Return as string. cc_map
           is modified to set the preset control index of parameters for which
           Ableton live string value representations must be sent.
           - device_name: device name for the preset; str
           - parameters: parameters to include; list of Live.DeviceParameter.DeviceParameter
           - cc_map: corresponding cc_map constructed first using
             _construct_ccmap. MAY BE MODIFIED: control_id is set to id if
             the parameter needs to be sent value strings generated by Ableton
             live (see GenericDeviceController.py); dict of CCInfo
           - result: the preset (a JSON object in E1 .epr format); str
        """
        self.debug(2,'Construct JSON')
        # create a random project id
        project_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=20))
        # write everything to the underlying StringIO, a mutable string
        # for efficiency.
        self._append( f'{{"version":{ VERSION }' # {{ = { in f-string
                   , f',"name":"{ _check_name(device_name) }"'
                   , f',"projectId":"{ project_id }"'
                   )
        self._append_json_pages(parameters)
        self._append_json_devices(cc_map)        
        self._overlay_map = {}
        self._append_json_overlays (parameters,cc_map)
        self._append( ',"groups":[]')
        self._append_json_controls(parameters,cc_map)
        self._append( '}' )
        # return the string constructed within the StringIO object
        return self.getvalue()

    def _construct_ccmap(self, parameters):
        """Construct a cc_map for the list of parameters. Map no more parameters
           then specified by MAX_CC7_PARAMETERS and MAX_CC14_PARAMETERS and use
           no more MIDI channels than specified by MAX_MIDI_EFFECT_CHANNELS
           - parameters:  parameter list; list of Live.DeviceParameter.DeviceParameter
           - result: ccmap; dict of CCInfo
        """
        self.debug(2,'Construct CC map')
        # 14bit CC controls are mapped first; they consume two CC parameters
        # (i AND i+32). 7 bit CC controls are mapped next filling any empty
        # slots.
        # For some reason, only the first 32 CC parameters can be mapped to
        # 14bit CC controls. 
        cc_map = {}
        if MAX_MIDI_EFFECT_CHANNELS == -1:
            max_channel = 16
        else:
            # config checks that this is always <= 16
            max_channel = MIDI_EFFECT_CHANNEL + MAX_MIDI_EFFECT_CHANNELS -1
        # get the list of parameters to be assigned to 14bit controllers
        cc14pars = [p for p in parameters if _wants_cc14(p)]
        if MAX_CC14_PARAMETERS != -1:
            cc14pars = cc14pars[:MAX_CC14_PARAMETERS]
        cur_cc14par_idx = 0
        # TODO: consider also including skipped cc14 parameters?
        # get the list of parameters to be assigned to 7bit controllers        
        cc7pars = [p for p in parameters if not _wants_cc14(p)]
        if MAX_CC7_PARAMETERS != -1:
            cc7pars = cc7pars[:MAX_CC7_PARAMETERS]
        cur_cc7par_idx = 0
        # add parameters per channel; break if all parameters are assigned
        for channel in range(MIDI_EFFECT_CHANNEL,max_channel+1):
            # Keep track of 'future' (+32) CC parameters assigned to 14bit parameters
            free = [ True for i in range(0,128)] 
            # first assign any remaining cc14 parameters to the range 0..31
            for i in range(0,32):
                if cur_cc14par_idx >= len(cc14pars):
                    break
                p = cc14pars[cur_cc14par_idx]
                cc_map[p.original_name] = CCInfo((UNMAPPED_ID,channel,IS_CC14,i))
                cur_cc14par_idx += 1
                free[i] = False
                free[i+32] = False
            # now assign cc7 parameters in any free slots
            cc_no = 0
            while (cc_no < 128) and (cur_cc7par_idx < len(cc7pars)):
                while (not free[cc_no]) and (cc_no < 128):
                    cc_no += 1
                if cc_no < 128: # free slot in current channel found
                    p = cc7pars[cur_cc7par_idx]
                    cc_map[p.original_name] = CCInfo((UNMAPPED_ID,channel,IS_CC7,cc_no))
                    cur_cc7par_idx += 1
                    cc_no += 1
        if (cur_cc14par_idx < len(cc14pars)) or (cur_cc7par_idx < len(cc7pars)):
            self.debug(1,'Not all parameters could be mapped.')
        if not DUMP: # no need to write this to the log if the same thing is dumped
            self.debug(5,f'CC map constructed: { cc_map }')
        return cc_map
        
    def _filter_and_order_parameters(self, device_name, parameters):
        """Order the parameters: either original, device-dict based, or
           sorted by name (determined by ORDER configuration constant).
           - device_name: device orignal_name
             (needed to retreive DEVICE_DICT sort order); str
           - parameters:  parameter list to sort;
             list of Live.DeviceParameter.DeviceParameter
           - result: a copy of the parameter list, sorted;
             list of Live.DeviceParameter.DeviceParameter
        """
        self.debug(2,'Filter and order parameters')
        parameters = [p for p in parameters \
                      if p.name not in PARAMETERS_TO_IGNORE]
        if (ORDER == ORDER_DEVICEDICT) and (device_name in DEVICE_DICT) and \
           (device_name not in ORDER_DEVICEDICT_IGNORE):
            banks = DEVICE_DICT[device_name] # tuple of tuples
            parlist = [p for b in banks for p in b] # turn into a list
            # order parameters as in parlist, skip parameters that are not
            # listed in parlist
            parameters_copy = []
            parameters_dict = { p.name: p for p in parameters }
            # copy in the order in which parameters appear in parlist
            for name in parlist:
                if name in parameters_dict:
                    parameters_copy.append(parameters_dict[name])
            return parameters_copy
        elif (ORDER == ORDER_SORTED) and \
             (device_name not in ORDER_SORTED_IGNORE):
            parameters_copy = []
            for p in parameters:
                parameters_copy.append(p)
            parameters_copy.sort(key=lambda p: p.name)
            return parameters_copy
        else: 
            return parameters

    def __init__(self, c_instance, device): 
        """Construct an Electra One JSON preset and a corresponding
           dictionary for the mapping to MIDI CC values, for the given device.
           Use get_preset() for the contructed object to obtain the result.
           Inclusion and order of parameters is controlled by the
           ORDER parameter
           - c_instance: controller instance parameter as passed by Live
           - device: device whose parameters must be dumped; Live.Device.Device
        """
        # initialise a StrinIO object to incrementally construct the preset
        # string in; this is more efficient than appending string constants
        io.StringIO.__init__(self)
        # ElectraOneBase instance used to have access to the log file for debugging.
        ElectraOneBase.__init__(self, c_instance)
        device_name = self.get_device_name(device)
        self.debug(2,f'Dumper for device { device_name } loaded.')
        # TODO: remove: debuging
        for p in device.parameters:
            value_as_str = p.str_for_value(p.min)
            self.debug(5,f'Min value {value_as_str} for {p.original_name} ')
            value_as_str = p.str_for_value(p.max)
            self.debug(5,f'Max value {value_as_str} for {p.original_name} ')
        parameters = self._filter_and_order_parameters(device_name, device.parameters)
        self._cc_map = self._construct_ccmap(parameters)
        # this modifes cc_map to set the control indices for parameters that
        # need to use Ableton generated value strings.
        self._preset_json = self._construct_json_preset(device_name, parameters, self._cc_map)
        self._lua_script = ''


    def get_preset(self):
        """Return the constructed preset and ccmap as PresetInfo.
           - result: preset and ccmap; PresetInfo
        """
        return PresetInfo(self._preset_json, self._lua_script, self._cc_map)
        
