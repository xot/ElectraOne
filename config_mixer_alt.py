UNMAPPED_ID = -1

MIDI_MASTER_CHANNEL = 7
MIDI_TRACKS_CHANNEL = 8
MIDI_SENDS_CHANNEL = 9

# Max nr of SENDS
MAX_NO_OF_SENDS = 5

# Number of mappable tracks on the E1
NO_OF_TRACKS = 5

# TrackController CCs  (see DOCUMENTATION.md)
# - On MIDI_TRACKS_CHANNEL

PAN_CC = 0
VOLUME_CC = 5
MUTE_CC = 116   
SOLO_CUE_CC = 84
ARM_CC = 89

DEVICE_SELECTION_CC = None

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

# Sends (see DOCUMENTATION.md)
# - On MIDI_SENDS_CHANNEL

SENDS_CC = 0  
PADS_CC = None
SESSION_CLIP_SLOT_CC = None
SESSION_SCENE_SLOT_CC = None
NO_OF_SESSION_ROWS = 0

# Transport controller CCs (see DOCUMENTATION.md)
# - On MIDI_MASTER_CHANNEL

PLAY_STOP_CC = 64
RECORD_CC = 65
POSITION_CC = 66
TEMPO_CC = 67

TAP_TEMPO_CC = None
NUDGE_DOWN_CC = None
NUDGE_UP_CC = None
METRONOME_CC = None
QUANTIZATION_CC = None

ROOT_NOTE_CC = None
SCALE_NAME_CC = None
SCALE_MODE_CC = None

ARRANGEMENT_OVERDUB_CC = None
SESSION_AUTOMATION_RECORD_CC = None
RE_ENABLE_AUTOMATION_ENABLED_CC = None
CAPTURE_MIDI_CC = None
SESSION_RECORD_CC = None

LOOP_START_CC = None
PUNCH_IN_CC = None
LOOP_CC = None
PUNCH_OUT_CC = None
LOOP_LENGTH_CC = None

UNDO_CC = None
REDO_CC = None

# MixerController CCs (see DOCUMENTATION.md)
# - On MIDI_MASTER_CHANNEL

PREV_TRACKS_CC = 68
NEXT_TRACKS_CC = 69
PAGE_UP_CC = None
PAGE_DOWN_CC = None

# Returns (see DOCUMENTATION.md)
# - On MIDI_MASTER_CHANNEL

RETURNS_PAN_CC = 10 
RETURNS_VOLUME_CC = 16
RETURNS_MUTE_CC = 70
RETURNS_SOLO_CUE_CC = 76

RM_DEVICE_SELECTION_CC = None

# Master (see DOCUMENTATION.md)
# - On MIDI_MASTER_CHANNEL

MASTER_PAN_CC = 0
MASTER_VOLUME_CC = 1
MASTER_CUE_VOLUME_CC = 2
MASTER_SOLO_CC = 9

MASTER_DEVICE_SELECTION_CC = None

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


