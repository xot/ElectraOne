# The basic mixer MIDI map

## Specific choices made in the mixers supplied with the remote script

Faders (except the Channel EQ Output faders) are 14 bit, all other controls are 7bit, which are essentially just buttons sending 0 for off and 127 for on values. Controls are mapped to CC as explained below. 

For the standard mixer (```Mixer.eproj```) we assume 5 tracks (```NO_OF_TRACKS = 5```) and at most 6 return tracks (```MAX_NO_OF_SENDS = 6```). The CC map is defined  setting the constants to their values as documented in ```config_mixer.py```.

For the alternative map (```Mixer.alt.eproj```, with transport controls on each page) we assume 5 tracks (```NO_OF_TRACKS = 5```) and at most 5 return tracks (```MAX_NO_OF_SENDS = 5```). The master and track Channel Eq devices do not have a highpass control in their mapping. Apart from that there are no other differences in the CC assignments themselves. The CC map is defined setting the constants to their values as documented in ```config_mixer_alt.py```.


## Master, return tracks and the transport.

The master track (including its optional ChannelEq device), return tracks and the transport are controlled through MIDI channel ```MIDI_MASTER_CHANNEL``` with the following CC parameter assignments. 
At most six return tracks (labelled A to E below) are controlled through the mixer.

|  CC | Controls   |            |            |            |
|----:|:-----------|:-----------|:-----------|:-----------|
|   0 | Pan        | Volume     | Cue Volume | EQ High    |
|   4 | EQ Mid F   | EQ Mid     | EQ Low     | EQ Out     |
|   8 | EQ Rumble  | Solo       | RTRN Pan A | RTRN Pan B |
|  12 | RTRN Pan C | RTRN Pan D | RTRN Pan E | RTRN Pan F |
|  16 | RTRN Vol A | RTRN Vol B | RTRN Vol C | RTRN Vol D |
|  20 | RTRN Vol E | RTRN Vol E | -          | -          |
|  24 | -          | -          | -          | -          | 
|  28 | -          | -          | -          | -          |
|  32 | X          | X          | X          | X          | 
|  36 | X          | X          | X          | X          | 
|  40 | -          | -          | X          | X          | 
|  44 | X          | X          | X          | X          | 
|  48 | X          | X          | X          | X          | 
|  52 | X          | X          | -          | -          |
|  56 | -          | -          | -          | -          | 
|  60 | -          | -          | -          | -          | 
|  64 | Play/Stop  | Record     | Position   | Tempo      | 
|  68 | Prev Trcks | Next Trcks | RTRN Mut A | RTRN Mut B |
|  72 | RTRN Mut C | RTRN Mut D | RTRN Mut E | RTRN Mut F |
|  76 | RTRN S/C A | RTRN S/C B | RTRN S/C C | RTRN S/C D | 
|  80 | RTRN S/C E | RTRN S/C F | -          | -          | 
|  84 | -          | -          | -          | -          | 
|  88 | -          | -          | -          | -          | 
|  92 | -          | -          | -          | -          | 
|  96 | -          | -          | -          | -          | 
| 100 | -          | -          | -          | -          | 
| 104 | -          | -          | -          | -          | 
| 108 | -          | -          | -          | -          | 
| 112 | -          | -          | -          | -          | 
| 116 | -          | -          | -          | -          | 
| 120 | -          | -          | -          | -          | 
| 124 | -          | -          | -          | -          | 

Legend:

- '-' refers to an unused slot.
- 'X refers to a 'shadow' CC occupied because of an earlier 14bit CC control.
- (For tables below) The number after a parameter name is the track  offset (relative to the first track being controlled).

## Tracks

