UNMAPPED_ID = 1

MIDI_MASTER_CHANNEL = 7
MIDI_TRACKS_CHANNEL = 8
MIDI_SENDS_CHANNEL = 9

# Max nr of SENDS
MAX_NO_OF_SENDS = 6

# Number of mappable tracks on the E1
NO_OF_TRACKS = 5

# TrackController CCs  (see DOCUMENTATION.md)
# - On MIDI_TRACKS_CHANNEL

PAN_CC = 0
VOLUME_CC = 5
MUTE_CC = 116   
SOLO_CUE_CC = 84
ARM_CC = 89

# Change this to manage a different EQ like device on every track
# Specify the device.class_name here
TRACK_EQ_DEVICE_NAME = 'ChannelEq'

# Specify the CC-map here (as in Devices.py)
# The actual cc_no for a parameter is obtained by adding the track offset
# to the base defined here. (see _my_cc() )
TRACK_EQ_CC_MAP = { 
              'Highpass On': (UNMAPPED_ID, MIDI_TRACKS_CHANNEL, 0, 121)
            , 'Low Gain'   : (UNMAPPED_ID, MIDI_TRACKS_CHANNEL, 1, 25)
            , 'Mid Gain'   : (UNMAPPED_ID, MIDI_TRACKS_CHANNEL, 1, 20)
            , 'Mid Freq'   : (UNMAPPED_ID, MIDI_TRACKS_CHANNEL, 1, 15)
            , 'High Gain'  : (UNMAPPED_ID, MIDI_TRACKS_CHANNEL, 1, 10)
            , 'Gain'       : (UNMAPPED_ID, MIDI_TRACKS_CHANNEL, 0, 64)
            }

# Sends (see DOCUMENTATION.md)
# - On MIDI_SENDS_CHANNEL

SENDS_CC = 0  

# Transport controller CCs (see DOCUMENTATION.md)
# - On MIDI_MASTER_CHANNEL

PLAY_STOP_CC = 64
RECORD_CC = 65
POSITION_CC = 66
TEMPO_CC = 67

# MixerController CCs (see DOCUMENTATION.md)
# - On MIDI_MASTER_CHANNEL

PREV_TRACKS_CC = 68
NEXT_TRACKS_CC = 69

# Returns (see DOCUMENTATION.md)
# - On MIDI_MASTER_CHANNEL

RETURNS_PAN_CC = 10 
RETURNS_VOLUME_CC = 16
RETURNS_MUTE_CC = 70
RETURNS_SOLO_CUE_CC = 76

# Master (see DOCUMENTATION.md)
# - On MIDI_MASTER_CHANNEL

MASTER_PAN_CC = 0
MASTER_VOLUME_CC = 1
MASTER_CUE_VOLUME_CC = 2
MASTER_SOLO_CC = 9

# Change this to manage a different EQ like device on the master track
# Specify the device.class_name here
MASTER_EQ_DEVICE_NAME = 'ChannelEq'

# Specify the CC-map here (as in Devices.py)
MASTER_EQ_CC_MAP = { 
              'Highpass On': (UNMAPPED_ID, MIDI_MASTER_CHANNEL, 0, 8)
            , 'Low Gain':    (UNMAPPED_ID, MIDI_MASTER_CHANNEL, 1, 6)
            , 'Mid Gain':    (UNMAPPED_ID, MIDI_MASTER_CHANNEL, 1, 5)
            , 'Mid Freq':    (UNMAPPED_ID, MIDI_MASTER_CHANNEL, 1, 4)
            , 'High Gain':   (UNMAPPED_ID, MIDI_MASTER_CHANNEL, 1, 3)
            , 'Gain':        (UNMAPPED_ID, MIDI_MASTER_CHANNEL, 1, 7)
            }

