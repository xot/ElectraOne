---
title: Technical Documentation of the Aleton Live Remote Script for the Electra One 
author: Jaap-Henk Hoepman (info@xot.nl)
---

# Introduction 

This is the *technical* documentation describing the internals of the Ableton Live Remote Script for the Electra One (aka E1). For the user guide, see the [Read Me](README). 

The remote script essentially supports two control surfaces
- a [mixer](#the-mixer) with a E1 preset in bank 6 slot 1 (```MIXER_PRESET_SLOT```), and
- a [current device](#device-control) with a E1 preset in bank 6 slot 2 (```EFFECT_PRESET_SLOT```).

(It also supports two interconnected E1s where one controls the current device and the other controls the mixer.) Their implementation is described further below, after a brief introduction on 
remote scripts and MIDI.

# Some background

## Ableton Live API

Ableton Live exposes a lot of its functionality for remotely controlling it through the so-called Live API. In essence any part of the interface, or most of the contents of a song all the way to the individual clip level can be accessed, not only for reading but also for writing!

Ableton officially only supports the Live API through [Max for Live](https://docs.cycling74.com/max8/vignettes/live_object_model). However, that information is mostly valid for Remote Scripts too, except that 
the paths in a MIDI Remote Script are slightly different from the paths mentioned in the Max for Live documentation:

- the root path for most of the API is listed as ```live_set```, but in a MIDI Remote Script, this is ```self.song()```
- also, paths in MIDI Remote Scripts don't use spaces but use dots, e.g. ```self.song().view.selected_track```.
- the symbol N in a path means that the part before it returns a list. So ```live_set tracks N ``` should be translated to ```self.song().tracks[i]``` to return the i-th track.

Note that (that version of) the Live API itself does not contain all the necessary information to write Remote Scripts: it does not offer any information on MIDI mapping, or the interface between Live and the remote script (i.e the ```c_instance``` object passed to the Remote Script by Live), which is necessary to understand how to send and receive MIDI messages, how to detect device 'appointment' (selection) changes, or how to indeed map MIDI (and how that works, exactly).

Because no official documentation existed, in the past people have reverse engineered the [Live API reference documentation](https://structure-void.com/PythonLiveAPI_documentation/Live11.0.xml) which shows the Python interface of most of Live's externally callable functions (most of the time without any documentation, however).


## Remote scripts

Remote scripts are the interface between the *controls* on an external MIDI controller and the device *parameters* and other Live UI interface elements. It ensures that Live responds to a user interacting with the controller, and ensures that information displayed by the controller is in sync with Live.

Communication between Live and the MIDI controller takes place using MIDI, and a remote scripts is assigned a specific input port (to listen for MIDI events from the controller) and output port (to send MIDI events to the controller). MIDI events on other ports are invisible to the remote script.

A remote script is written for a specific remote controller. As such the remote script knows the specific assignment of MIDI *events* (MIDI channel, event type and event number) to controls on the external controller. I.e. it knows what MIDI events will be generated when a dial on the controller is turned, a button is pushed or a key is pressed. The remote script (written in [Python](https://docs.python.org/3/)) uses this information to make Ableton Live respond appropriately to a controller change (for example by calling the appropriate function in the Live API), and also to send status information back to the controller.

A typical use case (and what makes remote scripts so useful and important to have for an external controller) is to map the controls on the external controller automatically to the currently selected device in Live. 

This is the general idea. Unfortunately, no official information on how to implement a remote script is available. Luckily, twelve years ago already Hanz Petrov wrote an excellent [introduction to remote scripts](http://remotescripts.blogspot.com/2010/03/introduction-to-framework-classes.html), and others made the effort of decompiling all officially supported [remote scripts in a Live distribution](https://github.com/gluon/AbletonLive11_MIDIRemoteScripts). Especially the latter resource proved to be invaluable to figure out exactly how to program a remote script.

### Python package

Every remote script is a separate [Python package](https://docs.python.org/3/tutorial/modules.html) contained in a separate directory in the remote scripts folder. User defined remote scripts are stored in ```~/Music/Ableton/User Library/Remote Scripts/``` on MacOS and ```~\Documents\Ableton\User Library\Remote Scripts``` on Windows. The name of the directory determines the name Live uses for the remote script. In our case, the ElectraOne remote script is therefore stored in the directory ```ElectraOne```. 

Ableton Live 11 support Python 3.

Every remote script Python package must contain a file ```__init.py__``` that should define two functions

- ```create_instance``` which is passed a parameter ```c_instance```. This must return an object implementing the remote script functionality (see below). It is called exactly once when opening a new live set (song), or when the remote script is attached to Live in the Preferences dialog. 
- ```get_capabilities``` that returns a dictionary with properties apparently used by Live to determine what capabilities the remote script supports, although I have not been able to find any information about what this should contain and how it is used.

Essentially, the object returned by ```create_instance``` allows Live to send instructions to (i.e. call methods on) the remote script. It is the interface from Live to the remote script. This is used by Live to tell the remote script to update the display, or to send it MIDI events.

The parameter ```c_instance``` on the other hand allows the remote script to send instructions to (i.e. call methods on) Live. It is the interface from the remote script back to Live. It is used, for example, to tell Live to add a MIDI mapping, or to send MIDI events to the external controller.

### Initialisation

Remote scripts are initialised whenever Live is started *and* whenever a new song is loaded.

### Threading, asynchrony.

The remote script is put on a separate thread (apparently): even if certain actions take seconds to complete they do not interfere with audio processing.

But within a remote script no threading appears to take place. However, sending MIDI appears to be asynchronous. That is to say: a call to ```send_midi``` (through the ```c_instance``` object) stores the MIDI bytes in a buffer within Live (who will then send them at its own pace) and immediately returns. Other sources of MIDI may also emit messages and these are interspersed with MIDI sent by the remote script. 

*The following is speculative; I think I've seen this behaviour, but may have misunderstood what is happening*
: For longer messages (i.e. SysEx), if that happens, Live appears to cut the message into 256 byte chunks. It also appears that later (shorter) MIDI messages sent by the remote script may overtake earlier (longer) MIDI messages sent. *If both are SysEx messages, this means the second may corrupt the first.*

Note that you can start threads within the remote script using Python's ```threading``` package! We make use of that in this remote script.

### The remote script object

The remote script object should define the following methods (although if a method is missing, it is simply ignored):

- ```suggest_input_port(self)``` to tell Live the name of the preferred input port name (returned as string).
- ```suggest_output_port(self)``` to tell Live the name of the preferred output port name (returned as string).
- ```suggest_map_mode(self, cc_no, channel)```: Live can ask the script to suggest a map mode for the given CC.
- ```can_lock_to_devices(self)``` to tell Live whether the remote script can be locked to devices (returned as a boolean).
- ```lock_to_device(self, device)``` tells the remote script to lock to a given device (passed as a reference of type ```Live.Device.Device```).
- ```unlock_from_device(self, device)``` tells the remote script to unlock from the given device (passed as a reference of type ```Live.Device.Device```).
- ```toggle_lock(self)``` tell the script to toggle whether it will lock to devices or not; this is a bit weird because you would expect Live itself to handle this (and there is a corresponding ```toggle_lock``` in ```c_instance``` to tell Live to toggle the lock...).
- ```receive_midi(self,midi_bytes)``` is called to pass a single MIDI event (encoded in the *sequence* of bytes midi_bytes) to the remote script. For CC like events this is *only* called when the specific MIDI event was registered by the remote script using ```Live.MidiMap.forward_midi_cc()```. Other incoming MIDI CC like events are ignored and not forwarded to the remote script. SysEx messages are *always* passed to this function.
- ```build_midi_map(self, midi_map_handle)``` asks the remote script to fill the MIDI map in ```midi_map_handle``` (empty when called).
- ```update_display(self)``` is called by Live every 100 ms. Can be used to execute scheduled tasks, like updating the remote controller display (but other uses are of course also possible).
- ```disconnect(self)``` is called right before the remote script gets disconnected from Live, and should be used to perform any cleanup actions.
- ```refresh_state(self)```: Appears to be called only once each time the remote script loaded.
- ```connect_script_instances```: Called after all remote scripts have been loaded. 
        


### The ```c_instance``` object

The ```c_instance``` object defines the following methods (among others, see below: it's interface is not officially documented anywhere):

- ```song(self)``` a reference to the current song and hence essentially to all things accessible through the Live API.
- ```log_message(self,m)``` log a message to the log file.
- ```show_message(self,m)``` show a message in Live's message area in the lower left corner of the Live window.
- ```send_midi(self,m)``` send the MIDI message m, defined as a *sequence* (not a list) of bytes over the output port assigned to the remote script.
- ```request_rebuild_midi_map(self)``` instructs Live to destroy *all* current MIDI mappings and to ask the remote script to construct a fresh map (by calling ```build_midi_map```, see above). This is somewhat asychronous. The way this appears to work is that as soon as the call to the remote script method that calls ```request_rebuild_midi_map(self)``` finishes and returns control back to Live, Live calls ```build_midi_map```.

It's use can be seen when looking at the ```ElectraOneBase.py``` module.

Using Python's ```dir()``` function we can obtain the full signature of ```c_instance```: 

```
['__bool__', 
'__class__', 
'__delattr__', 
'__dict__', 
'__dir__', 
'__doc__', 
'__eq__', 
'__format__', 
'__ge__', 
'__getattribute__', 
'__gt__', 
'__hash__', 
'__init__', 
'__init_subclass__', 
'__le__', 
'__lt__', 
'__module__', 
'__ne__', 
'__new__', 
'__reduce__', 
'__reduce_ex__', 
'__repr__', 
'__setattr__', 
'__sizeof__', 
'__str__', 
'__subclasshook__', 
'__weakref__', 
'full_velocity', 
'handle', 
'instance_identifier', 
'log_message', 
'note_repeat', 
'playhead', 
'preferences', 
'release_controlled_track', 
'request_rebuild_midi_map', 
'send_midi', 
'set_cc_translation', 
'set_controlled_track', 
'set_feedback_channels', 
'set_feedback_velocity', 
'set_note_translation', 
'set_pad_translation', 
'set_session_highlight', 
'show_message', 
'song', 
'toggle_lock', 
'update_locks', 
'velocity_levels']
```

Some additional fields are exposed/accessible depending on what ```get_capabilities()``` in ```__init__.py``` returns!!! E.g. this is what Push2 has available through ```c_instance```: 

```
['launch_external_process',
'process_connected', 
'real_time_mapper', 
'send_model_update',
'set_firmware_version']
``` 
 
Ableton actually provides a large collection of basic Python classes that it uses for the remote scripts officially supported by Live in modules called ```_Framework``` and ```_Generic```. Apart from the definition of 'best-of-bank' parameter sets for devices, the Electra One remote script does not make use of these.

### Memory management

Note: there is something strange going on with memory management in Ableton. Consider for example the memory allocated to Device objects. ```song().appointed_device``` returns alternating memory locations for the same device (e.g. ```<Device.Device object at 0x11da5bed0>``` and ```<Device.Device object at 0x11da5be00>```). When copying such an object to a local variable in the remote script (e.g. ```self._assigned_device``` this then refers to ```<Device.Device object at 0x11da5bf38>```). If the underlying device is deleted from Live, then testing ```self._assigned_device != None``` returns ```False``` (because by deleting the device also ```self._assigned_device``` is considered equal to ```None```).


## MIDI / Ableton


### MIDI mapping

Almost all Live *device* parameters (including most buttons, in fact all parameters returned by ```device.parameters```) can be mapped to respond to incoming MIDI CC messages. This is done using:

```
Live.MidiMap.map_midi_cc(midi_map_handle, parameter, midi_channel, cc_no, map_mode, avoid_takeover)
```

where:

- ```midi_map_handle``` is the handle passed by Live to ```build_midi_map``` (presumably containing a reference to the MIDI map that Live uses internally to decide how to handle MIDI messages that come in over the MIDI input port specified for this particular MIDI Remote Script).
- ```parameter``` (e.g. obtained as a member of ```device.parameters```) is a reference to the Live python object connected to the particular Live parameter to be controlled. (Note: complex Live interface objects like ```device.parameters``` are immutable.)
- ```midi_channel``` is the MIDI channel on which to listen to CC parameters. Note that internally MIDI channels are numbered from 0-15, so the MIDI channel to pass is *one less* than the MIDI channel typically used in documentation (where it ranges from 1-16).
- ```cc_no``` is the particular CC parameter number to listen to. 
- ```map_mode``` defines how to interpret incoming CC values. Possible ```map_mode``` values are defined in ```Live.MidiMap.MapMode```; we use it only to define whether CC values will be 7 bit (one byte) or 14 bit (two bytes, sent using separate CC messages, see below).
- ```avoid_takeover```: not clear how/if this parameter is honoured.

Once mapped, there is nothing much left to do: incoming MIDI CC messages that match the map are immediately processed by Live and result in the desired parameter update. The remote script does not get to see these MIDI messages. Even better: any change to a mapped Live parameter (either through the Live UI or through another remote controller) is automatically sent out as the mapped MIDI CC parameter straight to the (E1) controller. Again, the remote script does not get to see these MIDI remote messages. There is *one* thing the remote script must do itself unfortunately (but only *once* per mapped parameter): when mapping a parameter to control this way, the current value of the parameter must be sent to the E1 (as a MIDI CC message) to bring the controller on the E1 in sync with the current value of the Live parameter. After that, the remote script is literally out of the loop


### 7bit vs 14bit MIDI CC mapping

MIDI distinguishes two different types of CC parameters: 7bit and 14bit, to send 128 or 16384 different values. 14bit CC parameters actually use *two* CC parameter numbers. The originally assigned one *c* (used to transmit the most significant 7 bits of the value) and *c* + 32 (used to transmit the least significant 7 bits of the value). 

Only the first 32 CC parameters can be assigned to be 14bit controllers (even though there would be space for more starting at slot 64, but unfortunately neither Ableton nor the E1 fully support that).

### MIDI forwarding

Strangely enough, certain *non-device* parameters (like buttons appearing on tracks) can not be mapped to respond to incoming MIDI CC messages directly (luckily the volume faders, pan and send pots on tracks *can* be mapped as described above). For these parameters a different kind of mapping needs to be set up using

```
Live.MidiMap.forward_midi_cc(script_handle, midi_map_handle,midi_channel,cc_no)
```

The parameters to this call are like the one above, except:

- ```script_handle``` is the handle to this remote script (needed to call it's ```receive_midi``` method, see below). It is obtained using ```c_instance.handle()```  where ```c_instance``` is the parameter that Live passes to the call ```create_instance``` in ```__init__.py``` (as described [above](#the-c_instance-object)).

Once mapped, incoming MIDI CC messages that match the map are forwarded to the remote script that registered this mapping by calling its ```receive_midi``` method. The parameter to this call is a python *sequence* (not a list) of all bytes in the message, including the MIDI status byte etc. It is the responsibility of the remote script to process these messages and ensure something happens.

Note: only MIDI events that are forwarded as described above will be actually forwarded by Live to the ```receive_midi``` function when they occur. Other events are simply dropped. The only exception are MIDI SysEx messages that are always passed on to ```receive_midi``` for further processing by the remote script.


### Listeners

For such *non-device* parameters the remote script *also* needs to monitor any changes to the parameter in Live, and forward them to the E1 controller (to keep the two in sync). Unlike real device parameters, the mapping through ```Live.MidiMap.forward_midi_cc``` unfortunately does not instruct Live to automatically create the required MIDI CC message. Therefore the remote script needs to set this up differently (a bit like it already needs to do that for *all* mapped parameters *once* at the moment they are mapped).

For each of these *non-device* parameters (of which Live thinks you might be interested to monitor a value change) Live offers a function to add (and remove) *listeners* for this purpose. For example

```
track.add_mute_listener(on_mute_changed)
```

registers the function ```on_mute_changed``` (this is a reference, not a call!) 
to be called whenever the 'mute' button on track ```track``` changes. This function must then query the status of parameter (the mute button in this case) and send the appropriate MIDI CC message to the E1 controller to change the displayed value of the control there. 

> Note: in order for the ```on_mute_method``` to know *which* mute button (i.e. on which track) it needs to listen to, some Python trickery is required. In the E1 remote script, each track is managed by a separate object that keeps track of the Ableton Live track by setting ```self._track``` and that also defines the method ```self._on_mute_changed```. Because methods in Python have access to the object state of the object that defines them, we can define

    def _on_mute_changed(self):
        if self._track.mute:
            value = 0
        else:
            value = 127
        self.send_midi_cc7(self.midichannel, self.cc, value) 

> Passing this particular method when adding the listener (through ```track.add_mute_listener(self._on_mute_changed)```) then does the trick.


Unlike MIDI mappings (that appear to be destroyed whenever a new MIDI map is being requested through ```c_instance.request_rebuild_midi_map()```), these listeners are permanent. Therefore they only need to be added *once* when the controlling object is assigned. And they need to be explicitly removed as soon as they are no longer needed. In the example above, this is achieved by calling

```
track.remove_mute_listener(on_mute_changed)
```

### Parameter listeners

Any normal parameter (i.e. a member of the list ```device.paramters``` or the ```track.mixer_device.volume```, ```track.mixer_device.panning```, and similar) 
can also be assigned a value listener by calling ```parameter.add_value_listener(value_listener)```. This registers the function ```value_listener``` (this is a reference, not a call!) to be called whenever the value of the parameter changes. See the discussion above on the mute button listener to learn how to pass the value listener some state that tells it which parameter to listen to.

To remove an *existing* (test this first!) value listener for a parameter, call
```parameter.remove_value_listener(value_listener)```


### Initiating MIDI mapping

It is the responsibility of the remote script to ask Live to start the process of building a MIDI map for the remote script. This makes sense because only the remote script can tell whether things changed in such a way that a remap is necessary. The remote script can do so by calling  ```c_instance.request_rebuild_midi_map()```. Live will remove *all* existing MIDI mappings (for this particular remote script only). Live will then ask the remote script to build a new map by calling  ```build_midi_map(midi_map_handle)``` (which should be a method defined by the remote script object). Because the MIDI map is completely emptied, *all* MIDI mappings must be added again.


Live automatically calls ```build_midi_map``` when 
- a device is added or deleted, 
- when a (return) track is added or deleted,
- when a new song is opened, or
- when Live starts up.

At start-up or when loading a song build_midi_map is called several times.

## Device appointment

In Live, device *appointment* is the process of mapping the currently selected device to a remote controller. But it is a bit of a mess, to be honest. Here is why.

The currently loaded song maintains the currently appointed device (accessible as ```self.song().appointed_device```). If assigned a device, this device displays the `Blue Hand' to indicate it is controlled by a remote controller.
A remote control script can register a listener for changes to this variable (a [property](https://docs.python.org/3/library/functions.html#property), really) by calling

```
self.song().add_appointed_device_listener(<listener-function>)
```

to update the remote controller whenever the appointed device changes. So far so good.

The problem is that ```self.song().appointed_device``` is shared by all remote controllers and their scripts, but that Live does not itself handle the appointment of the currently selected device. The remote script needs to do it. In our case ```DeviceAppointer.py``` deals with this. But this potentially interferes with device appointment routines written by other remote scripts.

This means, for example, that setting ```APPOINT_ON_TRACK_CHANGE``` to ```False``` may have no effect if the other remote script decides to appoint anyway.


Device appointments should be ignored when the remote controller is locked to a device (this is not something Live handles for you; your appointed device handler needs to take care of this).

If your remote script supports device locking, ```can_lock_to_device``` should return ```True```. When a user locks the remote controller to a device, Live calls ```lock_to_device``` (with a reference to the device) and when the user later unlocks it Live calls ```unlock_from_device``` (again with a reference to the device).

*Note: hot-swapping a device preset in Ableton apparently sets the appointed device, even if that device was already appointed, and thus hot swapping presets always triggers the appointed device listener. It also triggers the MIDI map to be rebuilt and the state to be refreshed. The latter is a happy coincidence because it automatically ensures the state of the preset on the E1 is updated.*

## Value mapping

The Live API also offers additional functionality for retrieving the value of a parameter. Every parameter ```p``` has properties ```p.min```, ```p.value``` and ```p.max``` to obtain the minimum, current, and maximum value. These functions *always* return floating point values. 

To obtain a meaningful representation of such a value, as also displayed by Live in its own UI, every parameter ```p``` also defines a method ```p.str_of_value(v)``` that for a floating point value ```v``` for that parameter returns a string representation of that value (including its type, e.g. ```dB```, ```Hz```, ```kHz```, ```%```, ```st``` (for semitones), appended at the end of the sting).

Live distinguishes the following types of floating point values:

- Volume (```dB```)
- Frequency (```Hz``` or ```kHz```, the ```kHz``` is real-valued). In the Analog instrument filter frequencies are denoted ```k``` immediately following the value, e.g. ```22.0k```.
- ```%```. Different ranges are possible. When ranging from -x to x, the default is 0.
- Time (```ms``` or ```s```).
- Phase (```°```, written immediately after the value, e.g. ```360°```).
- Untyped (e.g. the ones used by Amp)

Live distinguishes the following types of integer values:

- Semitones (```st```). Range: -24, 24. Default: 0.
- Detune (```ct```). Range: -50 .. 50. Default 0.
- Morph (```lp/bp```), seen in certain filters.
- Pan: Ranging from ```50L``` through ```C``` to ```50R``` (note how the R and L immediately follow the value); the values appear to be integers at all times. Default: 0 (C).

Others:

- Compression ratios: ```1 : 0.25``` .. ```1 : Inf```
- Analog Sync Rate: ```4d```..```1/32t```.
- Wavetable Sync rate: ```8```..```1/64```.
- Analog Noise Balance: ```F2```..```50/50```..```F1```.

## Tracks

```self.song().visible_tracks``` returns the list (actually a ```Base.Vector``` ) of currently visible audio and midi tracks. This does include any tracks that are part of a expanded group track, but *does not include* any visible 'subtracks' created for chains in an instrument or drum rack. Therefore there is no straightforward way to list or get access to such subtracks. For this ```track_is_showing_chains``` needs to be checked and the shown chains for the first rack device on the track need to be found. 

Similarly ```self.song().view.selected_track``` *always* returns the main  track (or *group* subtrack), not the actually selected chain.


## Bugs/anomalies in Live

While developing the remote script it became clear there are certain bugs and anomalies in the interface between Live and the remote script.

First of all, some devices or instruments have internal names that are completely different from their name in the Live UI. For example SpectralResonator is called Transmute, Wavetable is called InstrumentVector, and Electric is called LounceLizzard.

For certain devices, Live does not allow mapping of parameters to the remote script even though they *are* MIDI mappable manually. The problem is that ```device.parameters``` does not contain these parameters. For example (in Live 11.2):

- Saturator: DC not mapped
- Wavetable/InstrumentVector: missing some global parameters
- SpectralResonator: resonator type is not a parameter; many MIDI input controls not mapped as parameter.
- Impulse: Soft, Sat, Filter, M, and S buttons cannot be mapped

For certain devices, Live reports the same name for different parameters in the list ```device.parameters``` (again in Live 11.2):

- Saturator patch on the fly: Dry/Wet output twice
- Compressor patch on the fly: S/C Gain twice
- Collision: 2x Panorama controlling Pan L and Pan R together
- Emit: several parameters with the same name, eg Attack!
- LFO Modulator: two parameters "Rate": one for Hz one for synced!

For certain devices, Live exposes parameters that are not visible in the Live UI, for example: 

- Hybrid Reverb: exposes parameters not in the Live UI (Eg Pr Sixth)

# The main E1 remote script

With the basics out of the way, we are now ready to explain how the Electra One (or E1 for short) remote script works.

The main remote script is ```ElectraOne.py``` implementing the interface Live expects, and dividing the work over  ```MixerController``` and ```EffectController``` by creating instances of both classes. There is also a ```ElectraOneBase``` base class that uses the ```c_instance``` passed to it to offer helper functions for the other classes (like sending midi, or writing to the log file).

Almost all methods in the ```ElectraOne``` interface test whether the remote script is ready to respond to external requests from Live, using the ```id_ready()``` function defined in ```ELectraOneBase```. There are two cases when it is not.

1. When the remote script is busy detecting whether an Electra One is indeed properly connected to it.
2. When the remote script is busy uploading a preset to the Electra One.

In both cases the remote script has sent a MIDI command to the Electra One and it is waiting for the appropriate response. To implement this waiting period in such a way that the MIDI response sent by the Electra One controller can be forwarded to Live to the remote script through ```receive_midi``` (the only interface method *not* testing readiness of the interface), 
two *threads* are used. Their working is described later on.

## Remote script package structure


The remote script package defines the following classes, shown hierarchically based on inheritance / import order.

- ```ElectraOne```: Main remote control script class for the Electra One.
  - ```MixerController```: Electra One track, transport, returns and mixer control. Also initialises and manages the E1 mixer preset.
	- ```TransportController```: Manage the transport (play/stop, record, rewind, forward).
	- ```MasterController```: Manage the master track.
	  - ```GenericTrackController```: Generic class to manage a track. To be subclassed to handle normal tracks, return tracks and the master track.
	- ```ReturnController```: Manage a return track. One instance for each return track present. (At most six).
      - ```GenericTrackController``` (see above).
	- ```TrackController```: Manage an audio or midi track. At most five instances, one for each track present.
      - ```GenericTrackController``` (see above).
  - ```EffectController```: Control the currently selected device. Handle device
    selection and coordinate preset construction and uploading. 
	- ```ElectraOneDumper```: Construct an Electra One preset and a corresponding mapping of parameters to MIDI CC for a device.
	- ```GenericDeviceController```: Control devices (both selected ones and the ChannelEq devices in the mixer): build MIDI maps, add value listeners, refresh state.

Only one instance of the ```TransportController```, ```MixerController``` and
```EffectController``` are created. For each track an instance of the ```GenericTrackController``` is created. For each assigned device a new instance of the ```GenericDeviceController``` is created. These instances are responsible for refreshing the state, listening to relevant parameter changes, mapping the MIDI, processing relevant incoming MIDI messages, for the controller on the E1 it is created for.

It also defines the following other, generic, classes:

- ```ElectraOneBase```: Common base class for most of the other classes with common functions: debugging, sending MIDI. (interfacing with Live through ```c_instance```). 
- ```DeviceAppointer```: Class that handles device appointment.
- ```Log```: Defines logging and debug functions.
- ```PresetInfo```: Stores the E1 JSON preset and the associated CC-map for a device.
- ```CCInfo```: Channel and parameter number of a CC mapping, and whether the associated controller on the E1 is 14bit or 7bit. Also records the control index of the associated control in the E1 preset (if necessary for sending the exact Ableton string representation of its value).

And it defines the following core modules:

- ```__init.py__ ```: package constructor.
- ```config.py```: defines configuration constants. 
- ```Devices.py```: stores curated device presets.
- ```versioninfo.py```: stores the date this version was committed

Finally, the file ```default.lua``` contains the default LUA scripting all effect presets need to include in order to properly format certain control values, and to pause/resume display redraws.

## Debugging

The remote script outputs various debug messages, with different 'importance' levels:

0. initialisations
1. main E1 events (except ones that happen frequently)
2. main subclass events
3. external events
4. sending values; handling acks queue
5. actual midi messages
6. display updates; detailed MIDI messages
7. device naming

Setting ```DEBUG=x``` will show all log messages whose level is lower or equal to x.

## The mixer (```MixerController```)

The mixer preset (in ```Mixer.eporj```) controls 

- the transport (play/stop, record, rewind and forward), 
- the master track (pan, volume, cue volume, solo), 
- at most six return tracks (pan, volume, mute), and 
- five tracks (pan, volume, mute, solo, arm, and at most six sends). 

The tracks controlled can be switched. Also, each track (audio, MIDI but also the master) can contain a Live Channel EQ device. If present it is automatically mapped to controls on the default E1 mixer preset as well.

The remote scripts comes with a default E1 mixer preset that matches the MIDI map defined below. But the layout, value formatting, colours etc. can all be changed, see [below](https://github.com/xot/ElectraOne/blob/main/DOCUMENTATION.md#alternative-mixer-design).

### Value formatting

For certain controls, the default mixer preset contains some additional formatting instructions (using the E1 LUA based formatting functions). 

For the mixer preset, we refrain from using the method used by almost all other remotes scripts to correctly display the values as shown by Live also on the remote control surface (using the ```p.str_of_value(v)``` approach, see [above](https://github.com/xot/ElectraOne/blob/main/DOCUMENTATION.md#value-mapping)). In most cases this is unnecessary: for enumerated controls the overlay system supported by the Electra One already makes sure the correct values are shown, and for simple controls a properly chosen 'formatter' LUA function can be used to display the correct value representation on the E1. 

In the mixer preset, the values to display are interpolated using the tables experimentally established and documented below.

**Pan**: mapped to 50L - C - 50L

**Volume**: Ranges from -infty to 6.0 dB.
  Live considers the CC value 13926 to be 0dB. The minimum CC value is 0, corresponding to -infinity. The maximum CC value equals 16383, corresponding to 6.0 db. In fact Live maps CC values to volume values using the following table (experimentally determined).
  
   
| CC (div 1024) | Value (dB) |
|---: |:-----------|
|  0  | -infty  |
| 8   | -54,925 |
| 16  | -44,646 |
| 24  | -35,941 |
| 32  | -28,798 |
| 40  | -23,202 |
| 48  | -19,175 | 
| 56  | -16,497 |
| 64  | -13,999 |
| 72  | -11,497 |
| 80  | -8,996 |
| 88  | -6,497 |
| 96  | -3,998 |
| 104 | -1,496 |
| 112 | 1,004  |
| 120 | 3,504  |
| 127 | 6,0    |

Interpolation happens as follows in the  LUA script associated with the mixer. Let ```value``` be the CC value (ranging from 0 to 16383) and let ```show``` be the floating point value to display. The last eight entries (```idx >= 8```) are linearly interpolated as follows:

```
   idx = math.floor(value / 1024)+1
   alpha = (value % 1024) / 1024.0
   show = table[idx] + alpha * (table[idx+1] - table[idx])
```

The first eight entries are interpolated exponentially as follows (with ```beta=0.1```)

```
   idx = math.floor(value / 1024)+1
   alpha = (value % 1024) / 1024.0
   show = table[idx] + (-beta * (alpha-0.5)*(alpha-0.5) + alpha + 0.25 * beta) * (table[idx+1] - table[idx])
```

   
**Send volume**: Ranges from -infty to 0.0 dB. We use the following Live CC to value table.


| CC (div 1024) | Value (dB) |
|---: |:-----------|
| 0   | -inf    |
| 8   | -60,925 |
| 16  | -50,646 |
| 24  | -41,941 |
| 32  | -34,798 | 
| 40  | -29,202 |
| 48  | -25,175 |
| 56  | -22,497 |
| 64  | -19,999 |
| 72  | -17,497 |
| 80  | -14,996 |
| 88  | -12,497 |
| 96  | -9,998 |
| 104 | -7,496 |
| 112 | -4,996 |
| 120 | -2,496 |
| 127 | 0,0   |

This table is interpolated similar to Volume.


**High/Mid/Low/Output of the Channel Eq**: The displayed value range is specified as -150..150 (or -120..120 for some); the formatter divides this by 10 and turns it into a float.

**Mid Freq of Channel Eq**: Ranges from 120 Hz to 7.5 kHz. Live CC to value table

| CC (div 1024) | Value (Hz) |
|---: |:-----------|
| 0  | 120   |
| 8  | 155   |
| 16 | 201   |
| 24 | 261   |
| 32 | 337   |
| 40 | 437   |
| 48 | 566   |
| 56 | 733   |
| 64 | 949   |
| 72 | 1230  |
| 80 | 1590  |
| 88 | 2060  |
| 96 | 2670  |
| 104 | 3450 |
| 112 | 4470 |
| 120 | 5790 |
| 127 | 7500 |

All values are interpolated polynomially (with ```beta=-0.1```).

Note that all these faders operate at their full 14bit potential.

### The Mixer MIDI map

The Mixer MIDI map is essentially defined using several constants, assigning certain MIDI channels and CC parameter ranges to MIDI controllable elements in the transport bar, the audio and MIDI tracks, the master track, and the return track.

```NO_OF_TRACKS``` defines the maximum number of tracks the mixer can manage at the same time in a single page. (Shifting tracks allows one to manage different tracks.) ```MAX_NO_OF_SENDS``` defines the maximum number of return tracks the mixer can manage. 

For audio, MIDI and return tracks the remote script assumes that the same controls for adjacent tracks in the mixer have consecutive CC parameter numbers. (For example, the PAN control on the first controlled track has CC parameter number 0, the PAN control on the second controlled track has CC parameter number 1, etc.). This allows the remote script to compute the necessary CC parameter numbers when only given the CC parameter number for the first, in the case of PAN controls defined by the constant ```PAN_CC```.

For the send controls on a track this is slightly more complicated, because tracks can have more sends, depending on the number of return tracks (limited to a maximum of ```MAX_NO_OF_SENDS```). In this case, the CC parameter for the x-th send on the y-th track equals ```SEND_CC``` + (x-1) *```NO_OF_TRACKS``` + (y-1).

Unfortunately, the number of 14 bit controls in one MIDI channel is limited to 32. As we would like the send controls to be fine grained, and therefore 14 bit, ```MAX_NO_OF_SENDS``` times ```NO_OF_TRACKS``` can never exceed 32.

#### Specific choices made in the mixers supplied with the remote script

Faders (except the Channel EQ Output faders) are 14 bit, all other controls are 7bit, which are essentially just buttons sending 0 for off and 127 for on values. Controls are mapped to CC as explained below. We assume 5 tracks, and at most 6 return tracks.


#### Master, return tracks and the transport.

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

#### Tracks

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

#### Sends

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

### Mixer control identifiers for labels and visibility

Each control and label in the Mixer has fixed id, used to change the label or the visibility (this allows different layouts of the mixer to be handled seamlessly). 

The control script is designed such that it doesn't need to be aware of the actual control identifier  assignments. Instead, the actual update of labels and visibility is implemented in LUA scripts embedded in the ```Mixer.eproj```. The E1 remote scripts expects the following LUA functions to be implemented by the mixer (see ```ElectraOnebase.py``` and of course the LUA code in ```Mixer.eproj```).

- ```aa()```: send at the start of a large number of display updates to be sent to the E1 to temporarily suspends display updates on the E1
- ```zz()```: send at the end of a large number of updates to resume disdplay updates (and execute all pending ones in one go).
- ```utl(idx,label)```: update the track label for the track with index ```idx``` (starting at 0) with the specified ```label``` string on all relevant pages (e.g. the Main, Channel EQs and Sends pages).
- ```ursl(idx,label)```: update the return track labels for track with index ```idx``` (starting at 0) with the specified ```label``` string on all relevant pages (e.g. the Returns page) and the associated control labels on the relevant pages (e.g. the Sends page).
- ```seqv(idx,flag)```: Set the visibility of the channel eq device on the specified track (if idx=```NO_OF_TRACKS```) this signals the master track.
- ```sav(idx,flag)```: Set the visibility of the arm button on the specified track.
- ```st(str)```: set the value for the tempo dial to the string ```str```.
- ```sp(str)```: set the value for the position dial to the string ```str```.
- ```smv(tc,rc)```: make ```tc``` tracks and ```rc``` return tracks visible. This mat also impact other pages (eg the Channel EQ and Sends pages).

### Internally

The code to handle the mixer is distributed over the following modules (with their associated class definitions):

1 ```MixerController.py```
: Sets up the other modules (and their classes) below. Handles the previous tracks and next tracks  selection buttons. Distributes incoming MIDI messages to the modules below (see ```receive_midi```). Coordinates the construction of the MIDI map (see```build_midi_map```). Forwards ```update_display``` to each module below. Also keeps track of which five tracks are assigned to the controller (the index of the first track in ```_first_track_index```) and updating the track controllers whenever tracks are added or deleted, or when the user presses the previous and next track buttons.

  (Currently, the mixer preset must be installed once in the right slot ```MXIER_PRESET_SLOT``` before using the remote script; future release should upload it automatically when not present.)

2 ```TransportController.py```
: Handles the play/stop, record, rewind and forward button. ```update_display()``` (called every 100ms by Live) is used to test whether the rewind or forward button is (still) pressed and move the song play position accordingly (by ```FORW_REW_JUMP_BY_AMOUNT```).

3 ```MasterController.py```
: Handles the master track volume, pan, cue volume and solo on/off parameters. Also sets up control of a Channel EQ device, when present on the master track.

4 ```ReturnController.py```
: Handles one return track, as specified by the ```idx``` (0 for return track A) when created by ```MixerController```. ```MixerController``` will create at most six instances of this controller, the actual number depending on the actual number of return tracks present. Each ```ReturnController``` manages the pan, volume and mute on the return track assigned to it. ```idx``` is used to compute the actual CC parameter number to map to a Live parameter (using the base CC parameter number defined as a constant derived from the tables above).

5 ```TrackController.py```
: Handles one audio or MIDI track, as specified by the ```idx``` (0 for the first track in the song) when created by ```MixerController```. ```MixerController``` will create five instances of this controller (passing an additonal ```offset``` value, in the range 0..4, to tell this controller which of the five tracks it is controlling and hence allowing it to compute the correct CC parameter numbers to map to the parameters in the track assigned to it. Each ```TrackController``` manages the pan, volume, mute, solo and arm button of the assigned track. Also sets up control of a Channel EQ device, when present on this track.

All these modules essentially map/manage controls and parameters using the strategy outlined above. In fact almost all code for this is in ```GenericTrackController```, of which ```TrackController```, ```MasterController``` and ```ReturnController``` are simple subclasses. The idea being that all three share a similar structure (they are all 'tracks') except that each of them has slightly different features. Which features are present is indicated through the definition of the corresponding CC parameter value in the ```__init__``` constructor of the subclass (where the value ```None``` indicates a feature is missing).

The ```GenericTrackController``` expects the subclass to define a method ```_my_cc``` that derives the actual CC parameter number to use for a particular instance of an audio/midi track (```TrackController```) or a return track (```ReturnController```). It also expects the subclass to define a method ```_init_cc_handlers``` (explained below).

### The EQ device

If the master track and the five audio and midi tracks currently managed 
contain a Live Channel EQ device, this one is automatically discovered and mapped to the corresponding controls in the E1 preset 'Channel EQs' page. (The last possible match is used.) The mapping essentially follows the exact same method as used by ```EffectController.py``` (see below) and involves little more than a call to 
```build_midi_map_for_device``` (to map the device parameters to the CC controllers) and ```update_values_for_device``` to initialise the controller values as soon as the device is mapped.

The device mapped can relatively easily be changed by changing the definitions of ```EQ_DEVICE_NAME``` and ```EQ_CC_MAP``` in ```MasterController.py``` and ```TrackController.py```. Of course, the E1 mixer preset must also be updated then.

If a track currently managed by the mixer preset does not contain an EQ device (or if it gets deleted), the associated controls are made invisible on the mixer preset. It uses the following LUA function defined in the mixer preset for that:

- ```seqv(idx,flag)```: update the EQ controls visibility for the track with index idx (starting at 0).

### Alternative mixer design

Alternative mixer designs are possible (provided they adhere to the mappings and constraints outlined above). 

*Warning: do NOT remove any controls; this may break the script/mixer preset. The reason is that controls associated with (return) tracks that are not present in Ableton are hidden using their control id; the LUA scripting embedded in the Mixer preset responsible for that assumes these controls exist. If you want to hide them, move them to a hidden page.*

If you are really adventurous you can replace the default EQ controls based on Live's Channel EQ with a different default device on the audio, MIDI and master tracks by changing the ```MASTER_EQ_DEVICE_NAME```/```TRACK_EQ_DEVICE_NAME``` and ```MASTER_EQ_CC_MAP```/```TRACK_EQ_CC_MAP``` constants in ```config.py```.
All that matters is that you do not change the control id, MIDI channel assignments (ie the E1 devices), the CC parameter numbers, the CC minimum and maximum values, and whether it is a 7bit or 14bit controller.

For example an alternative mixer design is included (```Mixer.alt.eproj```) that shows the track select and transport controls on all pages. As a result, the Channel Eq page no longer shows the 'rumble' filter switch, and only 5 sends are defined. To match this,  ```MAX_NO_OF_SENDS = 5``` and ```TRACK_EQ_CC_MAP``` and ```MASTER_EQ_CC_MAP``` have been adjusted in ```config.py```.



### E1 MIDI CC forwarding

Recall that certain Live UI elements cannot be mapped to MIDI CCs automatically. For those, incoming MIDI CC messages must be registered and, when received, be handled.

In the E1 remote script, each class that needs to set up MIDI CC message forwarding defines a (constant) dictionary ```_CC_HANDLERS``` containing for each (midi_channel,cc_no) pair the function responsible for processing that particular incoming MIDI message.

For example, ```TransportController.py``` defines

```
self._CC_HANDLERS = {
	   (MIDI_MASTER_CHANNEL, POSITION_CC) : self._handle_position
	,  (MIDI_MASTER_CHANNEL, TEMPO_CC) : self._handle_tempo
	,  (MIDI_MASTER_CHANNEL, PLAY_STOP_CC) : self._handle_play_stop
	,  (MIDI_MASTER_CHANNEL, RECORD_CC) : self._handle_record
	}
```

The ```process_midi``` function in the same class (called by the global ```receive_midi_function``` but with the midi channel, CC parameter number and value already parsed) uses this dictionary to find the correct handler for the incoming MIDI CC message automatically. And the ```build_midi_map``` method in the same class uses the same dictionary to set up MIDI forwarding using ```Live.MidiMap.forward_midi_cc```.


## Device control (```EffectController```)

The remote script also manages the currently selected device, through a second dynamic preset (alongside the static mixer preset outlined above). The idea is that whenever you change the currently selected device (indicated by the 'Blue Hand' in Live), the corresponding preset for that device is uploaded to the E1 so you can control it remotely. 

The ```EffectController.py``` module handles this, with the help of
- ```ElectraOneDumper.py``` (that creates device presets on the fly based on the information it can obtain from Live about the parameters of the device, see [further below](#generating-an-e1-preset)),
- ```Devices.py```(that contains curated, fine-tuned, presets for common devices), and
- ```GenericDeviceController.py``` that contains the code to update midi maps and refresh state (that is also used to control the Eq devices in the mixer preset).

Starting with E1 firmware version 3.4, the curated presets stored in ```Devices.py``` can actually be uploaded once to the E1 and stored on its internal file system. A SysEx call can then quickly stage such a preloaded preset in the effect slot.

Module ```EffectController.py``` uses the same method as described above for the different mixer classes to map MIDI controls to device parameters,  initialising controller values and keeping values in sync. This is relatively straightforward as all device parameters can be mapped using ```LiveMidiMap.map_midi_cc```. (Note that unfortunately certain devices omit certain controls from their parameter list.) The complexity lies in having the right preset to upload to the E1, and knowing how the CC parameters are assigned in this preset.


When the selected device changes (see [device appointment below](), ```EffectController``` does the following.

1. A patch for the newly selected device is uploaded to the Electra One to slot ```EFFECT_PRESET_SLOT``` (default the second slot of the sixth bank).
   - If a user-defined [curated preset](https://github.com/xot/ElectraOne/blob/main/DOCUMENTATION.md#curated-presets) exists, that one is used: either using the preloaded version already stored on the E1, or the one stored in ```Devices.py```. In the latter case it is uploaded to the E1.
   - If not, the parameters for the newly selected device are retrieved from Live (using ```device.parameters```) and automatically converted to a Electra One patch (see ```ElectraOneDumper.py```) in the order specified by the configuration constant ```ORDER```. 

2. All the parameters in the newly selected device are mapped to MIDI CC (using ```Live.MidiMap.map_midi_cc```). For a user-defined preset, an accompanying CC map must be defined to provide the necessary information. For presets constructed on the fly, ```ElectraOneDumper.py``` creates it. 

3. After this mapping, the values of the controller are initialised once (after a small delay to ensure the patch on the E1 is ready to receive them). With that all is set: Ableton will forward incoming MIDI CC changes to the mapped parameter, and will also *send* MIDI CC messages whenever the parameter is changed through the Ableton GUI or another control surface.

If *no* device is currently selected (e.g. initially, after deleting a device), a special empty device is uploaded. This allows the remote script to store some LUA script at the effect preset slot, which serves two purposes

- ensure that the patch request button keeps on working, and
- ensure that in ```CONTROL_BOTH``` mode (when a second E1 is connected to the USB Host input that controls the mixer) the necessary SysEx commands are forwarded to the second E1.

Sometimes when the appointed device changes, it may not be possible to upload it immediately because:

- the mixer preset is visible and we are in ```CONTROL_EITHER``` mode, or
- the E1 is not yet ready for it (e.g. when a previous upload hasn't completed yet), or 
- it may not even be necessary to do so (e.g. because a device appointment change should not immediately trigger  an upload, see the ```SWITCH_TO_EFFECT_IMMEDIATELY``` configuration option)

In that case ```EffectController``` keeps track of this delayed upload, and will initiate the actual upload when necessary. 

### Curated presets

Curated presets are 
- either stored preloaded on the E1, by default in the folder ```xot/ableton``` within ```ctrlv2/presets```, using the ```device.class_name``` as the file name (where the preset itself is stored in ```<name>.epr``` and any associated LUA code is stored in ```<name>.lua```),
- or stored in a dictionary ```DEVICES``` defined in ```Devices.py```. The keys of this dictionary are the names of devices as returned by ```device.class_name```. This is not perfect as MaxForLive devices return a generic Max device name and not the actual name of the device. The same is true for plugins. See [below](#getting-the-name-of-a-plugin-or-max-device) for how the script somewhat solves this.

Using a device name as its key, the dictionary stores information about a preset as a ```PresetInfo``` object (defined in ```PresetInfo.py```). This is essentially a tuple containing the E1 preset JSON as a string, a CC map, and some LUA scripting special to the preset. Certain presets use this to hide/show certain parts of the preset depending on the value of certain parameters (e.g. to show either a synchronised rate control or a free frequency control to control the speed of an LFO, depending on a 'sync' toggle button).

The E1 JSON preset format is described [here](https://docs.electra.one/developers/presetformat.html#preset-json-format). A control in the preset is assigned a CC parameter number, a MIDI channel, a type and whether it transmits/listens to 7bit or 14 bit CC values. (All controls are CC type.)

The CC map is yet another dictionary, indexed by parameter names (as returned by ```parameter.original_name```). For every control defined in the JSON preset, a corresponding entry (with the same MIDI information) must be present in the CC map (or else the control will not control an actual parameter in Live). The other way around, a preset may be simplified and not contain controls for all the parameters in the CC map. Note that the preset does not (need to) know the parameter name (although for presets constructed on the fly the parameter name is in fact used as the label of the control).

(*Note: should a parameter name in Live change across version updates (yes, I've seen this happen, argh) then keep the dictionary entry in the CC map for the original name, and duplicate it to add another dictionary entry for the new parameter name. This way the curated preset works for both versions of Live.*)

A parameter entry in the CC map is a ```CCInfo``` object containing:

- the E1 preset identifier for the control (-1 if updating values can be done completely by sending MIDI CC values; otherwise strings are used as described [here](https://github.com/xot/ElectraOne/blob/main/DOCUMENTATION.md#value-updates)). This can be either an integer (for normal controls) or a tuple (cid,vid) for complex controls like ADSRs on the E1, where cid indicates the control-id and the vid indicates the value index within the control (in the range 1..10) (*This complex variant is not implemented yet in the current E1 firmware 3.1*)
- the MIDI channel (in the range 1..16),
- whether the control sends 7bit (```False``` or 0) or 14 bit (```True``` or 1) values, and
- the actual CC parameter number (between 0..127, -1 if not mapped).

The constructor for ```CCInfo``` also accepts an untyped four-tuple as parameter, to allow the definition of a CC map for a curated preset to look like 

```
{'Device On': (-1,11,False,1),'State': (-1,11,False,2),'Feedback': (-1,11,True,3),...
```

The full curated definition for the Looper device in ```Devices.py``` then looks like this:

```
DEVICES = {
'Looper': PresetInfo('{"version":2,"name":"Looper v2","projectId":"Jx8aDJ9D5K2sl9iAZnTj",...',
    """""",
    {'Device On': (-1,11,False,2),'State': (-1,11,False,7),...}),
```

> Note: for user-defined patches it is possible to assign *several different device parameters* to the same MIDI CC; this is e.g. useful in devices like Echo that have one visible dial in the UI for the left (and right) delay time, but that actually corresponds to three different device parameters (depending on the Sync and Sync Mode settings); this allows one to save on controls in the Electra One patch *and* makes the UI there more intuitive (as it corresponds to what you see in Ableton itself). This approach requires the controls to not show any values (because the value ranges of each Ableton parameter is different), so in the actual Echo preset, some LUA functions are used to allow several controls on the same location, while making some of them visible or invisible.

#### Getting the name of a plugin or Max device

For native devices and instruments, ```device.class_name``` is the name of the device/instrument, and ```device.name``` equals the selected preset (or the device/instrument name). For plugins and Max devices, ```device.class_name``` is useless (denoting its type like ```AuPluginDevice``` or```MxDeviceAudioEffect```). To reliably identify curated presets by name for such devices as well, the remote script checks whether a plugin or Max device is embedded inside an audio or instrument rack, and if so it uses the name of the enclosing rack followed by a single hyphen ```-``` as the name to use for the plugin or Max device when dumping its preset or when looking up a preloaded preset. So if a plugin is in a rack with name ```MiniV3``` then ```MiniV3-``` is used as the plugin name. (If a plugin is not enclosed in a rack, then its own preset name is used as the device name, which is unreliable.)

*Note that selecting the rack itself will upload the set of macros as the preset.*

So, if you want to make your own curated presets for plugins or Max devices, embed them inside an audio or instrument rack and rename that rack to the name of the plugin. Save the rack preset, and in future load that rack preset instead of loading the plugin or Max device directly. Selecting the plugin or Max device (*not* the enclosing rack!) will then show the preset you created for it. (Be sure to add the hyphen to the name when creating such presets!)



#### Getting the name for a rack device

For rack devices (audio, MIDI, drum or instruments), the remote script also uses the (unreliable) method of using ```device.name``` to determine the name to use to lookup a predefined preset.

### Generating presets on the fly

To generate a preset on the fly, an instance of ```ElectraOneDumper``` is created passing it the device name and its list of parameters. The resulting object is queried for the generated preset through ```get_preset()```.

Internally creating an instance (and hence the preset) proceeds through the following three steps:

1. [Sort (and filter) the list of parameters](#sorting-and-filter-parameters),
2. [Construct a CC map for the resulting list of parameters](#constructing-a-cc-map), and
3. [Generate a JSON encoded E1 preset as a string](#generating-an-e1-preset).

#### Sorting and filter parameters

First, the list of all parameters of the device is filtered using ```PARAMETERS_TO_IGNORE```. Any parameter in ```PARAMETERS_TO_IGNORE["All"]``` or in ```PARAMETERS_TO_IGNORE[<device-name>]``` are omitted.

Sorting and filtering the resulting parameter list is controlled through the configuration constant ```ORDER```. The parameters can be 

1. left in the order as reported by Live (```ORDER_ORIGINAL```), 
2. sorted alphabetically (```ORDER_SORTED```),  or 
3. sorted according to the order specified in the Live remote script framework that is also used by all other officially supported remote scripts (```ORDER_DEVICEDICT```). 

The third option uses ```PERSONAL_DEVICE_DICT``` or, if no list for the device can be found there,  ```DEVICE_DICT``` defined in ```_Generic.Devices```. This 'system wide' preferred order actually only contains the most important parameters, and thus reduces the complexity of the generated patch.

#### Constructing a CC map

Each parameter in the list is assigned a MIDI channel and CC parameter number. Depending on the type of parameter, it is assigned either a 7bit or 14bit controller. Essentially this means that most faders (i.e. non-quantised and non-integer valued parameters, see ```wants_cc14()``` and also the [discussion below](#generating-an-e1-preset)) are considered 14bit. 

This is relevant also for constructing the CC map as 14bit CC parameters actually use *two* CC parameter numbers. The originally assigned one *c* (used to transmit the most significant 7 bits of the value) and *c* + 32 (used to transmit the least significant 7 bits of the value). This means that when assigning *c*, *c* + 32 must be marked as taken too. The code in ```construct_ccmap``` therefore first maps all 14 bit CC parameters (limited by
```MAX_CC14_PARAMETERS``` and then all 7 bit CC parameters (limited
 by ```MAX_CC14_PARAMETERS```). This allows the 7 bit CC parameters to fill any holes left by the 14 bit CC assignments.
 
Note: Only the first 32 CC parameters (i.e numbered 0..31) can be used to map 14 bit CC controllers (using up the range 32..63 as 'shadow' CC parameter numbers in the process). The range 64..127 can only be used for 7 bit CC parameters. I turns out that you can actually map say CC 64 to a 14 bit controller on the E1, correctly sending 14 bit values (over CC 64 and CC 96) to Live. Live in fact also correctly processes such incoming 14 bit values for a parameter mapped to CC 64. Unfortunately Live does not *send* any value when this parameter changers. And the E1 does not process any incoming 14 bit CC values (even when sent explicitly by the remote script) for CC parameter numbers in the 64..96 range.

The first MIDI channel assigned for a preset is ```MIDI_EFFECT_CHANNEL```. When no more valid or free CC parameters are available, the next MIDI channel is claimed (up to a maximum of ```MAX_MIDI_EFFECT_CHANNELS```). Large devices like Analog require 4 MIDI channels to allow all of its many (14 bit) faders to be mapped.

#### Generating an E1 preset

Using the information in the just created CC map, ```construct_json_preset``` proceeds to generate the E1 preset. Given the number of parameters it counts the required number of pages. For each assigned MIDI channel in the CC map it creates a corresponding E1 MIDI device. 

For the label of a control, ```parameter.name``` is  used (whereas ```paramater.original_name``` is used for the CC map and thus is guaranteed not to change over time, ensuring the mappings remain consistent.

For plain on/off parameters it creates a 'pad' control in the patch. For all other quantized parameters  (```p.is_quantized```, except plain on/off buttons) it creates an overlay containing all possible values for the parameter as reported by Live through ```parameter.value_items```. This overlay is subsequently used by the corresponding 'list' control in the controls section of the patch. As a result, a parameter like 'Shape' can list as its values 'Sine', 'Saw' and 'Noise' on the E1. For pan faders, an overlay with index 1 is created to create center value ```C```. 

For faders some 'intelligence' is necessary to decide on how to define the range of display values to use in the preset. These are different than the underlying CC value range, which is always set to 0..127 for 7 bit and 0..16383 for 14 bit controls. This intelligence is necessary because the E1 only allows the definition of integer display value ranges, and when defined, *only sends out a MIDI CC message when the display value changes*. This is exactly as desired for parameters like 'Octave' (typically ranging from -3 to 3) or 'Semitones' (ranging typically from -12 to 12). But this is undesirable for e.g. output mix parameters that range from 0 to 100 % (or filter attenuation that ranges from -12 dB to 12 dB) but for which fine grained full 14 bit control is required. The 'intelligence' is implemented by ```is_int_parameter``` that looks at the minimum and maximum parameter values reported by Live, and 

- when their value contains a '.', or 
- they end with a type designator 'dB', '%', 'Hz', 's', or 'ms', 

then the parameter is considered not an integer, and is assigned a 14 bit CC (already when creating the CC map, of course) and no display value range is defined. Depending on the type, a suitable formatter function is assigned (these are defined in ```default.lua```). For actual integer parameters, the minimum and maximum values reported by Live are used as the display value range.

Note that the ```ElectraOneDumer``` actually is a subclass of ```io.StringIO``` to make the incremental construction of the preset string efficient. In Python strings are constants, so appending a string essentially means copying the old string to the new string and then appending the new part (some Python interpreters may catch this and optimise for this case, but we cannot rely on that). We use the ```write``` method of ```io.StringIO``` to define an ```append``` method that takes varying number of elements as parameter and writes (i.e. appends) their string representation to the output string. 

### Default LUA script

Presets use some general functions defined in ```default.lua```. From firmware 3.4 onwards, this code is assumed to be preloaded on the E1, and included in the LUA for a particular preset using the line ```require("xot/default")```.

It defines some formatting functions to format parameters with decibel values, frequency values, pan controllers, etc, that are used in both the curated presets and the presets generated on the fly. And it defines the functions ```aaa()``` and ```zzz()``` to pause and resume display updates.

It also defines the function ```patch.onRequest``` that is called whenever the patch request button (top right) is pressed. It sends a special MIDI SysEx command ```(0xF0 0x00 0x21 0x45 0x7E 0x7E 0xF7)``` back to the remote script that then toggles between mixer and effect control. As complex presets may have more than one device defined (and patch.onRequest sends a message out for every device), we use device.id to diversify the outgoing message. (Effect presets always have device.id = 1 as the first device)

And it defines variants for the mixer display control functions (```aa()```, ```zz()```, ```utl()```, ```ursl()```, ```seqv()``` and ```smv()```) to forward them when ```CONTROL_MODE = CONTROL_BOTH```.

### Value updates 

Values are updated by a call to ```refresh_state```. This checks which of the presets is actually visible on the Electra One. This is possible because the Electra One sends out a SysEx whenever a preset is selected on the device (see 
```_do_preset_changed```). Both the mixer and effect controller call ```refresh_state``` after having (re)built their MIDI map. 

*Note: selecting the slot when uploading a preset apparently also triggers the preset selected sysex on the E1; we use this to trigger a value updates in certain cases because the preset selected sysex is sent after the preset has been fully activated. This way we can be sure it is actually ready to receive values.*

The actual conversion of Live parameter values to the corresponding MIDI CC values, and the sending of these MIDI CC values over the right channel and with the right CC parameter number, is handled by the ```send_parameter_...``` and ```send_midi_...``` methods in ```ElectraOneBase.py```. (This is one of the reasons why all controller classes mentioned above subclass ```ElectraOneBase```). Care is taken to properly handle 7 bit and 14 bit CC parameters (in the latter case first sending the 7 most significant bits and then the remaining 7 least significant bits in a second MIDI CC message, with CC parameter 32 higher).

For non-quantised parameters (think value faders), the MIDI value to send for the current device parameter value depends 

- on the type of control (7 bit or 14  bit) and hence their MIDI value range (0..127 vs 0..16383), and 
- the minimum and maximum value of this parameter, and the position of the current value within that range, i.e. (val - min) / (max - min).

The computation of the 7bit MIDI value to send for a quantised parameter works as follows. Quantized parameters have a fixed list of values. For such a list with *n* items, item *i* (starting counting at 0) has MIDI CC control value
*round*(*i* * 127/(*n*-1)).

When sending a bunch of MIDI message to update the values of a complete mixer or effect preset (as the ```refresh_state``` does, the script first disables display updates on the E1, and reactivates display updates after all values are sent: this makes the E1 respond faster. See the ```_midi_burst_on()``` and ```_midi_burst_off()``` methods in ```ElectraOneBase```. These functions rely on the following two LUA functions to be implemented on the mixer preset (the same holds for the effect preset as well):

- ```aa()```: delay updating the display of the preset.
- ```zz()```: resume updating the display of the preset, and force a redraw now. 

For complex Abelton parameters whose display function is hard to derive from the underlying MIDI value (e.g. exponential or logarithmic volume or frequency domains), the remote script uses the ```str_for_value()``` function that Ableton defines for each device parameter. (In fact, for a parameter ```p``` the standard ```str(p)``` call is equivalent to ```p.str_for_value(p.value)```.)
The resulting string is sent to the E1 by calling the LUA function ```svu``` defined in every effect preset. (See ```ElectraOneBase.py``` and ```DEFAULT_LUASCRIPT``` defined in ```EffectController.py```. The preset must use ```defaultFormatter``` as the formatter function for such controls (to ensure that the E1 itself does not change the value). 

For device presets, the CC map tells the remote script which parameters need to be treated this way, see [here](https://github.com/xot/ElectraOne/blob/main/README-ADDING-PRESETS.md#device-preset-dumps).

For smoother operation, values for such complex Ableton parameters are not immediately updated whenever their underlying MIDI value changes. Instead the ```update_display()``` function is used to update *all changed* values of such parameters, every ```EFFECT_REFRESH_PERIOD``` times.


### Device appointment

(TBD)


## Threading

The remote script relies on threading to be able to asynchronously wait for confirmation that a certain command has properly been executed on the E1. 

If ```DETECT_E1=True```, one thread (```_connect_E1```) sends out a request for a response from the Electra One controller repeatedly until an appropriate request response is received. It never stops doing so, so when no Electra One gets connected, the remote script never really starts.

The other thread (```_upload_preset_thread```) first tries to load a preloaded preset, and if that is not possible it sends a select preset slot MIDI command to the Electra One controller, and waits for the ACK before uploading the actual preset (again waiting for an ACK as confirmation that the preset was successfully received). See [the section on uploading for more detais](#uploading_a_preset)

In both cases a timeout is set (for the preset upload this timeout increases with the length of the preset) in case an ACK is missed and the remote script would stop working  forever. (In such cases, a user can always try again by reselecting a device.)

### Dealing with ACKs and NACKs

For allmost all SysEx commands, the E1 returns whether they were successfully executed or not by sending back an [ACK](https://docs.electra.one/developers/midiimplementation.html#ack) or [NACK](https://docs.electra.one/developers/midiimplementation.html#nack). 

The way Ableton implements control scripts makes it hard to wait for them in a normal fashion. An incoming ACK or NACK will be passed by Ableton Live to the ```receive_midi()``` function, which is the only way for the remote script to learn about receipt of an ACK/NACK. But ```receive_midi()``` can only be called if the remote script is not active, which is *not* the case if the remote script is busy waiting for an ACK/NACK after sending a SysEx message!

The ElectraOne remotescript solves this as follows.

After sending a SysEx message for which an ACK/NACK is expected, the script calls ```_increment_acks_pending()``` which increments ```ElectraOneBase.acks_pending``` by 1 and records the current time. This creates a virtual ACk/NACK queue (representing the actual ACKs/NACKs sent by the E1 that still need to be consumed by the remote script).

The threads use this mechanism as follows. First they consume all pending ACKs/NACks by calling ```_clear_acks_queue()```. This is a loop that waits for some timeout and sleeps inbetween (to release the thread and to allows Live to call ```receive_midi()``` to process and register incoming ACKs and NACKs, decrementing ```ElectraOneBase.acks_pending```. Then the threads start their actual commands, and wait for confirmation by calling ```_wait_for_ack_or_timeout()```.


### Uploading a preset

The 'standard' way of uploading a preset is to send it as a SysEx message through the ```send_midi``` method offered by Ableton Live. However, this is *extremely* slow on MacOS (apparently because Ableton interrupts sending long MIDI messages for its other real-time tasks). Therefore, the remote script offers a fast upload option that bypasses Live and uploads the preset directly using an external command. It uses [SendMIDI](https://github.com/gbevin/SendMIDI), which must be installed. To enable it, ensure that ```SENDMIDI_CMD``` points to the SendMIDI program, and set ```E1_CTRL_PORT``` to the right port (```Electra Controller Electra CTRL```).


## Switching views

The PATCH REQUEST button on the E1 (right top button) is programmed to send the SysEx command ```0xF0 0x00 0x21 0x45 0x7E 0x7E 0xF7```. On receipt of this message, the main E1 remote script switches the visible preset form mixer to effect or vice versa (but only of ```CONTROL_MODE = CONTROL_EITHER```). It uses the global class variable   ```ElectraOneBase.current_visible_slot``` to keep track of this (already needed to prevent value updates for invisible presets. To implement this, the mixer and effect presets redefine the ```patch.onRequest(device)``` function (see ```default.lua``` and the mixer lua script).




<!--
## TODO

- lessons learned, e.g. not overflooding the E1
-->
