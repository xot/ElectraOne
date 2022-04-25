# config
# - configuration constants
#
# Part of ElectraOne.
#
# Ableton Live MIDI Remote Script for the Electra One - user configurations
#
# Author: Jaap-henk Hoepman (info@xot.nl)
#
# Distributed under the MIT License, see LICENSE
#

# Whether debugging information should be written to the log
DEBUG = True

# Whether creates patch info should be dumped
DUMP = True

# Local directory where dunps are stored (./dumps) and user defined
# presets are loaded from (./user-presets). This is first tried as a
# directory relative to the user's home directory; if that doesn't exist,
# it is interpreted as an absolute path. If that also doesn't exist, then
# the user home directory is used instead (and ./dumps or ./user-presets
# are not appended).
LOCALDIR = 'src/ableton-control-scripts/ElectraOne'

ORDER_ORIGINAL = 0   # order as reported by Live
ORDER_SORTED = 1     # sort by parameter name
ORDER_DEVICEDICT = 2 # order according to the standard remote script preferred order as defined by DEVICE_DICT in the Ableton Live rmeote script framework

# Specify the order in which parameters shoudl appear in an automatically
# created preset for the currently selected device. If order is
# ORDER_DEVICEDICT, parameters NOT in DEVICE_DICT are NOT included in the preset
ORDER = ORDER_SORTED

# Limit the number of parameters assigned to 7bit and 14bit CC controllers
# included in a preset constructed on the fly;
# -1 means all parameters are included: this is a good setting when
# ORDER = ORDER_DEVICEDICT
MAX_CC7_PARAMETERS = -1
MAX_CC14_PARAMETERS = -1

# First MIDI channel used when creating effect/device presets on the fly;
# range of MIDI channels used is
# [MIDI_EFFECT_CHANNEL, .. , MIDI_EFFECT_CHANNEL + MAX_MIDI_CHANNELS-1]
MIDI_EFFECT_CHANNEL = 11

# Limit the number of MIDI channels used in a preset constructed on the fly;
# -1 means all possible MIDI channels are used  (starting from MIDI_CHANNEL
# all the way up to and including channel 16)
MAX_MIDI_CHANNELS = 2
