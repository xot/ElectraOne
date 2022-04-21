# ElectrOneDumper
# - code to construct and dump presets.
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
# Devices.py), this assignment can be overridden using the cc-map. Parameters
# with a 7-bit CC get a CC parameter number in the range 1-127 (0 is reserved)
# while parameters with a 14-bit CC are given a CC parameter number in the
# range (129-255); the actual CC is obtained by subtracting 128.
#
# Parameters with only on or off values do not get an overlay and are
# represented on the ElectraOne as (toggle) pads.
#
# Other quantised parameters are represented on the ElectraOne as lists, for
# which a separate overlay with all possible values is created.

# TODO/FIXME: None mappings in cc_map
# (Two different goals: in a *dumped* preset, you want to have *all* parameters
# even those without a CC map; but in a preset you *ulpload* you only want to
# include parameters that are actually mapped in order not to surprise the users)

# Python imports
import io, random, string

# Ableton Live imports
from _Framework.ControlSurface import ControlSurface
from _Generic.Devices import *

# Local imports
from .config import *

# TODO: use p.name or p.original_name??
#
MIDI_PORT = 1
MIDI_CHANNEL = 11
DEVICE_ID = 1

# Electra One JSON file format version constructed 
VERSION = 2

# ElectraOne display parameters
PARAMETERS_PER_PAGE = 3 * 12
CONTROLSETS_PER_PAGE = 3
SLOTS_PER_ROW = 6

# Default color
COLOR = 'FFFFFF'

# Bounds constants: the width and height of  a control on the ElectraOne display
WIDTH = 146
HEIGHT = 56
XCOORDS = [0,170,340,510,680,850]
YCOORDS = [40,128,216,304,392,480]

