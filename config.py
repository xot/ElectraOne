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

# === GENERAL CONFIGURATION CONSTANTS 

# How much debugging information should be logged; higher values
# imply more information. 0 means no logging at all.
DEBUG = 5

# Whether created patch info should be dumped
DUMP = False

# Whether to detect the  E1 at start up (or assume it's there regardless)
DETECT_E1 = False

# Local directory where dunps are stored (./dumps), user defined
# presets are loaded from (./user-presets), and where to llok for the sendmidi
# program.
#
# This is first tried as a directory relative to the user's home directory;
# if that doesn't exist, it is interpreted as an absolute path. If that also
# doesn't exist, then the user home directory is used instead (and ./dumps
# or ./user-presets are not appended to make sure the directory exists).
LOCALDIR = 'src/ableton-control-scripts/ElectraOne'

# 'reset slot': when selecting this slot on the E1, the remote script is reset
RESET_SLOT = (5,11)

# === FAST SYSEX UPLOAD 

# Flag whether to use fast sysex uploading,
# using the (external) sendmidi package
# If True, correctly set the following two constants too  
USE_FAST_SYSEX_UPLOAD = True

# path to the sendmidi command, relative to ~/LOCLADIR or ~ 
SENDMIDI_CMD = 'lib/sendmidi'
# name of the Electra One port to which to send the SysEx command
E1_CTRL_PORT = 'Electra Controller Electra CTRL'

# === EFFECT/DEVICE CONFIGURATION CONSTANTS

# E1 preset slot where the preset controlling the currently selected device
# is stored. Specified by bank index (0..5) followed by preset index (0.11)
EFFECT_PRESET_SLOT = (5,1)

ORDER_ORIGINAL = 0   # order as reported by Live
ORDER_SORTED = 1     # sort by parameter name
ORDER_DEVICEDICT = 2 # order according to the standard remote script preferred order as defined by DEVICE_DICT in the Ableton Live rmeote script framework

# Specify the order in which parameters shoudl appear in an automatically
# created preset for the currently selected device. If order is
# ORDER_DEVICEDICT, parameters NOT in DEVICE_DICT are NOT included in the preset
ORDER = ORDER_DEVICEDICT

# Limit the number of parameters assigned to 7bit and 14bit CC controllers
# included in a preset constructed on the fly;
# -1 means all parameters are included: this is a good setting when
# ORDER = ORDER_DEVICEDICT
MAX_CC7_PARAMETERS = -1
MAX_CC14_PARAMETERS = -1

# ===  MIXER CONFIGURATION CONSTANTS 

# E1 preset slot where the master is stored. Specified by bank index (0..5)
# followed by preset index (0.11)
MIXER_PRESET_SLOT = (5,0)

# E1 preset for the mixer (encoded as a JSON string); if None no mixer preset
# is uploaded (and it is as assumed a mixer preset is already present)
MIXER_PRESET = None

# The MIXER uses three MIDI channels: MIDI_MASTER_CHANNEL, MIDI_TRACKS_CHANNEL
# and MIDI_SENDS_CHANNEL.
# Must be smaller than MIDI_EFFECT_CHANNEL
MIDI_MASTER_CHANNEL = 7
MIDI_TRACKS_CHANNEL = 8
MIDI_SENDS_CHANNEL = 9

# Max nr of SENDS
MAX_NO_OF_SENDS = 6

# First MIDI channel used when creating effect/device presets on the fly;
# range of MIDI channels used is
# [MIDI_EFFECT_CHANNEL, .. , MIDI_EFFECT_CHANNEL + MAX_MIDI_CHANNELS-1]
MIDI_EFFECT_CHANNEL = 11

# Limit the number of MIDI channels used in a preset constructed on the fly;
# -1 means all possible MIDI channels are used  (starting from MIDI_CHANNEL
# all the way up to and including channel 16)
MAX_MIDI_EFFECT_CHANNELS = -1

# Amount to rewind or forward by
FORW_REW_JUMP_BY_AMOUNT = 1

# Number of mappable tracks on the E1
NO_OF_TRACKS = 5

# === CHECKING CONFIGURATION

# sanity check on configuration values 
def check_configuration():
    assert MIDI_EFFECT_CHANNEL in range(1,17), f'Onfiguration error: MIDI_EFFECT_CHANNEL set to { MIDI_EFFECT_CHANNEL}.'
    assert MIDI_MASTER_CHANNEL < MIDI_EFFECT_CHANNEL \
        , f'Configuration error: MIDI_MASTER_CHANNEL set to { MIDI_MASTER_CHANNEL}.'
    assert MIDI_TRACKS_CHANNEL < MIDI_EFFECT_CHANNEL \
        , f'Configuration error: MIDI_TRACKS_CHANNEL set to { MIDI_TRACKS_CHANNEL}.'
    assert MIDI_SENDS_CHANNEL < MIDI_EFFECT_CHANNEL \
        , f'Configuration error: MIDI_SENDS_CHANNEL set to { MIDI_SENDS_CHANNEL}.'
    assert (MAX_MIDI_EFFECT_CHANNELS == -1) or \
           (MIDI_EFFECT_CHANNEL + MAX_MIDI_EFFECT_CHANNELS) in range(1,17) \
        , f'Configuration error: MIDI_MAX_EFFECT_CHANNELS set to { MIDI_MAX_EFFECT_CHANNELS}.' 
    assert ORDER in [ORDER_ORIGINAL, ORDER_SORTED, ORDER_DEVICEDICT] \
               , f'Configuration error: ORDER set to { ORDER }.'
    
