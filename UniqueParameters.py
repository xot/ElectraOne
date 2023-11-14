# UniqueParameters
# - class to make Live's device parameter names unique
#
# Part of ElectraOne.
#
# Ableton Live MIDI Remote Script for the Electra One
#
# Author: Jaap-henk Hoepman (info@xot.nl)
#
# Distributed under the MIT License, see LICENSE

import Live

class UniqueParameter(Live.DeviceParameter.DeviceParameter):
    """Class extending Live's original parameter to redefine original_name
       and name. 'Monkeypatched' in get_unique_parameters_for_device
       See: https://stackoverflow.com/questions/31590152/monkey-patching-a-property
    """
    # Define class variables with the same name as the properties we want
    # to override; this shields the property defintions in DeviceParameter.
    # Now an instance of this class can create its own
    # instance variables with the same name without complaints about a missing
    # setter for the instance
    original_name = ""
    name = ""
    
def make_device_parameters_unique(device):
    """Return the list device.parameters, in the same order, but making
       original_name and name unique
       - device: Live.Device
       result: list of parameters; [UniqueParameter]
    """
    original_names = {}
    parameters = []
    for p in device.parameters:
        name = p.name
        original_name = p.original_name
        if original_name in original_names:
            original_names[original_name] += 1
            suffix = f'.{original_names[original_name]}'
        else:
            original_names[original_name] = 0
            suffix = ''
        p.__class__ = UniqueParameter
        # This creates instance variables!
        p.original_name = original_name + suffix
        p.name = name + suffix
        parameters.append(p)
    return parameters