# maximum values in a preset
MAX_NAME_LEN = 14
MAX_ID = 432
MAX_PAGE_ID = 12
MAX_OVERLAY_ID = 51
MAX_CONTROLSET_ID = CONTROLSETS_PER_PAGE
MAX_POT_ID = (PARAMETERS_PER_PAGE // CONTROLSETS_PER_PAGE)

# --- PresetInfo ---

# TODO: convert to a proper class
# TODO: properly deal with None values: in this 'dumper' module, None values
# are written as '0' to the json preset and as None into the ccmap

def set_cc14 (cc_no):
    return cc_no + 128

def is_cc14 (cc_no):
    if cc_no == None:
        return False
    else:
        return cc_no > 127

def get_cc (cc_no):
    if cc_no == None:
        return 0
    elif cc_no > 127:
        return cc_no - 128
    else:
        return cc_no

class PresetInfo ():
    # - The preset is a JSON string in Electra One format.
    # - The MIDI cc mapping data is a dictionary of Ableton Live original
    #   parameter names with their corresponding MIDI CC values in the preset.
    #   For parameters with a 14bit CC assigned, cc_no+128 is stored

    def __init__(self,json_preset,cc_map):
        self._json_preset = json_preset
        self._cc_map = cc_map

    def get_cc_for_parameter(self,parameter_original_name):
        """Return the MIDI CC parameter info assigned to the device parameter.
           Return None if not mapped.
        """
        assert self._cc_map != None, 'Empty cc-map'
        if parameter_original_name in self._cc_map:
            return self._cc_map[parameter_original_name]
        else:
            return None

    def get_preset(self):
        """Retrun the JSON preset as a string
        """
        assert self._json_preset != None, 'Empty JSON preset'
        return self._json_preset
     
# --- output sanity checks

# check/truncate name
def check_name(name):
    # TODO log truncation
    return name[:MAX_NAME_LEN]

def check_id(id):
    assert (1 <= id) and (id <= MAX_ID), f'{ id } exceeds max number of IDs ({ MAX_ID }).'
    return id

def check_pageid(id):
    assert (1 <= id) and (id <= MAX_PAGE_ID), f'{ id } exceeds max number of pages ({ MAX_PAGE_ID }).'
    return id

def check_overlayid(id):
    assert (1 <= id) and (id <= MAX_OVERLAY_ID), f'{ id } exceeds max number of overlays ({ MAX_OVERLAY_ID }).'
    return id

def check_cc_no(cc_no):
    # TODO FIXME
    if cc_no == None:
        return 0
    assert cc_no in range(128), f'CC no ({ cc_no }) out of range.'
    return cc_no

# This is more strict than the Electra One documentation requires
def check_controlset(id):
    assert (1 <= id) and (id <= MAX_CONTROLSET_ID), f'{ id } exceeds max number of controlsets ({ MAX_CONTROLSET_ID }).'
    return id

def check_pot(id):
    assert (1 <= id) and (id <= MAX_POT_ID), f'{ id } exceeds max number of pots ({ MAX_POT_ID }).'
    return id
    

# --- utility

def is_on_off_parameter(p):
    """Return whether the parameter has the values "Off" and "On" only.
    """
    if not p.is_quantized:
        return False
    values = p.value_items
    if (len(values) != 2):
        return False
    else:
        return ( (str(values[0]) == "Off") and (str(values[1]) == "On"))

def needs_overlay(p):
    """Return whether the parameter needs an overlay to be generated
       (that enumerates all the values in the list, and that will be attached
       to the parameter in the 'controls' section of the same parameter.
    """
    return p.is_quantized and (not is_on_off_parameter(p))

# quantized parameters have a list of values. For such a list with
# n items, item i (staring at 0) has MIDI CC control value
# round(i * 127/(n-1)) 
def cc_value_for_item_idx(idx,items):
    return round( idx * (127 / (len(items)-1) ) )


# Return the number part in the string representation of the value of a parameter
def get_par_number_part(p,v):
    value_as_str = p.str_for_value(v)                                         # get value as a string
    (number_part,sep,rest) = value_as_str.partition(' ')                      # split at the first space
    return number_part


# Determine whether the parameter is integer
def is_int_parameter(p):
    min_number_part = get_par_number_part(p,p.min)
    # TODO: uncomment once it is clear how to deal with negative values
    # integer parameters.
    if (len(min_number_part) > 0) and (min_number_part[0] == '-'):
        min_number_part = min_number_part[1:] 
    max_number_part = get_par_number_part(p,p.max)
    # in the unlikely event that a maximum value is also negative ;-)
    if (len(max_number_part) > 0) and (max_number_part[0] == '-'):
        max_number_part = max_number_part[1:] 
    return min_number_part.isnumeric() and max_number_part.isnumeric() 

def wants_cc14(p):
    """Return whether a parameter wants a 14bit CC fader or not.
       (Faders that are not mapped to integer parameters want CC14.)
    """
    return (not p.is_quantized) and (not is_int_parameter(p))                 # not quantized parameters are always faders


# TODO: FIXME: global parameter   
overlay_idx = 0

def sortkey(list,p):
    if p in list:
        return list.index(p)
    else:
        return len(list)+1
        
class ElectraOneDumper(io.StringIO):
    """ElectraOneDumper extends the StringIO class allows the gradual
       construction of a long JSOPN preset string by appending to it.
    """

    def append(self,*elements):
        """Append the (string representation) of the elements to the output
        """
        for e in elements:
            self.write(str(e))

    # append a comma if flag; return true; us as:
    # flag = false
    # flag = append_comma(flag)
    def append_comma(self,flag):
        if flag:
            self.append(',')
        return True
                        
    def debug(self,m):
        self._e1_instance.debug(m)
        
    def append_json_pages(self,parameters) :
        """Append the necessary number of pages (and their names)
        """
        # WARNING: this code assumes all parameters are included in the preset
        self.append(',"pages":[')
        pagecount = 1 + (len(parameters) // PARAMETERS_PER_PAGE)
        flag = False
        for i in range(1,pagecount+1):
            flag = self.append_comma(flag)
            self.append( f'{{"id":{ check_pageid(i) },"name":"Page { i }"}}')
        self.append(']')

    def append_json_overlay_item(self,label,index,value):
        """Append an overlay item.
        """
        self.append( f'{{"label":"{ label }"' 
                   , f',"index":{ index }'
                   , f',"value":{ value }'
                   ,  '}'
                   )

    def append_json_overlay_items(self,value_items):
        """Append the overlay items.
        """
        self.append(',"items":[')
        flag = False
        for (idx,item) in enumerate(value_items):
            assert (len(value_items) <= 127), f'Too many overly items { len(value_items) }.'
            item_cc_value = cc_value_for_item_idx(idx,value_items)
            assert (0 <= item_cc_value) and (item_cc_value <= 127), f'MIDI CC value out of range { item_cc_value }.'
            flag = self.append_comma(flag)
            self.append_json_overlay_item(item,idx,item_cc_value)
        self.append(']')

    def append_json_overlay(self,idx,parameter):
        """Append an overlay.
        """
        self.append(f'{{"id":{ check_overlayid(idx) }')
        self.append_json_overlay_items(parameter.value_items)
        self.append('}')

    def append_json_overlays(self,parameters):
        """Append the necessary overlays (for list valued parameters).
        """
        self.append(',"overlays":[')
        overlay_idx = 1
        flag = False
        for p in parameters:
            if needs_overlay(p):
               flag = self.append_comma(flag)
               self.append_json_overlay(overlay_idx,p)
               overlay_idx += 1
        self.append(']')

    def append_json_bounds(self,idx):
        idx = idx % PARAMETERS_PER_PAGE
        # (0,0) is top left slot; layout controls left -> right, top -> bottom
        x = idx % SLOTS_PER_ROW
        y = idx // SLOTS_PER_ROW
        self.append( f',"bounds":[{ XCOORDS[x] },{ YCOORDS[y] },{ WIDTH },{ HEIGHT }]' )

    def append_json_toggle(self, idx, cc_no):
        """Append a toggle pad for an on/off valued list.
        """
        self.append( ',"type":"pad"'
                   , ',"mode":"toggle"'
                   , ',"values":[{"message":{"type":"cc7"'
                   ,                       ',"offValue": 0'
                   ,                       ',"onValue": 127'
                   ,                      f',"parameterNumber":{ check_cc_no(cc_no) }'
                   ,                      f',"deviceId":{ DEVICE_ID }'
                   ,                       '}' 
                   ,            ',"id":"value"'
                   ,            '}]'
                   )

    def append_json_list(self,idx, overlay_idx,cc_no):
        """Append a list, with values as specified in the overlay.
        """
        self.append( ',"type":"list"'
                   ,  ',"values":[{"message":{"type":"cc7"' 
                   ,                       f',"parameterNumber":{ check_cc_no(cc_no) } '
                   ,                       f',"deviceId":{ DEVICE_ID }'
                   ,                        '}' 
                   ,            f',"overlayId":{ check_overlayid(overlay_idx) }'
                   ,             ',"id":"value"'
                   ,             '}]'
                   )
        
    def append_json_fader(self, idx, p, cc_no):
        """Append a fader.
        """
        # TODO: it may happen that an integer parameter has a lot of values
        # but it actually is assigned a 7bit CC
        if is_cc14(cc_no):
            min = 0
            max = 16383
        else:
            min = 0
            max = 127        
        self.append(    ',"type":"fader"' )
        if is_cc14(cc_no):
            self.append(',"values":['
                       ,   '{"message":{"type":"cc14"'
                       ,              ',"lsbFirst":false'
                       )
        else:
            self.append(',"values":['
                       ,   '{"message":{"type":"cc7"'
                       )
        self.append(                 f',"parameterNumber":{ check_cc_no(get_cc(cc_no)) }'
                   ,                 f',"deviceId":{ DEVICE_ID }'
                   ,                 f',"min":{ min }'
                   ,                 f',"max":{ max }'
                   ,                  '}'
                   )
        if is_int_parameter(p):
            vmin = get_par_number_part(p,p.min)
            vmax = get_par_number_part(p,p.max)
            self.append(  f',"min":{ vmin }'
                       ,  f',"max":{ vmax }'
                       ) 
        self.append(       ',"id":"value"'
                   ,       '}'
                   ,     ']'
                   )
        
    # idx (for the parameter): starts at 0!
    def append_json_control(self, idx, parameter, cc_no):
        """Append a control (depending on the parameter type): a fader, list or
           on/off toggle pad).
        """
        global overlay_idx
        overlay_idx = 1
        page = 1 + (idx // PARAMETERS_PER_PAGE)
        controlset = 1 + ((idx % PARAMETERS_PER_PAGE) // (PARAMETERS_PER_PAGE // CONTROLSETS_PER_PAGE))
        pot = 1 + (idx % (PARAMETERS_PER_PAGE // CONTROLSETS_PER_PAGE))
        self.append( f'{{"id":{ check_id(idx+1) }'
                  , f',"name":"{ check_name(parameter.name) }"'
                  ,  ',"visible":true' 
                  , f',"color":"{ COLOR }"' 
                  , f',"pageId":{ check_pageid(page) }'
                  , f',"controlSetId":{ check_controlset(controlset) }'
                  , f',"inputs":[{{"potId":{ check_pot(pot) },"valueId":"value"}}]'
                  )
        self.append_json_bounds(idx)
        # TODO: overlay_idx implicitly matched to parameter; dangerous
        if needs_overlay(parameter):
            self.append_json_list(idx,overlay_idx,cc_no)
            overlay_idx += 1
        elif is_on_off_parameter(parameter):
            self.append_json_toggle(idx,cc_no)
        else:
            self.append_json_fader(idx,parameter,cc_no)
        self.append('}')

    def append_json_controls(self, parameters, cc_map):
        """Append the controls. Parameters that do not have a CC assigned
           (ie with None in the cc_map) are given cc=0 in the output.
        """
        global overlay_idx
        self.append(',"controls":[')
        overlay_idx = 1
        flag = False
        for (i,p) in enumerate(parameters):
            flag = self.append_comma(flag)
            # TODO FIXME
            # assert p.original_name in cc_map, 'Parameter expected in CC map'
            if p.original_name not in cc_map:
                cc_no = None
            else:
                cc_no = cc_map[p.original_name]
            self.append_json_control(i,p,cc_no)
        self.append(']')

    def construct_json_preset(self, device_name, parameters, cc_map):
        """Construct a Electra One JSON preset for the given list of Ableton Live 
           Device/Instrument parameters. Return as string.
        """
        # create a random project id
        PROJECT_ID = ''.join(random.choices(string.ascii_uppercase + string.digits, k=20))
        # write everything to a mutable string for efficiency
        self.append( f'{{"version":{ VERSION }'
                   , f',"name":"{ check_name(device_name) }"'
                   , f',"projectId":"{ PROJECT_ID }"'
                   )
        self.append_json_pages(parameters)
        self.append( f',"devices":[{{"id":{ DEVICE_ID }'
                   ,                ',"name":"Generic MIDI"'
                   ,               f',"port":{ MIDI_PORT }'
                   ,               f',"channel":{ MIDI_CHANNEL }'
                   ,                '}]'
                   )
        self.append_json_overlays (parameters)
        self.append( ',"groups":[]')
        self.append_json_controls(parameters,cc_map)
        self.append( '}' )
        return self.getvalue()

    def construct_ccmap(self,parameters):
        """Construct a cc_map for the list of parameters.
        """
        # first compute how many faders we can assign to 14bit CCs (because
        # they consume two CC parameters (i AND i+32) and we want to map as many
        # device parameters as possible
        space_for_cc14 = 127-len(parameters)
        cc_map = {}
        # Keep track of used CC parameters
        free = [ True for i in range(0,128)] # extra free[0] not used
        i = 1
        # first assign 14bit CC controllers
        for p in parameters:
            if wants_cc14(p):
                # find a free CC parameter from where we are now
                while (i < 128) and (not free[i]):
                    i += 1
                # only assign a 14bit CC if there is still space
                if space_for_cc14 > 0:
                    space_for_cc14 -= 1
                    assert i+32 < 128, 'There should be space for this 14bit CC'
                    cc_map[p.original_name] = set_cc14(i)
                    free[i] = False
                    free[i+32] = False
                else:
                    if i < 128:
                        cc_map[p.original_name] = i
                        free[i] = False
                i += 1
        # now fill the remaining slots with other parameters (that are 7bit)
        i = 1
        for p in parameters:
            if not wants_cc14(p):
                # find a free CC parameter from where we are now
                while (i < 128) and (not free[i]):
                    i += 1
                if i < 128:
                    cc_map[p.original_name] = i
                    free[i] = False
                i += 1 
        return cc_map

    def order_parameters(self,device_name, parameters):
        """Order the parameters: either original, or sorted by name.
        """
        if (ORDER == ORDER_ORIGINAL):
            return parameters
        else:
            parameters_copy = []
            for p in parameters:
                parameters_copy.append(p)
            if (ORDER == ORDER_SORTED):
                parameters_copy.sort(key=lambda p: p.name)
            else: # ORDER == ORDER_DEVICEDICT
                if device_name in DEVICE_DICT:
                    banks = DEVICE_DICT[device_name] # tuple of tuples
                    parlist = [p for b in banks for p in b] # turn into a list
                    parameters_copy.sort(key=lambda p: sortkey(parlist,p.name))
            return parameters_copy

    def __init__(self, e1_instance, device_name, parameters):
        """Construct an Electra One JSON preset and a corresponding
           dictionary for the mapping to MIDI CC values, for the given
           device with the given list of Ableton Live Device/Instrument
           parameters. 
        """
        super(ElectraOneDumper, self).__init__()
        # e1_instance used to have access to the log file for debugging.
        self._e1_instance = e1_instance
        self.debug('ElectraOneDumper loaded.')
        self.debug('Order parameters')
        parameters = self.order_parameters(device_name,parameters)
        self.debug('Construct CC map')
        self._cc_map = self.construct_ccmap(parameters)
        self.debug('Construct JSON')
        self._preset_json = self.construct_json_preset(device_name, parameters,self._cc_map)


    def get_preset(self):
        """Return the constructed preset and ccmap as PresetInfo.
        """
        return PresetInfo(self._preset_json,self._cc_map)
        
