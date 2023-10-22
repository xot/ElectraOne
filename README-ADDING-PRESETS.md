# Adding or changing presets, and other advanced configuration

The remote script can be adapted in interesting ways: the mixer preset can be customised to your taste, device presets can be customised or added as well, and some other advanced configurations is possible. These are discussed below.

## Changing the mixer preset

There is nothing specific about the design of the mixer apart from the MIDI channel, ELectra One port and CC number assignments of individual controls. This means you can freely redesign the mixer to your own needs, e.g one where tracks are laid out horizontally instead of vertically (such that all track controls are active at the same time). But please make sure that *all* controls retain both their original CC numbers *and* their original control id!

*Warning: do NOT remove any controls; this may break the script/mixer preset. The reason is that controls associated with (return) tracks that are not present in Ableton are hidden using their control id; the LUA scripting embedded in the Mixer preset responsible for that assumes these controls exist.*

As an example, an alternative mixer design is included in the distribution that shows the transport controls on all pages, at the cost of removing one return track and removing the rumble/high-pass toggle from the channel eq page. See ```Mixer.alt.eproj```. To use it, copy ```config.mixer.alt.py``` to ```config.py```.

## Using a second E1 to control the mixer

If you happen to own *two* E1s, then you can use the second one to control the mixer exclusively, while the first controls the currently selected device. 

(**Note: this currently does not work due to firmware changes; a fix is in the works.**)