Five tracks (each with an optional ChannelEq device) are simultaneously controlled through MIDI channel ```MIDI_TRACKS_CHANNEL```, with the following CC parameter assignments (which assures that the CC's for the same control on adjacent tracks differ by 1; in other words the CC for the control on track x equals the CC for the control on track 0 + x)

|  CC | Controls   |            |            |            |            |
|----:|:-----------|:-----------|:-----------|:-----------|:-----------|
|   0 | Pan 0      | Pan 1      | Pan 2      | Pan 3      | Pan 4      |
|   5 | Volume 0   | Volume 1   | Volume 2   | Volume 3   | Volume 4   |
|  10 | EQ Hi  0   | EQ Hi  1   | EQ Hi  2   | EQ Hi  3   | EQ Hi  4   |
|  15 | EQ Mid F 0 | EQ Mid F 1 | EQ Mid F 2 | EQ Mid F 3 | EQ Mid F 4 |
|  20 | EQ Mid 0   | EQ Mid 1   | EQ Mid 2   | EQ Mid 3   | EQ Mid 4   |
|  25 | EQ Low 0   | EQ Low 1   | EQ Low 2   | EQ Low 3   | EQ Low 4   |
|  30 | -          | 
|  31 | -          | 
|  32 | X          | X          | X          | X          | X          |
|  37 | X          | X          | X          | X          | X          |
|  42 | X          | X          | X          | X          | X          |
|  47 | X          | X          | X          | X          | X          |
|  52 | X          | X          | X          | X          | X          |
|  57 | X          | X          | X          | X          | X          |
|  62 | -          | 
|  63 | -          | 
|  64 | EQ Out 0   | EQ Out 1   | EQ Out 2   | EQ Out 3   | EQ Out 4   |
|  69 | -          | -          | -          | -          | -          | 
|  74 | -          | -          | -          | -          | -          | 
|  79 | -          | -          | -          | -          | -          | 
|  84 | Solo/C 0   | Solo/C 1   | Solo/C 2   | Solo/C 3   | Solo/C 4   |
|  89 | Arm    0   | Arm    1   | Arm    2   | Arm    3   | Arm    4   |
|  94 | -          |
|  95 | -          |
|  96 | -          | -          | -          | -          | -          |
| 101 | -          | -          | -          | -          | -          | 
| 106 | -          | -          | -          | -          | -          | 
| 111 | -          | -          | -          | -          | -          | 
| 116 | Mute   0   | Mute   1   | Mute   2   | Mute   3   | Mute   4   |
| 121 | EQ Rmble 0 | EQ Rmble 1 | EQ Rmble 2 | EQ Rmble 3 | EQ Rmble 4 |
| 126 | -
| 127 | -

Note that EQ Out i is mapped as a 7bit controller due to space constraints. (Otherwise we would have needed to claim another MIDI channel for an additional 14bit CC slot.)

## Sends

The sends of the five tracks are controlled over another MIDI channel, ```MIDI_SENDS_CHANNEL```, with the following CC parameter assignments. Note that
not all sends may be present on a track. The first six sends of a track are controlled by the mixer. CC assignments are such that the x-th send on track y equals  x*<no-of-sends> + y


|  CC | Controls   |            |            |            |            |
|----:|:-----------|:-----------|:-----------|:-----------|:-----------|
|   0 | Send A 0   | Send A 1   | Send A 2   | Send A 3   | Send A 4   |
|   5 | Send B 0   | Send B 1   | Send B 2   | Send B 3   | Send B 4   |
|  10 | Send C 0   | Send C 1   | Send C 2   | Send C 3   | Send C 4   |
|  15 | Send D 0   | Send D 1   | Send D 2   | Send D 3   | Send D 4   |
|  20 | Send E 0   | Send E 1   | Send E 2   | Send E 3   | Send E 4   |
|  25 | Send F 0   | Send F 1   | Send F 2   | Send F 3   | Send F 4   |
|  30 | -
|  31 | - 
|  32 | X          | X          | X          | X          | X          |
|  37 | X          | X          | X          | X          | X          |
|  42 | X          | X          | X          | X          | X          |
|  47 | X          | X          | X          | X          | X          |
|  52 | X          | X          | X          | X          | X          |
|  57 | X          | X          | X          | X          | X          |
|  62 | -          | 
|  63 | -          | 
