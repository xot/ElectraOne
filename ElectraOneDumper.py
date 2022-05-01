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
# Devices.py), this assignment can be overridden using the cc-map. 
#
# Parameters with only on or off values do not get an overlay and are
# represented on the ElectraOne as (toggle) pads.
#
# Other quantised parameters are represented on the ElectraOne as lists, for
# which a separate overlay with all possible values is created.

# TODO/FIXME: None mappings in cc_map
# (Two different goals: in a *dumped* preset, you want to have *all* parameters
# even those without a CC map; but in a preset you *upload* you only want to
# include parameters that are actually mapped in order not to surprise the users)
# Currently, the CC-map contains *all* parameters (also unmapped onse,
# indicated ny None) while the on-the-fly constructed preset does not contain
# them. 

# Note: parameter.name used as the visible name for a parameter, and
# parameter.original_name used to index cc_map (because .original_name
# is guaranteed not to change so mappings remain consistent).


# Python imports
import io, random, string

# Ableton Live imports
from _Generic.Devices import *

# Local imports
from .config import *
from .ElectraOneBase import cc_value_for_item_idx
from .CCInfo import CCInfo, UNMAPPED_CC, IS_CC7, IS_CC14
from .PresetInfo import PresetInfo

# Electra One MIDI Port to use
MIDI_PORT = 1

# Electra One JSON file format version constructed 
VERSION = 2

# ElectraOne display parameters
PARAMETERS_PER_PAGE = 3 * 12
CONTROLSETS_PER_PAGE = 3
SLOTS_PER_ROW = 6

# Default color
COLOR = 'FFFFFF'

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


# return the device id to use in the preset for the specified MIDI channel
# (deviceId 1 contains the first (lowest) MIDI channel)
def device_idx_for_midi_channel(midi_channel):
    return 1 + midi_channel - MIDI_EFFECT_CHANNEL

     
# --- output sanity checks

# check/truncate name
def check_name(name):
    # TODO log truncation
    return name[:MAX_NAME_LEN]

def check_id(id):
    assert (1 <= id) and (id <= MAX_ID), f'{ id } exceeds max number of IDs ({ MAX_ID }).'
    return id

def check_deviceid(id):
    assert (1 <= id) and (id <= MAX_DEVICE_ID), f'{ id } exceeds max number of device IDs ({ MAX_DEVICE_ID }).'
    return id

def check_midichannel(channel):
    assert channel in range(1,17), f'MIDI channel { channel } not in range.'
    return channel

def check_pageid(id):
    assert (1 <= id) and (id <= MAX_PAGE_ID), f'{ id } exceeds max number of pages ({ MAX_PAGE_ID }).'
    return id

def check_overlayid(id):
    assert (1 <= id) and (id <= MAX_OVERLAY_ID), f'{ id } exceeds max number of overlays ({ MAX_OVERLAY_ID }).'
    return id

# This is more strict than the Electra One documentation requires
def check_controlset(id):
    assert (1 <= id) and (id <= MAX_CONTROLSET_ID), f'{ id } exceeds max number of controlsets ({ MAX_CONTROLSET_ID }).'
    return id

def check_pot(id):
    assert id in range(1,MAX_POT_ID+1), f'{ id } exceeds max number of pots ({ MAX_POT_ID }).'
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


# Ableyon's str_for_value function for a parameter returns a string with the
# following structure <valuestring><space><valuetype>. Untyped values
# only return <valuestring>.
# 100 %
# -4.00
# 5 ms
# On
# -inf dB
# 3.7 Hz

# Return the number part and its type in the string representation of
# the value of a parameter, as reported by Ableton
def get_par_value_info(p,v):
    value_as_str = p.str_for_value(v)                                         # get value as a string
    (number_part,sep,type) = value_as_str.partition(' ')                      # split at the first space
    return (number_part,type)

def strip_minus(v):
    if (len(v) > 0) and (v[0] == '-'):
        return v[1:]
    else:
        return v

NON_INT_TYPES = ['dB', '%', 'Hz', 's', 'ms']

# Determine whether the parameter is integer
def is_int_parameter(p):
    (min_number_part, min_type) = get_par_value_info(p,p.min)
    min_number_part = strip_minus(min_number_part)
    (max_number_part, max_type) = get_par_value_info(p,p.max)
    max_number_part = strip_minus(max_number_part)
    return min_number_part.isnumeric() and max_number_part.isnumeric() and \
       (min_type not in NON_INT_TYPES) and (max_type not in NON_INT_TYPES)