Use a USB cable to connect the second E1 to the USB Host port on the first E1. Make sure that in the USB Host configuration on the first E1, Port 1 is selected for the second connected E1. See [these instructions](https://docs.electra.one/userinterface.html#menu). Finally, in
```config.py``` set ```CONTROL_MODE = CONTROL_BOTH```.

Before starting Ableton, ensure that the effect preset slot (bank 6 slot 2) is selected on the first E1, and the mixer preset is uploaded and selected (bank 6, slot 1) in the second E1. 

(*Both controllers apparently need to run firmware 3.1.5. or larger for this to work.*)

## Adding preloaded device presets

You can modify existing presets, or add new ones for other, non-standard, devices or plugins. Sources for the existing presets can be found in this repository of course, or in the E1 web editor: simple select 'Ableton' as brand in the Preset Library browser.
 
When changing existing preloaded presets, you only need to upload the new versions of both `device.epr` (created with `Download Preset` in the web editor) and the `device.lua` (cut and paste from the web editor) to the E1 
at `ctrlv2/presets/xot/ableton`. Make sure to include the following line

```
require("xot/default")
```

at the start of the `device.lua` file. This includes some common LUA functions used by the remote script and the preset.

When uploading a preset for a new, non-standard, device, don't forget to also include the `device.ccmap` (as described next).


### Device preset dumps

Constructed presets can be dumped, along with associated CC mapping information. This can be used for fine tuning the preset as it will be shown on the E1 (e.g. parameter layout, assignment over pages, colours, groups). The updated information can be added to ```Devices.py``` to turn it into a [preloaded preset](#preloaded-presets).

Such a dump constructs a file ```<devicename>.epr``` with the JSON preset (which can be uploaded to the [Electra Editor](Https://app.electra.one)), and a file ```<devicename>.ccmap``` listing for each named parameter the following tuple:

- the identifier of the control on the E1, in case Ableton Live [needs to send the string representation of the value](https://github.com/xot/ElectraOne/blob/main/DOCUMENTATION.md#value-updates) of the parameter to the E1 for display, because the E1 cannot reliably determine it. This is a tuple (*cid*,*vid*) where *cid* is the control identifier, and *vid* is the value index within a complex control like an ADSR envelope. If *cid* equals -1 (i.e. the tuple equals (-1,0)), then no string value updates need to be sent to the E1.
- the MIDI channel,
- whether it is a 14bit controler (1/True: yes, 0/False: no), and
- the CC parameter number (between 0 and 127) that controls it in the preset. ```None``` means the parameter is not/could not be mapped. 

For example, dumping the Echo device could create the following CC map entry:

```
'L Time': ((25,0),11,True,14)
```

Meaning that the Echo device parameter ```L Time``` has a control with identifier 25, and is mapped on Midi channel 11 as a 14-bit control on CC parameter number 14. (*Note: the actual CC map for Echo lists `'L Time': (25,11,True,14)` as its entry; this uses an older shorthand for the control identifier.*)

Note that the actual CC parameter used for a 14bit control is cc_no *and* cc_no+32 (because by convention a 14bit CC value is sent using the base CC and its 'shadow' parameter 32 higher. (This means the constructed map may appear to have holes in the 32-63 range.)

The construction of presets is controlled by several constants defined in ```config.py```. Dumps are written in the folder ```<LIBDIR>/dumps```.
See the [documentation of configuration options](#configuring) below.)

### Names used for plugins and Max devices

There is unfortunately no reliable way for the remote script to get the *device* name for a plugin or a Max device: when asking Live it returns the name of the currently loaded 'Live preset' for the plugin or Max device. This is annoying when dumping E1 presets, or defining preloaded presets (see below).

The remote script uses the following hack to still allow a fixed device name to be found. Enclose such a plugin or Max device in an instrument, midi, or audio rack and rename that enclosing rack to the name of the device. The remote script uses the name of the enclosing rack followed by a single hyphen ```-``` as the name to use for the plugin or Max device when dumping its preset or when looking up a preloaded preset. So if a plugin is in a rack with name ```MiniV3``` then ```MiniV3-``` is used as the plugin name. (If a plugin is not enclosed in a rack, then its own preset name is used as the device name.)

### Preloaded presets

Preloaded presets are stored in ```Devices.py```. The Python script ```makedevices``` creates this file based on all presets stored in ```./preloaded```, using the following files

- ```<devicename>.epr```, the preset in JSON format, as [documented here](https://docs.electra.one/developers/presetformat.html#preset-json-format); it is minified by the script, 
- ```<devicename>.lua```, containing additional LUA functions used within the preset (this file is optional), and
- ```<devicename>.cmap``` containing a textual representation of the CC-map Python data structure. 

See [further documentation here](./makedevices-README.md)

You can copy a dumped preset in ```./dumps``` to ```./preloaded```. Better still, upload the patch in ```./dumps``` to the Electra Editor, change the layout, and then download it again, saving it to ```./preloaded```. Do *not* change the assigned CC parameter numbers (these should be the same in both the patch (```.epr```) and the corresponding CC-map (```.ccmap```). Save any LUA script you added to the preset to the corresponding LUA file (```.lua```). 

The remote script is actually completely oblivious about the actual preset it uploads to the E1: it only uses the information in the CC-map to map CC's to Ableton Live parameters, to decide which MIDI channel to use, and to decide whether to use 7 or 14 bit control assignments. It is up to the patch to actually have the CCs listed in the map present, have it mapped to a control with the specified index and mapped to a device with that correct MIDI channel, and to ensure that the number of bits assigned is consistent. Also, the MIDI port in the preset must correspond to what the remote script expects; so leave that value alone.

If you set the control identifier in the CC-map of a parameter to the actual identifier in the preset (instead of -1), the remote script sends the textual representation of the current value of the parameter as reported by Ableton Live to the E1. To make sure it is displayed, set the ```formatter``` function field in the E1 preset to ```defaultFormatter```.

Apart from that, anything goes. This means you can freely change controller names, specify value ranges and assign special formatter functions. Also, you can remove controls that you hardly ever use and that would otherwise clutter the interface.

## Advanced configuration

The behaviour of the remote script can be changed by editing ```config.py```:

- ```E1_PRESET_FOLDER``` subfolder on the E1 where the preloaded presets are stored, relative to ```ctrlv2/presets``` (only possible for E1 with firmware 3.4 and higher). The default is ```xot/ableton```.
- ```E1_LOGGING``` controls whether the E1 should send log messages, and if so how detailed. Default ```-1``` (which means no logging). Other possible levels: ```0``` (critical messages and errors only), ```1``` (warning messages), ```2``` (informative messages), or ```3``` (tracing messages).
- ```E1_LOGGING_PORT``` controls which port to use to send log messages to (0: Port 1, 1: Port 2, 2: CTRL). Default is 2, the CTRL port.
- ```DUMP``` controls whether the preset and CC map information of the  currently appointed device is dumped  (to ```LIBDIR/dumps```). The default is ```False```.
- ```RESET_SLOT``` (default ```(5,11)``` i.e the last, lower right slot in the sixth bank); when selected the remote script resets.
- ```EFFECT_REFRESH_PERIOD``` amount of time (in 100ms increments) between successive refreshes of controls on the E1 whose string values need to be provided by Abelton (default is 2).
- ```E1_PORT``` port number used by the remote script for input/output (0: Port 1, 1: Port 2, 2: CTRL), i.e. the one set in Ableton Live preferences. (Default is 0).
- ```E1_PORT_NAME``` (default is ```Electra Controller Electra Port 1```), the name of ```E1_PORT``` to use to upload presets using ```sendmidi```

The following constant deals with the slot where device presets are loaded.

- ```EFFECT_PRESET_SLOT``` E1 preset slot where the preset controlling the currently appointed device is stored. Specified by bank index (0..5) followed by preset index (0.11). The default is ```(5,1)```.

The following constants *only* influence the construction of presets 'on the fly' and do not affect preloaded presets:

- ```MAX_CC7_PARAMETERS``` and ```MAX_CC14_PARAMETERS``` limits the number of parameters assigned as CC7 or CC14 parameters. If ```-1``` (the default) all parameters are included (limited by the number of available MIDI channels and CC parameter slots): this is a good setting when dumping devices and/or when setting ```ORDER = ORDER_DEVICEDICT```
- ```MIDI_EFFECT_CHANNEL``` is the first MIDI channel to use to assign device parameters controls to. The default value is 11.
- ```MAX_MIDI_EFFECT_CHANNELS``` limits the number of MIDI channels used in a preset constructed on the fly; -1 means all MIDI channels are used. If this means that there are more parameters then available CC numbers, those parameters are not assigned. The default is -1.

The following constants deal with the mixer preset.

- ```MIXER_PRESET_SLOT``` E1 preset slot where the master preset is stored. Specified by bank index (0..5) followed by preset index (0..11). The default is ```(5,0)```.
- ```MIDI_MASTER_CHANNEL```,  ```MIDI_TRACKS_CHANNEL``` and ```MIDI_SENDS_CHANNEL``` set the distinct MIDI channels to map the master, track, and sends controls to. See the [technical documentation](./DOCUMENTATION.md) for details.
- ```MAX_NO_OF_SENDS``` sets the maximum number of sends (and return tracks) present on the controller (currently 6).
- ```NO_OF_TRACKS``` sets the number of tracks present on the controller (currently 5).
- ```FORW_REW_JUMP_BY_AMOUNT```the number of beats to jump ahead or back when rewinding or moving forward. The default is 1.

The following constants deal with the equaliser devices managed through the mixer preset

- ```TRACK_EQ_DEVICE_NAME``` and ```MASTER_EQ_DEVICE_NAME```: (class)name of the equaliser device (on the normal tracks and the master track respectively) to be managed by the mixer preset.
- ```TRACK_EQ_CC_MAP``` and ```MASTER_EQ_CC_MAP```: CC mapping information describing which equaliser controls are mapped, and through which CC.


### Setting up logging

To log all events (also those that happen on the E1 itself), set ```DEBUG=5``` and ```E1_LOGGING=True``` in ```config.py``` (setting ```E1_LOGGING=False``` will still give a lot of debugging information without any logging from the E1). On the MAC, this should create log messages in ```~/Library/Preferences/Ableton/Live <version>/Log.txt``` (where ```~``` is your home folder). 

To actually catch the log messages from the E1 in the same log file set ```E1_LOGGING_PORT=0```. This directs the log messages from the E1 to Port 1 connected to Live. 

Alternatively, leave the default ```E1_LOGGING_PORT=2``` as is which direct log messages from the E1 to its CTRL port, and catch the log messages from the E1 independently either using the (old) E1 Console app or using the debugger in the [web app](https://app.electra.one), see [the E1 documentation](https://docs.electra.one/editor.html#lua-debugger)
for more information.

If you want to help to debug the remote script, you can extract the tail of the messages in this log file that were logged right before the bug, and submit a bug report.

