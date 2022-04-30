---
title: Technical Documentation Aleton Live Remote Script for the Electra One 
author: Jaap-Henk Hoepman (info@xot.nl)
date: 
---

# Introduction 

This is the *technical* documentation describing the internals of the Aleton Live Remote Script for the Electra One.

Two parts
- a mixer
- current device

# The mixer

Layout arbitary; also internal value repr.
Not all controls need to be in the preset -> simplify

## Value mapping

- Pan
: mapped to 50L - C - 50L
- Volume
: Live considers 13926 to be 0dB. The minimum value is 0, corresponding to -\infty. The maximum equals 16383, corresponding to 6.0 db. So the function to map (MIDI) values to real values is 6* (value-13926) / 2458)

## MIDI MAP

Sliders are 14 bit, all other controls are 7bit, essentially just buttons sending 0 for off and  127 for on values.

Only the first 32 CC parameters can be assigned to be 14bit controllers (even though there would be space for more starting at slot 64, but unfortunately neither Ableton nor the E1 fully support that).

### Master, return tracks and the transport.

The master track, return tracks and the transport are controlled through MIDI channel ```MIDI_MASTER_CHANNEL``` with the following CC parameter assignments. 

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
|  64 | Play/Stop  | Record     | Rewind     | Forward    | 
|  68 | Prev Trcks | Next Trcks | RTRN Mut A | RTRN Mut B |
|  72 | RTRN Mut C | RTRN Mut D | RTRN Mut E | RTRN Mut F |
|  76 | -          | -          | -          | -          | 
|  80 | -          | -          | -          | -          | 
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

- '-' refers to an unused slot.
- 'X refers to a 'shadow' CC occupied because of an earlier 14bit CC control.


### Tracks

Tracks are controlled through two MIDI channels. The first MIDI channel, ```MIDI_TRACKS_CHANNEL```, has the following CC parameter assignments. 

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
|  96 | X          | X          | X          | X          | X          |
| 101 | -          | -          | -          | -          | -          | 
| 106 | -          | -          | -          | -          | -          | 
| 111 | -          | -          | -          | -          | -          | 
| 116 | Mute   0   | Mute   1   | Mute   2   | Mute   3   | Mute   4   |
| 121 | EQ Rmble 0 | EQ Rmble 1 | EQ Rmble 2 | EQ Rmble 3 | EQ Rmble 4 |
| 126 | -
| 127 | -

Note that EQ Out i is mapped as a 7bit controller due to space constraints.

Legend:
- The number after a parameter name is the track  offset (relative to the first track being controlled).
- '-' refers to an unused slot.
- 'X refers to a 'shadow' CC occupied because of an earlier 14bit CC control.

The second MIDI channel, ```MIDI_SENDS_CHANNEL```, controls a varying number of send controls for each track, and has the following CC parameter assignments. 

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

# Basic architecture

When the selected device changes

1. A patch for the newly selected device is uploaded to the Electra One.
   - If a user-defined patch exists, that one is used 
   - If not, the parameters for the newly selected device are retrieved and automatically converted to a Electra One patch (see ElectraOneDump) in the order in which they are retrieved from the device (using ```device.parameters```)
   
3. All the parameters in the newly selected device are mapped to MIDI CC (using ```Live.MidiMap.map_midi_cc```). For a user-defined patch, a accompanying CC map must also be defined. This dictionary defines for each device parameter name the corresponding MIDI CC parameter. If a parameter is missing from the dictionary it is not mapped.

   For an automatically converted patch MIDI CC numbers are assigned to parameters in the order in which they are retrieved from the device.
   
3. After this mapping all is set: Ableton will forward incoming MIDI CC changes to the mapped parameter, and will also *send* MIDI CC messages whenever the parameter is changed through the Ableton GUI or another control surface.

Note: for user-defined patches it is possible to assign *several different device parameters* to the same MIDI CC; this is e.g. useful in devices like Echo that have one visible dial in the UI for the left (and right) delay time, but that actually corresponds to three different device parameters (depending on the Sync and Sync Mode settings); this allows one to save on controls in the Electra One patch *and* makes the UI there more intuitive (as it corresponds to what you see in Ableton itself). 

However, changing the parameter value in the Ableton UI does not necessarily update the displayed value in that case... (but this may be due to the fact that a parameter is then wrongly mapped to 14bit (or 7bit)

Note: The current implementation maps all quantized parameters to 7-bit absolute CC values while all non quantized parameters (ie faders and dials) to 14-bit absolute values. User defined patches are responsible for making sure that this convention is followed.
