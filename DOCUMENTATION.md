---
title: Technical Documentation of the Aleton Live Remote Script for the Electra One 
author: Jaap-Henk Hoepman (info@xot.nl)
---

# Introduction 

This is the *technical* documentation describing the internals of the Aleton Live Remote Script for the Electra One. For the user guide, see the [Read Me](README). 

Two parts
- a [mixer](#the-mixer) 
- [current device](#device-control)

# Some background

[Live 11.0 API](https://structure-void.com/PythonLiveAPI_documentation/Live11.0.xml)

## Remote scripts

```c_instance```

## MIDI / Ableton


Only the first 32 CC parameters can be assigned to be 14bit controllers (even though there would be space for more starting at slot 64, but unfortunately neither Ableton nor the E1 fully support that).

*control* a thing on the E1
*parameter* the Live thing controlled




### MIDI mapping

All Live *device* parameters (including buttons) can be mapped to respond to incoming MIDI CC messages. This is done using:

```
Live.MidiMap.map_midi_cc(midi_map_handle, parameter, midi_channel, cc_no, map_mode, avoid_takeover)
```

where:

- ```midi_map_handle``` is the handle passed by Live to ```build_midi_map``` (presumably containing a reference to the MIDI map that Live uses internally to decide how to handle MIDI messages that come in over the MIDI input port specified for this particular MIDI Remote Script).
- ```parameter``` (e.g. obtained as a member of ```device.parameters```) is a reference to the Live python object connected to the particular Live parameter to be controlled.
- ```midi_channel``` is the MIDI channel on which to listen to CC parameters. Note that internally MIDI channels are numbered from 0-15, so the MIDI channel to pass is *one less* than the MIDI channel typically used in documentation (where it ranges from 1-16).
- ```cc_no``` is the particular CC parameter number to listen to. 
- ```map_mode``` defines how to interpret incoming CC values. Possible ```map_mode``` values are defined in ```Live.MidiMap.MapMode```; we use it only to define whether CC values will be 7 bit (one byte) or 14 bit (two bytes, sent using separate CC messages, see above).
- ```avoid_takeover```: not clear how/if this parameter is honoured.

Once mapped, there is nothing much left to do: incoming MIDI CC messages that match the map are immediately processed by Live and result in the desired parameter update. The remote script does not get to see these MIDI messages. Even better: any change to a mapped Live parameter (either through the Live UI or through another remote controller) is automatically sent out as the mapped MIDI CC parameter straight to the (E1) controller. Again, the remote script does not get to see these MIDI remote messages. There is *one* thing the remote script must do itself unfortunately (but only *once* per mapped parameter): when mapping a parameter to control this way, the current value of the parameter must be sent to the E1 (as a MIDI CC message) to bring the controller on the E1 in sync with the current value of the Live parameter. After that, the remote script is literally out of the loop

### MIDI forwarding

For buttons on *non-device* parameters this is not the case unfortunately (luckily the volume sliders, pan and send pots on tracks *can* be mapped as described above). For these parameters a different kind of mapping needs to be set up using

```
Live.MidiMap.forward_midi_cc(script_handle, midi_map_handle,midi_channel,cc_no)
```

The parameters to this call are like the one above, except:

- ```script_handle``` handle to this remote script (needed to call it's ```receive_midi``` method, see below). It is obtained using ```c_instance.handle()```  where ```c_instance``` is the parameter that Live passes to the call ```create_instance``` in ```__init__.py```. 

Once mapped, incoming MIDI CC messages that match the map are forwarded to the remote script that registered this mapping by calling its ```receive_midi``` method. The parameter to this call is a python *sequence* (not a list) of all bytes in the message, including the MIDI status byte etc. It is the responsibility of the remote script to process these messages and ensure something happens.

In the E1 remote script, each class (that needs to set up MIDI CC message forwarding)  defines a (constant) dictionary ```_CC_HANDLERS``` containing for each (midi_channel,cc_no) pair the function responsible for processing that particular incoming MIDI message.

For example, ```TransportController.py``` defines

```
self._CC_HANDLERS = {
	   (MIDI_MASTER_CHANNEL, REWIND_CC) : self._do_rewind
	,  (MIDI_MASTER_CHANNEL, FORWARD_CC) : self._do_forward
	,  (MIDI_MASTER_CHANNEL, PLAY_STOP_CC) : self._do_play_stop
	,  (MIDI_MASTER_CHANNEL, RECORD_CC) : self._do_record
	}
```

The ```process_midi``` function in the same class (called by the global ```receive_midi_function``` but with the midi channel, CC parameter number and value already parsed) uses this dictionary to find the correct handler for the incoming MIDI CC message automatically. And the ```build_midi_map``` method in the same class uses the same dictionary to set up MIDI forwarding using ```Live.MidiMap.forward_midi_cc```.

### Listeners

For such *non-device* parameters the remote script *also* needs to monitor any changes to the parameter in Live, and forward them to the E1 controller (to keep the two in sync). Unlike real device parameters, the mapping through ```Live.MidiMap.forward_midi_cc``` unfortunately does not instruct Live to automatically create the required MIDI CC message. The remote script needs to do that now continually (like it already needs to that for *all* mapped parameters *once* at the moment they are mapped).

For each of such *non-device* parameters (of which Live thinks you might be interested to monitor a value change) live offers a function to add (and remove) *listeners* for this purpose. For example

```track.add_mute_listener(on_mute_changed)```

registers the function ```on_mute_changed``` (this is a reference, not a call!) 
to be called whenever the 'mute' button on track ```track``` changes. This function must then query the status of parameter (the mute button in this case) and send the appropriate MIDI CC message to the E1 controller to change the displayed value of the control there. 

Unlike MIDI mappings (that appear to be destroyed whenever a new MIDI map is being requested through ```c_instance.request_rebuild_midi_map()```), these listeners are permanent. Therefore they need to be explicitly removed as soon as they are no longer needed. In the example above, this is achieved by calling

```track.remove_mute_listener(on_mute_changed)```

In the E1 remote script, each class defines a ```_add_listeners()``` and ```_ remove_listeners()``` method that handle this for any parameters/listeners this class is responsible for.

### Initiating MIDI mapping

It is the responsibility of the remote script to ask Live to start the process of building a MIDI map for the remote script. This makes sense because only the remote script can tell whether things changed in such a way that a remap is necessary. The remote script can do so by calling  ```c_instance.request_rebuild_midi_map()```. Live will remove *all* existing MIDI mappings (for this particular remote script only). Live will then ask the remote script to build a new map by calling  ```build_midi_map(midi_map_handle``` (which should be a method defined by the remote script object).


# The mixer

The mixer preset can control the transport (play/stop, record, rewind and forward), the master track (pan, volume, cue volume, solo), at most six return tracks (pan, volume, mute) and five tracks (pan, volume, mute, solo, arm, and at most six sends). The tracks controlled can be switched. Also, each track (audio, MIDI but also the master) can contain a Live Channel EQ device. If present it is automatically mapped to controls on the default E1 mixer preset as well.

The mixer comes with a default E1 mixer preset that matches the MIDI map defined below. But the layout, value formatting, colours etc. can all be changed. You can even remove certain controls from the preset to simplify it. If you are really adventurous you can replace the default EQ controls based on Live's Channel EQ with a different default device on the audio, MIDI and master tracks by changing the ```EQ_DEVICE_NAME``` and ```EQ_CC_MAP``` in ```MasterController.py``` and ```TrackController.py``` (see there for details). 
All that matters is that you do not change the MIDI channel assignments (ie the E1 devices), the CC parameter numbers, the CC minimum and maximum values, and whether it is a 7bit or 14bit controller.


## Value mapping

For certain controls, the default mixer preset contains some additional formatting instructions (using the E1 LUA based formatting functions).

Pan
: mapped to 50L - C - 50L

Volume
: Live considers the CC value 13926 to be 0dB. The minimum CC value is 0, corresponding to -infinity. The maximum CC value equals 16383, corresponding to 6.0 db. You would therefore think that the function to map (MIDI) values to real display values is 6* (value-13926) / 2458), but this becomes less accurate below -20dB or so. The display value range is set to -435..76 (to stay just within 511 to ensure that the E1 actually even shows a value) with a default value of 0. With these specific range settings, the actual Live parameter value 0 dB is mapped to 0 on the E1.

High/Mid/Low/Output of the Channel Eq
: The displayed value range is specified as -150..150 (or -120..120 for some); the formatter divides this by 10 and turns it into a float.

Note that all these sliders do not operate at their full 14bit potential due to the fact that the display value range is restricted (to ensure that values are shown on the E1), while the E1 unfortunately *only* sends out MIDI CC messages when the *display* value changes (not when the underlying MIDI value changes that comes from the true 14bit range). A bug report has been filed for this at Electra. As soon as any of these restrictions are lifted, the preset will be updated.

## The Mixer MIDI MAP

Sliders are 14 bit, all other controls are 7bit, essentially just buttons sending 0 for off and  127 for on values. Controllers are mapped as follows.


### Master, return tracks and the transport.

The master track, return tracks and the transport are controlled through MIDI channel ```MIDI_MASTER_CHANNEL``` with the following CC parameter assignments. 
At most six return tracks are controlled through the mixer.

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

Legend:
- '-' refers to an unused slot.
- 'X refers to a 'shadow' CC occupied because of an earlier 14bit CC control.
- The number after a parameter name is the track  offset (relative to the first track being controlled), see table below.
- '-' refers to an unused slot.
- 'X refers to a 'shadow' CC occupied because of an earlier 14bit CC control.

### Tracks

Five tracks are simultaneously controlled through MIDI channel, ```MIDI_TRACKS_CHANNEL```, with the following CC parameter assignments. 

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

### Sends

The sends of the five tracks are controlled over another MIDI channel, ```MIDI_SENDS_CHANNEL```, with the following CC parameter assignments. Note that
not all sends may be present on a track. The first six sends of a track are controlled by the mixer.


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

## Internally

The code to handle the mixer is distributed over the following modules (with their associated class definitions):

```MixerController.py```
: Sets up the other modules (and their classes) below. Handles the previous tracks and next tracks  selection buttons. Distributes incoming MIDI messages to the modules below (see ```receive_midi```). Coordinates the construction of the MIDI map (see```build_midi_map```). Forwards ```update_display``` to each module below. Also keeps track of which five tracks are assigned to the controller (the index of the first track in ```_first_track_index```) and updating the track controllers whenever tracks are added or deleted, or when the user presses the previous and next track buttons.

  FIXME: uploading mixer preset

```TransportController.py```
: Handles the play/stop, record, rewind and forward button. ```update_display()``` (called every 100ms by Live) is used to test whether the rewind or forward button is (still) pressed and move the song play position accordingly (by ```FORW_REW_JUMP_BY_AMOUNT```).

```MasterController.py```
: Handles the master track volume, pan, cue volume and solo on/off parameters. Also sets up control of a Channel EQ device, when present on the master track.

```ReturnController.py```
: Handles one return track, as specified by the ```idx``` (0 for return track A) when created by ```MixerController```. ```MixerController``` will create at most six instances of this controller, the actual number depending on the actual number of return tracks present. Each ```ReturnController``` manages the pan, volume and mute on the return track assigned to it. ```idx``` is used to compute the actual CC parameter number to map to a Live parameter (using the base CC parameter number defined as a constant derived from the tables above).

```TrackController.py```
: Handles one audio or MIDI track, as specified by the ```idc``` (0 for the first track in the song) when created by ```MixerController```. ```MixerController``` will create five instances of this controller (passing an additonal ```offset``` value, in the range 0..4, to tell this controller which of the five tracks it is controlling and hence allowing it to compute the correct CC parameter numbers to map to the parameters in the track assigned to it. Each ```TrackController``` manages the pan, volume, mute, solo and arm button of the assigned track. Also sets up control of a Channel EQ device, when present on this track.

All these modules essentially map/manage controls and parameters using the strategy outlined above. A few more details follow.

### The EQ device

If the master track and the five audio and midi tracks currently managed 
contain a Live Channel EQ device, this one is automatically discovered and mapped to the corresponding controls in the E1 preset 'Channel EQs' page. The mapping essentially follows the exact same method as used by ``` EffectController.py``` (see below) and involves little more than a call to 
```build_midi_map_for_device``` (to map the device parameters to the CC controllers) and ```update_values_for_device``` to initialise the controller values as soon as the device is mapped.

The device mapped can relatively easily be changed by changing the definitions of ```EQ_DEVICE_NAME``` and ```EQ_CC_MAP``` in ```MasterController.py``` and ```TrackController.py```. Of course, the E1 mixer preset must also be updated then.

### Value updates / ```update_display``

Initial value updating uses ```update_display``` to delay the value updates until after the mixer preset is uploaded to the E1. (FIXME)

The class sets the  ```value_update_timer``` variable in its ```__init__``` method. The ```update_display``` method decrements it until it becomes 0. At that time it executes ```_init_controller_values``` that actually sends the controller value updates.

The current delays have not been thoroughly tested yet; and seem to be unnecessary anyway when no actual mixer presets are uploaded.

The actual conversion of Live parameter values to the corresponding MIDI CC values, and the sending of these MIDI CC values over the right channel and with the right CC parameter number is handled by the ```send_parameter_...``` and ```send_midi_...``` functions in ```ElectraOneBase.py```. Care is taken to properly handle 7 bit and 14 bit CC parameters (in the latter case first sending the 7 most significant bits and then the remaining 7 least significant bits in a second MIDI CC message, with CC parameter 32 higher).

For non-quantised parameters (think value sliders), the MIDI value to send for the current device parameter value depends 

- on the type of control (7 bit or 14  bit) and hence their MIDI value range (0..127 vs 0..16383), and 
- the minimum and maximum value of this parameter, and the position of the current value within that range, i.e. $(val - min) / (max - min)$.

The computation of the 7bit MIDI value to send for a quantised parameter works as follows. Quantized parameters have a list of values. For such a list with
$n$ items, item $i$ (starting counting at $0$) has MIDI CC control value
$round(i * 127/(n-1))$.

# Device control

The remote script also manages the currently selected device, through a second dynamic preset (alongside the static mixer preset outlined above).

When the selected device changes

1. A patch for the newly selected device is uploaded to the Electra One.
   - If a user-defined patch exists, that one is used 
   - If not, the parameters for the newly selected device are retrieved from Live (using ```device.parameters```) and automatically converted to a Electra One patch (see ```ElectraOneDumper.py```) in the order specified by ```ORDER```.
   

3. All the parameters in the newly selected device are mapped to MIDI CC (using ```Live.MidiMap.map_midi_cc```). For a user-defined patch, a accompanying CC map must also be defined. This dictionary defines for each device parameter name the corresponding MIDI CC parameter. If a parameter is missing from the dictionary it is not mapped.

   For an automatically converted patch MIDI CC numbers are assigned to parameters in the order in which they are retrieved from the device.
   
3. After this mapping all is set: Ableton will forward incoming MIDI CC changes to the mapped parameter, and will also *send* MIDI CC messages whenever the parameter is changed through the Ableton GUI or another control surface.

Note: for user-defined patches it is possible to assign *several different device parameters* to the same MIDI CC; this is e.g. useful in devices like Echo that have one visible dial in the UI for the left (and right) delay time, but that actually corresponds to three different device parameters (depending on the Sync and Sync Mode settings); this allows one to save on controls in the Electra One patch *and* makes the UI there more intuitive (as it corresponds to what you see in Ableton itself). 

However, changing the parameter value in the Ableton UI does not necessarily update the displayed value in that case... (but this may be due to the fact that a parameter is then wrongly mapped to 14bit (or 7bit)

Note: The current implementation maps all quantized parameters to 7-bit absolute CC values while all non quantized parameters (ie faders and dials) to 14-bit absolute values. User defined patches are responsible for making sure that this convention is followed. ???????

## Order