def wants_cc14(p):
    """Return whether a parameter wants a 14bit CC fader or not.
       (Faders that are not mapped to integer parameters want CC14.)
    """
    return (not p.is_quantized) and (not is_int_parameter(p))                 # not quantized parameters are always faders


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
                        
    def debug(self,level,m):
        self._e1_instance.debug(level,m)
        
    def append_json_pages(self,parameters) :
        """Append the necessary number of pages (and their names)
        """
        # WARNING: this code assumes all parameters are included in the preset
        # (Also wrong once we start auto-detecting ADSRs)
        self.append(',"pages":[')
        pagecount = 1 + (len(parameters) // PARAMETERS_PER_PAGE)
        flag = False
        for i in range(1,pagecount+1):
            flag = self.append_comma(flag)
            self.append( f'{{"id":{ check_pageid(i) },"name":"Page { i }"}}')
        self.append(']')

    def append_json_devices(self, cc_map):
        self.append(',"devices":[')
        channels = { c.get_midi_channel() for c in cc_map.values() }
        flag = False
        for channel in channels:
            flag = self.append_comma(flag)
            device_id = device_idx_for_midi_channel(channel)
            self.append( f'{{"id":{ check_deviceid(device_id) }'
                       ,   ',"name":"Generic MIDI"'
                       ,  f',"port":{ MIDI_PORT }'
                       ,  f',"channel":{ check_midichannel(channel) }'
                       ,   '}'
                       )
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
        self._overlay_map[parameter.original_name] = idx
        self.append(f'{{"id":{ check_overlayid(idx) }')
        self.append_json_overlay_items(parameter.value_items)
        self.append('}')

    def append_json_overlays(self,parameters,cc_map):
        """Append the necessary overlays (for list valued parameters).
        """
        self.append(',"overlays":[')
        overlay_idx = 1
        flag = False
        for p in parameters:
            if p.original_name in cc_map:
                cc_info = cc_map[p.original_name]
                if cc_info.is_mapped() and needs_overlay(p):
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

    def append_json_toggle(self, idx, cc_info):
        """Append a toggle pad for an on/off valued list.
        """
        device_id = device_idx_for_midi_channel(cc_info.get_midi_channel())
        self.append( ',"type":"pad"'
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

    def append_json_list(self,idx, overlay_idx,cc_info):
        """Append a list, with values as specified in the overlay.
        """
        device_id = device_idx_for_midi_channel(cc_info.get_midi_channel())
        self.append( ',"type":"list"'
                   ,  ',"values":[{"message":{"type":"cc7"' 
                   ,                       f',"parameterNumber":{ cc_info.get_cc_no() } '
                   ,                       f',"deviceId":{ device_id }'
                   ,                        '}' 
                   ,            f',"overlayId":{ check_overlayid(overlay_idx) }'
                   ,             ',"id":"value"'
                   ,             '}]'
                   )
        
    def append_json_fader(self, idx, p, cc_info):
        """Append a fader.
        """
        device_id = device_idx_for_midi_channel(cc_info.get_midi_channel())
        # TODO: it may happen that an integer parameter has a lot of values
        # but it actually is assigned a 7bit CC
        if cc_info.is_cc14():
            min = 0
            max = 16383
        else:
            min = 0
            max = 127        
        self.append(    ',"type":"fader"' )
        if cc_info.is_cc14():
            self.append(',"values":['
                       ,   '{"message":{"type":"cc14"'
                       ,              ',"lsbFirst":false'
                       )
        else:
            self.append(',"values":['
                       ,   '{"message":{"type":"cc7"'
                       )
        self.append(                 f',"parameterNumber":{ cc_info.get_cc_no() }'
                   ,                 f',"deviceId":{ device_id }'
                   ,                 f',"min":{ min }'
                   ,                 f',"max":{ max }'
                   ,                  '}'
                   )
        if is_int_parameter(p):
            (vmin,mintype) = get_par_value_info(p,p.min)
            (vmax,maxtype) = get_par_value_info(p,p.max)
            self.append(  f',"min":{ vmin }'
                       ,  f',"max":{ vmax }'
                       ) 
        self.append(       ',"id":"value"'
                   ,       '}'
                   ,     ']'
                   )
        
    # idx (for the parameter): starts at 0!
    def append_json_control(self, idx, parameter, cc_info):
        """Append a control (depending on the parameter type): a fader, list or
           on/off toggle pad).
        """
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
        if needs_overlay(parameter):
            overlay_idx = self._overlay_map[parameter.original_name]
            self.append_json_list(idx,overlay_idx,cc_info)
        elif is_on_off_parameter(parameter):
            self.append_json_toggle(idx,cc_info)
        else:
            self.append_json_fader(idx,parameter,cc_info)
        self.append('}')

    def append_json_controls(self, parameters, cc_map):
        """Append the controls. Parameters that do not have a CC assigned
           (i.e. not in cc_map, or with UNMAPPED_CCINFO in the ccmap)
           are skipped. (To create a full dump, set MAX_CC7_PARAMETERS,
           MAX_CC14_PARAMETERS and MAX_MIDI_EFFECT_CHANNELS generously).
        """
        global overlay_idx
        self.append(',"controls":[')
        overlay_idx = 1
        id = 0  # control identifier
        flag = False
        for p in parameters:
            if p.original_name in cc_map:
                cc_info = cc_map[p.original_name]
                if cc_info.is_mapped():
                    flag = self.append_comma(flag)
                    self.append_json_control(id,p,cc_info)
                    id += 1
        self.append(']')

    def construct_json_preset(self, device_name, parameters, cc_map):
        """Construct a Electra One JSON preset for the given list of Ableton Live 
           Device/Instrument parameters. Return as string.
        """
        self.debug(1,'Construct JSON')
        # create a random project id
        PROJECT_ID = ''.join(random.choices(string.ascii_uppercase + string.digits, k=20))
        # write everything to a mutable string for efficiency
        self.append( f'{{"version":{ VERSION }'
                   , f',"name":"{ check_name(device_name) }"'
                   , f',"projectId":"{ PROJECT_ID }"'
                   )
        self.append_json_pages(parameters)
        self.append_json_devices(cc_map)        
        self._overlay_map = {}
        self.append_json_overlays (parameters,cc_map)
        self.append( ',"groups":[]')
        self.append_json_controls(parameters,cc_map)
        self.append( '}' )
        return self.getvalue()

    def construct_ccmap(self,parameters):
        """Construct a cc_map for the list of parameters. Map no more parameters
           then specified by MAX_CC7_PARAMETERS and MAX_CC14_PARAMETERS and use
           no more MIDI channels than specified by MAX_MIDI_EFFECT_CHANNELS
        """
        self.debug(1,'Construct CC map')
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
        cc14pars = [p for p in parameters if wants_cc14(p)]
        if MAX_CC14_PARAMETERS != -1:
            cc14pars = cc14pars[:MAX_CC14_PARAMETERS]
        cur_cc14par_idx = 0
        # TODO: consider also including skipped cc14 parameters?
        # get the list of parameters to be assigned to 7bit controllers        
        cc7pars = [p for p in parameters if not wants_cc14(p)]
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
                cc_map[p.original_name] = CCInfo((channel,IS_CC14,i))
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
                    cc_map[p.original_name] = CCInfo((channel,IS_CC7,cc_no))
                    cur_cc7par_idx += 1
                    cc_no += 1
        if (cur_cc14par_idx < len(cc14pars)) or (cur_cc7par_idx < len(cc7pars)):
            self.debug(1,'Not all parameters could be mapped.')
        if not DUMP: # no need to write this to the log if the same thing is dumped
            self.debug(4,f'CC map constructed: { cc_map }')
        return cc_map
        
    def order_parameters(self,device_name, parameters):
        """Order the parameters: either original, device-dict based, or sorted by name.
        """
        self.debug(2,'Order parameters')
        if (ORDER == ORDER_DEVICEDICT) and (device_name in DEVICE_DICT):
            banks = DEVICE_DICT[device_name] # tuple of tuples
            parlist = [p for b in banks for p in b] # turn into a list
            # order parameters as in parlist, skip parameters that are not listed there
            parameters_copy = []
            parameters_dict = { p.name: p for p in parameters }
            # copy in the order in which parameters appear in parlist
            for name in parlist:
                if name in parameters_dict:
                    parameters_copy.append(parameters_dict[name])
            return parameters_copy
        elif (ORDER == ORDER_SORTED):
            parameters_copy = []
            for p in parameters:
                parameters_copy.append(p)
            parameters_copy.sort(key=lambda p: p.name)
            return parameters_copy
        else: # ORDER == ORDER_ORIGINAL or (ORDER == ORDER_DEVICEDICT) and (device_name not in DEVICE_DICT)
            return parameters

    def __init__(self, e1_instance, device_name, parameters):
        """Construct an Electra One JSON preset and a corresponding
           dictionary for the mapping to MIDI CC values, for the given
           device with the given list of Ableton Live Device/Instrument
           parameters. 
        """
        super(ElectraOneDumper, self).__init__()
        # e1_instance used to have access to the log file for debugging.
        self._e1_instance = e1_instance
        self.debug(0,'Dumper loaded.')
        parameters = self.order_parameters(device_name,parameters)
        self._cc_map = self.construct_ccmap(parameters)
        self._preset_json = self.construct_json_preset(device_name,parameters,self._cc_map)


    def get_preset(self):
        """Return the constructed preset and ccmap as PresetInfo.
        """
        return PresetInfo(self._preset_json,self._cc_map)
        
