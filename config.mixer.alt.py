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

# indicate that control index is not mapped, ie will not listen to Ableton value
# strings
UNMAPPED_ID = -1

# === GENERAL CONFIGURATION CONSTANTS 

# How much debugging information should be logged; higher values
# imply more information. 0 means no logging at all.
DEBUG = 2

# Whether the E1 should send log messages, and if so at which levek of detail
# (-1 is no logging)
E1_LOGGING = -1

# Which port to use to send log messages to (0: Port 1, 1: Port 2, 2: CTRL)
E1_LOGGING_PORT = 2

# Whether created patch info should be dumped (this is useful if you want
# to create your own custom patches for certain devices)
DUMP = False

# Whether to detect the E1 at start up (or assume it's there regardless)
DETECT_E1 = True

# Local directory where dumps are stored (./dumps), user defined
# presets are loaded from (./user-presets), and where to look for the sendmidi
# program.
#
# This is first tried as a directory relative to the user's home directory;
# if that doesn't exist, it is interpreted as an absolute path. If that also
# doesn't exist, then the user home directory is used instead (and ./dumps
# or ./user-presets are not appended to make sure the directory exists).
# (Leading or trailing slash is ignored)
LIBDIR = 'ElectraOne'

# 'reset slot': when selecting this slot on the E1, the remote script is reset
RESET_SLOT = (5,11)

# Configure whether the remote script controls both mixer and effect, the mixer
# or the effect only, or if two E!s are connected each controlling one of them

CONTROL_EITHER = 0
CONTROL_EFFECT_ONLY = 1
CONTROL_MIXER_ONLY = 2
CONTROL_BOTH = 3 # dual E1 mode

CONTROL_MODE = CONTROL_EITHER

# Whether to use the exact value strings Ableton generates for faders
# whose value cannot be easily computed by the E1 itself.
USE_ABLETON_VALUES = True

# === FAST SYSEX UPLOAD 

# full path to the sendmidi command. If None, fast sysex upload is not supported
SENDMIDI_CMD = None
#SENDMIDI_CMD = '/usr/local/bin/sendmidi'

# Remote script input/output port number (0: Port 1, 1: Port 2, 2: CTRL)
E1_PORT = 0
# Name of this port as used by SENDMIDI_CMD
E1_PORT_NAME = 'Electra Controller Electra Port 1'

# === DEVICE APPOINTMENT OPTIONS

# Whether to appoint the currently selected device on a selected track
# (only guaranteed to work if this is the only remote script handling device
# appointment), or only do this when device is explicitly selected
APPOINT_ON_TRACK_CHANGE = True

# Whether to switch immediately from the mixer preset to the effect preset
# whenever a new device is appointed in Ableton, or only switch when explicitly
# requested by the user by pressing the upper right preset request button on
# the E1 
SWITCH_TO_EFFECT_IMMEDIATELY = True

# === EFFECT/DEVICE CONFIGURATION CONSTANTS

# Length of time (in 100ms increments) between successive refreshes of
# controls on the E1 whose string values need to be provided by Abelton
EFFECT_REFRESH_PERIOD = 2

# E1 preset slot where the preset controlling the currently selected device
# is stored. Specified by bank index (0..5) followed by preset index (0.11)
EFFECT_PRESET_SLOT = (5,1)

# Default color to use for controls in a generated preset
PRESET_COLOR = 'FFFFFF'

ORDER_ORIGINAL = 0   # order as reported by Live
ORDER_SORTED = 1     # sort by parameter name
ORDER_DEVICEDICT = 2 # order according to the standard remote script preferred order as defined by DEVICE_DICT in the Ableton Live rmeote script framework

# Specify the order in which parameters should appear in an automatically
# created preset for the currently selected device. If order is
# ORDER_DEVICEDICT, parameters NOT in DEVICE_DICT are NOT included in the preset
ORDER = ORDER_DEVICEDICT

# A dictionary, keyed by device name, containing for each device a list of
# names of parameters to ignore when constructing presets on the fly.
# The list with key "ALL" contains the names of parameters to ignore for all
# presets constructed on the fly. Can e.g. be used to exclude the "Device On"
# button normally included.
# e.g. PARAMETERS_TO_IGNORE = {"ALL": ["Device On"]}
PARAMETERS_TO_IGNORE = {}

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

# The MIXER uses three MIDI channels: MIDI_MASTER_CHANNEL, MIDI_TRACKS_CHANNEL
# and MIDI_SENDS_CHANNEL.
# Must be smaller than MIDI_EFFECT_CHANNEL
MIDI_MASTER_CHANNEL = 7
MIDI_TRACKS_CHANNEL = 8
MIDI_SENDS_CHANNEL = 9

# Max nr of SENDS
MAX_NO_OF_SENDS = 5

# Change this to manage a different EQ like device on every track
# Specify the device.class_name here
TRACK_EQ_DEVICE_NAME = 'ChannelEq'

# Specify the CC-map here (as in Devices.py)
# The actual cc_no for a parameter is obtained by adding the track offset
# to the base defined here. (see _my_cc() )
TRACK_EQ_CC_MAP = { 
              'Low Gain'   : (UNMAPPED_ID, MIDI_TRACKS_CHANNEL, 1, 25)
            , 'Mid Gain'   : (UNMAPPED_ID, MIDI_TRACKS_CHANNEL, 1, 20)
            , 'Mid Freq'   : (UNMAPPED_ID, MIDI_TRACKS_CHANNEL, 1, 15)
            , 'High Gain'  : (UNMAPPED_ID, MIDI_TRACKS_CHANNEL, 1, 10)
            , 'Gain'       : (UNMAPPED_ID, MIDI_TRACKS_CHANNEL, 0, 64)
            }

# Change this to manage a different EQ like device on the master track
# Specify the device.class_name here
MASTER_EQ_DEVICE_NAME = 'ChannelEq'

# Specify the CC-map here (as in Devices.py)
MASTER_EQ_CC_MAP = {
              'Low Gain':    (UNMAPPED_ID, MIDI_MASTER_CHANNEL, 1, 6)
            , 'Mid Gain':    (UNMAPPED_ID, MIDI_MASTER_CHANNEL, 1, 5)
            , 'Mid Freq':    (UNMAPPED_ID, MIDI_MASTER_CHANNEL, 1, 4)
            , 'High Gain':   (UNMAPPED_ID, MIDI_MASTER_CHANNEL, 1, 3)
            , 'Gain':        (UNMAPPED_ID, MIDI_MASTER_CHANNEL, 1, 7)
            }

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
    
