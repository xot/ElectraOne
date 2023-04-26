# ElectraOne

Ableton Live MIDI Remote Script for the Electra One.

## What it does

This Ableton Live MIDI Remote script allows you to [control the session mixer]((#the-mixer)) and the parameters of the [currently selected device](#controlling-the-currently-appointed-device) in Ableton Live using the [Electra One](https://electra.one), E1 for short. 

It can also be used to dump E1 presets for Ableton Live devices with sensible default control assignments, which can be used to craft your own preset designs to control these devices.

The remote script comes with a default Ableton Live template (```Live template.als```) that has several Channel EQs configured on the tracks, together with an [E1 mixer preset](#the-mixer) (```Mixer.eproj```) to control it.

(*Note: this is a beta release, but it should be relatively stable and usable by now.*)

## The mixer

The mixer preset is included in the distribution (```Mixer.eproj```), and should be uploaded to bank 6, first slot. *Please make sure to upload the latest version each time you upgrade the script.*

It controls five consecutive session tracks parameters: pan, volume, mute, solo and arm. The 'prev tracks' and 'next tracks' buttons on the main page switch control to the previous five or next five tracks (never shifting left of the first or right of the last visible track). Inserted or removed tracks are automatically handled. The 'Main' mixer page also contains controls for the master pan, volume, cue volume, and solo switch. And it contains the following transport controls: play/stop, record, rewind, and forward.

![Main](./images/main.png "Main")


For each track, the level of at most six sends can be controlled (see the 'Sends' page). Note that the sends on the return tracks (that are disabled by default in Live) are not included and cannot be controlled by the mixer.

![Sends](./images/sends.png "Sends")

The return track corresponding to each send can be managed using the controls on the 'Returns' page: pan, volume, and mute.

![Returns](./images/returns.png "Returns")

Finally a separate 'Channel EQs' page contains controls the parameters of an equaliser device (by defauklt the Channel EQ device), when present on an audio/midi track or the master track. (When more than one ChannelEq device is present, the last, rightmost ChannelEq device will be controlled.)

![Channel EQs](./images/channeleqs.png "Channel EQs")

All controls on all pages are synced with the values of the parameters in Live they control as soon as a selection changes, or when parameters in Live are changed through the UI or using a different controller.

When fewer than 5 tracks and fewer than 6 return tracks are present in the Live set, the controls on track strips on the E1 for tracks that are not present in Live are hidden.

### Alternative mixer designs

There is nothing specific about the design of the mixer apart from the MIDI channel, ELectra One port and CC number assignments of individual controls. This means you can freely redesign the mixer to your own needs, e.g one where tracks are laid out horizontally instead of vertically (such that all track controls are active at the same time). But please make sure that *all* controls retain both their original CC numbers *and* their original control id!

*Warning: do NOT remove any controls; this may break the script/mixer preset. The reason is that controls associated with (return) tracks that are not present in Ableton are hidden using their control id; the LUA scripting embedded in the Mixer preset responsible for that assumes these controls exist.*

As an example, an alternative mixer design is included in the distribution that shows the transport controls on all pages, at the cost of removing one return track and removing the rumble/high-pass toggle from the channel eq page. See ```Mixer.alt.eproj```. To use it, copy ```config.mixer.alt.py``` to ```config.py```.


### Using a second E1 to control the mixer

If you happen to own *two* E1s, then you can use the second one to control the mixer exclusively, while the first controls the currently selected device. 

Use a USB cable to connect the second E1 to the USB Host port on the first E1. Make sure that in the USB Host configuration on the first E1, Port 1 is selected for the second connected E1. See [these instructions](https://docs.electra.one/userinterface.html#menu). Finally, in
```config.py``` set ```CONTROL_MODE = CONTROL_BOTH```.

Before starting Ableton, ensure that the effect preset slot (bank 6 slot 2) is selected on the first E1, and the mixer preset is uploaded and selected (bank 6, slot 1) in the second E1. 

(*Both controllers apparently need to run firmware 3.1.5. or larger for this to work.*)

## Controlling the currently appointed device

In Ableton Live, each track typically has a selected device, and usually the selected device on the currently selected track is controlled by a remote control surface. This specific selected device is called the *appointed* device (and is indicated by Live using the 'Blue Hand').

The remote script looks for a preloaded preset for the appointed device in ```Devices.py``` and uses that if it exists. You can add your own favourite preset layout here. The easiest way to create such a preset (to ensure that it properly interfaces with this E1 remote script) is to modify dumps made by this script. See [below](#device-preset-dumps).

![Delay preloaded preset](./images/delay.png "Delay preloaded preset")

If no preloaded preset exists, it creates a preset on the fly. The preset is uploaded to the E1 to the second preset slot in bank 6 by default (*overwriting any preset currently present in that slot*). All controls in the preset are mapped to the corresponding parameter in the device. (The image shows the preset created on the fly for the Saturator effect, in 'devicedict' order, see below.)

![Preset created on the fly](./images/saturator.png "Preset created on the fly")

When constructing presets:
- On/off parameters are shown as toggles on the E1.
- Other 'quantised' parameters are shown as lists on the E1, using the possible values reported by Ableton. (In E1 terms, these are turned into 'overlays' added to the preset.)
- Non-quantised parameters are shown as faders on the E1. As many faders as possible are assigned to 14bit CCs. (These CCs actually occupy *two* slots in the CC map, see below.) 
- Integer valued, non-quantised, parameters are shown as integer-valued faders on the E1. Other faders simply show a value within the minimum - maximum CC value range (although for faders with a large range this is currently not the case.).

Note that large devices with many parameters may create a preset with several pages.

### Racks

When selecting a rack (audio, instrument, drum or MIDI rack), the E1 automatically maps the macro's for the rack to controls on the E1.

*Note: when using a drum rack on a visible track, by default it shows the last played drum instrument in the chain. Whenever an incoming note plays a drum instrument, this drum instrument becomes selected **and therefore gets uploaded to the E1**. This is of course undesirable as the E1 would get swamped with preset uploads. To avoid this, hide the devices on a drum track!*



### VST or AU plugins

VST or AU plugin parameters can also be managed, but this needs to be done in a slightly roundabout way in order to ensure the mappings are properly saved within Ableton.

Depending on the plugin, *first* create an audio or instrument rack. Then add the plugin to the rack. To manage the parameters within the plugin, click on the expand (triangle down) button in the title bar of the plugin to expose the 'Configure' button. Click on it and follow the instructions to add plugin parameters to the configuration panel. To save this configuration, *save the enclosing rack configuration*: saving the plugin state itself *does not save the configuration of parameters*! You don't need to bother about the macros, although it might be useful to assign them such that the most important parameters of the plugin are mapped on a single preset page.

### Configuring Ableton to map AU and VST plugin parameters

To more easily control the parameters of AU and VST plugins in Ableton, you need to tell Ableton to automatically configure and reveal the plugin parameters. This is done by adding the following line to Ableton Live's ```Options.txt``` file (see this [Ableton help document](https://help.ableton.com/hc/en-us/articles/6003224107292-Options-txt-file) on where to find it and how to edit it).

```-_PluginAutoPopulateThreshold=128```

Note the hyphen followed by the underscore! Also this is not guaranteed to work for all plugins; I've seen it work for AU plugins but not for VSTs on MacOS.



### Device preset dumps

Constructed presets can be dumped, along with associated CC mapping information. This can be used for fine tuning the preset as it will be shown on the E1 (e.g. parameter layout, assignment over pages, colours, groups). The updated information can be added to ```Devices.py``` to turn it into a [preloaded preset](#preloaded-presets).

Such a dump constructs a file ```<devicename>.epr``` with the JSON preset (which can be uploaded to the [Electra Editor](Https://app.electra.one)), and a file ```<devicename>.ccmap``` listing for each named parameter the following tuple:

- the identifier of the control on the E1, in case Ableton Live needs to send the string representation of the value of the parameter to the E1 for display, because the E1 cannot reliably determine it (-1 otherwise).
- the MIDI channel,
- whether it is a 14bit controler (1/True: yes, 0/False: no), and
- the CC parameter number (between 0 and 127) that controls it in the preset. ```None``` means the parameter is not/could not be mapped. 

For example, dumping the Echo device could create the following CC map entry:

```
'L Time': (25,11,True,14)
```

Meaning that the Echo device parameter ```L Time``` has a control with identifier 25, and is mapped on Midi channel 11 as a 14-bit control on CC parameter number 14.

Note that the actual CC parameter used for a 14bit control is cc_no *and* cc_no+32 (because by convention a 14bit CC value is sent using the base CC and its 'shadow' parameter 32 higher. (This means the constructed map may appear to have holes in the 32-63 range.)

The construction of presets is controlled by several constants defined in ```config.py```. Dumps are written in the folder ```<LIBDIR>/dumps```.
See [documentation of configuration options](#configuring) below.)


### Names used for plugins and Max devices

There is unfortunately no reliable way for the remote script to get the *device* name for a plugin or a Max device: when asking Live it returns the name of the currently loaded 'Live preset' for the plugin or Max device. This is annoying when dumping E1 presets, or defining preloaded presets (see below).

The remote script uses the following hack to still allow a fixed device name to be found. Enclose such a plugin or Max device in an instrument, midi, or audio rack and rename that enclosing rack to the name of the device. The remote script uses the name of the enclosing rack followed by a single hyphen ```-``` as the name to use for the plugin or Max device when dumping its preset or when looking up a preloaded preset. So if a plugin is in a rack with name ```MiniV3``` then ```MiniV3-``` is used as the plugin name. (If a plugin is not enclosed in a rack, then its own preset name is used as the device name.)


### Preloaded presets

Preloaded presets are stored in ```Devices.py```. The Python script ```makedevices``` creates this file based on all presets stored in ```./preloaded```, using the following files

- ```<devicename>.epr```, the preset in JSON format, as [documented here](https://docs.electra.one/developers/presetformat.html#preset-json-format); it is minified by the script, 
- ```<devicename>.lua```, containing additional LUA functions used within the preset (this file is optional), and
- ```<devicename>.cmap``` containing a textual representation of the CC-map Python data structure. 
- ```<devicename>.remap``` containing information about remapping controls to different pages (this file is also optional). 

See [further documentation here](./makedevices-README.md)

You can copy a dumped preset in ```./dumps``` to ```./preloaded```. Better still, upload the patch in ```./dumps``` to the Electra Editor, change the layout, and then download it again, saving it to ```./preloaded```. Do *not* change the assigned CC parameter numbers (these should be the same in both the patch (```.epr```) and the corresponding CC-map (```.ccmap```). Save any LUA script you added to the preset to the corresponding LUA file (```.lua```). 

The remote script is actually completely oblivious about the actual preset it uploads to the E1: it only uses the information in the CC-map to map CC's to Ableton Live parameters, to decide which MIDI channel to use, and to decide whether to use 7 or 14 bit control assignments. It is up to the patch to actually have the CCs listed in the map present, have it mapped to a control with the specified index and mapped to a device with that correct MIDI channel, and to ensure that the number of bits assigned is consistent. Also, the MIDI port in the preset must correspond to what the remote script expects; so leave that value alone.

If you set the control identifier in the CC-map of a parameter to the actual identifier in the preset (instead of -1), the remote script sends the textual representation of the current value of the parameter as reported by Ableton Live to the E1. To make sure it is displayed, set the ```formatter``` function field in the E1 preset to ```defaultFormatter```.

Apart from that, anything goes. This means you can freely change controller names, specify value ranges and assign special formatter functions. Also, you can remove controls that you hardly ever use and that would otherwise clutter the interface.

## Switching between presets

You can use the normal way of switching between presets on the E1 via the MENU button. 

There is a faster way however, when ```CONTROL_MODE=CONTROL_EITHER```.
Pressing the PRESET REQUEST button on the E1 (right column, top button) switches the currently visible preset (i.e. alternates between the mixer and the device preset).

## Resetting the remote script

Occasionally, the remote script or the E1 may get in a bad state.

You can unplug and then replug the E1 to restart it and continue to use it with the remote script to see if that solves the problem. (See below for [how to completely reset](#recovering-from-errors) and remove all existing presets from it.)

If the remote script appears to have stopped working (typically noticeable if selecting a new device does not upload or change anything on the E1) you can reset the remote script by selecting the 'reset slot' on the E1 (by default this is the last, lower right slot in the sixth bank).

## Warning

**This is *beta* software.**

It was built using the [excellent resources](https://structure-void.com/ableton-live-midi-remote-scripts/) provided by Julien Bayle (StructureVoid), and Hanz Petrov's [introduction to remote scripts](http://remotescripts.blogspot.com/2010/03/introduction-to-framework-classes.html). Also the incredibly well maintained [documentation](https://docs.electra.one) for the E1 itself was super useful.

However, official documentation from Ableton to program MIDI remote scripts is unfortunately missing. This means the code seems to work, but I don't really know *why* it works. Clearly, this is dangerous. 

**Use at your own risk!**

## Installation

Make sure that the version of Ableton Live and the firmware of the E1 are supported (see below).


1. Create a new directory ```ElectraOne``` into your local Ableton MIDI Live Scripts folder: that is ```~/Music/Ableton/User Library/Remote Scripts/``` on MacOS and ```~\Documents\Ableton\User Library\Remote Scripts``` on Windows (that directory may not exist initially, in that case create it manually). Note that ```~``` stands for your home directory (```/Users/<username>/``` on the Mac and ```C:\Users\<username>``` on recent Windows versions)

2. Copy all files and subdirectories and their contents that you find in the [ElectraOne remote script repository](https://github.com/xot/ElectraOne) to the ```ElectraOne``` directory you just created. The easiest is to download [the whole repository as a compressed zip file](https://github.com/xot/ElectraOne/archive/refs/heads/main.zip) and unpack on your computer (make sure to remove the ```ElectraOne-main``` root directory).

3. *MacOS*: Add E1 as a Control Surface in Live > Preferences > MIDI. Set the both the input port and the output port to ```Electra Controller (Electra Port 1)```. For both, tick the *Remote* boxes in the MIDI Ports table below, untick the *Track* boxes. 

![Ableton Preferences](./images/ableton.png "Ableton Preferences")

3. *Windows*: Add E1 as a Control Surface in Options > Preferences > MIDI. Set the both the input port and the output port to ```Electra Controller```. For both, tick the *Remote* boxes in the MIDI Ports table below, untick the *Track* boxes.

4. Upload the ```Mixer.eproj``` (included in the distribution) patch to the E1 to bank 6 preset 1.

Start Ableton 

A patch for the appointed device (indicated by the 'Blue Hand') will automatically be constructed (or loaded), uploaded and then mapped to the E1

See ```~/Library/Preferences/Ableton/Live <version>/Log.txt``` for any error messages (on MacOS) (again note that ```~``` stands for your home folder).

### Installing SendMidi

Although not strictly necessary, the remote script becomes much more responsive (and usable) under MacOS if you install [SendMidi](https://github.com/gbevin/SendMIDI). (*It seems that sending larger MIDI messages natively through Live under Windows is faster than MacOS; SendMidi isn't necessary in that case, and is harder to install under Windows because it requires shared access to the MIDI port with which to communicate with the E1, which the default Windows MIDI driver does not support.*)

Here are the instructions for installing sendmidi 1.2.0 under MacOS.

Download the right binary [here](https://github.com/gbevin/SendMIDI/releases). Install the package by double clicking on it and following the steps in the installation program. Use the default settings (ie do not change the install location). This will create the sendmidi executable in ```/usr/local/bin/```. 

Set the following constants in the ```config.py``` (this is one of the files you just copied into the new ```ElectraOne``` directory that you created in your local Ableton MIDI Live Scripts folder):

- ```SENDMIDI_CMD = /usr/local/bin/sendmidi```
- ```E1_CTRL_PORT = 'Electra Controller Electra Port 1'``` (or whatever the exact name of MIDI Port 1 of the ElectraOne happens to be on your system; the value shown here is the default).

## Configuring

The behaviour of the remote script can be changed by editing ```config.py```:

- ```LIBDIR```determines where external files are read and written. This is first tried as a directory relative to the user's home directory; if that doesn't exist, it is interpreted as an absolute path. If that also doesn't exist, then the user home directory is used instead.
- ```DEBUG``` the amount of debugging information that is written to the log file. Larger values mean more logging. Set to ```0``` to create no log entries and to speed up the script.
- ```E1_LOGGING``` controls whether the E1 should send log messages, default ```False```.
- ```E1_LOGGING_PORT``` controls which port to use to send log messages to (0: Port 1, 1: Port 2, 2: CTRL). Default is 2, the CTRL port.
- ```DUMP``` controls whether the preset and CC map information of the  currently appointed device is dumped  (to ```LIBDIR/dumps```). The default is ```False```.
- ```DETECT_E1``` controls whether to detect the E1 at startup, or not.
- ```RESET_SLOT``` (default ```(5,11)``` i.e the last, lower right slot in the sixth bank); when selected the remote script resets.
- ```CONTROL_MODE``` whether the remote script controls both mixer and effect (```CONTROL_EITHER```), the mixer (```CONTROL_MIXER_ONLY```) or the effect only (```CONTROL_EFFECT_ONLY```), or if two E1s are connected each controlling one of them (```CONTROL_BOTH```).
- ```USE_ABLETON_VALUES```. Whether to use the exact value strings Ableton generates for faders whose value cannot be easily computed by the E1 itself (like non-linear frequency and volume sliders). Default is ```True```.
- ```EFFECT_REFRESH_PERIOD``` amount of time (in 100ms increments) between successive refreshes of controls on the E1 whose string values need to be provided by Abelton (default is 2).
- ```SENDMIDI_CMD``` full path to the ```sendmidi```command. If ```None```(the default), fast uploading of presets is not supported.
- ```E1_PORT``` port number used by the remote script for input/output (0: Port 1, 1: Port 2, 2: CTRL), i.e. the one set in Ableton Live preferences. (Default is 0).
- ```E1_PORT_NAME``` (default is ```Electra Controller Electra Port 1```), the name of ```E1_PORT``` to use to upload presets using ```sendmidi```

If the sendmidi command cannot be found or fails, the remote script falls back to normal (slow) sending of presets through Live itself.

The following constants configure when a device is *appointed* (becomes the device to manage by the remote controller(s)) and how to respond to that.

- ```APPOINT_ON_TRACK_CHANGE``` Whether to appoint the currently selected device on a selected track (only guaranteed to work if this is the only remote script handling device appointment), or only do this when device is explicitly selected. Default is ```True```.
- ```SWITCH_TO_EFFECT_IMMEDIATELY```  Whether to switch immediately from the mixer preset to the effect preset whenever a new device is appointed in Ableton, or only switch when explicitly requested by the user by pressing the upper right preset request button on the E1. Default is ```True```.


The following constant deals with the slot where device presets are loaded.

- ```EFFECT_PRESET_SLOT``` E1 preset slot where the preset controlling the currently appointed device is stored. Specified by bank index (0..5) followed by preset index (0.11). The default is ```(5,1)```.

The following constants *only* influence the construction of presets 'on the fly' and do not affect preloaded presets:

- ```PRESET_COLOR``` Default color to use for controls in a generated preset, as a hex-string (default is white, i.e.  ```FFFFFF```).
- ```ORDER``` specifies whether presets that are constructed on the fly arrange parameters in the preset in alphabetical order (```ORDER_SORTED```),  simply in the order given by Ableton (```ORDER_ORIGINAL```) or in the order defined in the Ableton Live remote script framework (```ORDER_DEVICEDICT```, the default). This is the same order as used by most other remote controllers, as this limits the shown controllers to only the most significant devices. Indeed, when selecting the latter option, any parameters not in the 'DEVICE_DICT' are not included in the JSON preset. (They *are* included in the CC map for reference, with a mapping of ```None```, but *not* in the dumped preset; you may therefore want to use ```ORDER_SORTED``` when dumping presets.)
- ```PARAMETERS_TO_IGNORE``` a dictionary, keyed by device name, containing for each device a list of names of parameters to ignore when constructing presets on the fly. The list with key "ALL" contains the names of parameters to ignore for all presets constructed on the fly. Can e.g. be used to exclude the "Device On" button normally included (setting ```{"ALL": ["Device On"]}```). Default ```{}```.
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

## Current limitations

- Externally stored, user-defined, presets are not implemented yet. (You *can* add them to ```Devices.py```.)
- Uploading large patches is *slow*, unless you enable fast loading. (Best to stick to preloaded patches or setting ```ORDER = ORDER_DEVICEDICT```, which is the default.)


## Dependencies

This project depends on:

- Ableton Live 11, tested with version 11.1.1 upto 11.2.11 (code relies on Abelton Live supporting Python 3.6).
- E1 firmware version 3.1.5 or later. See [these instructions for uploading firmware](https://docs.electra.one/troubleshooting/hardrestart.html#recovering-from-a-system-freeze) that you can [download here](https://docs.electra.one/downloads/firmware.html).
- Optional: [SendMidi](https://github.com/gbevin/SendMIDI), for faster preset uploading. 

## Recovering from errors

Should the E1 get bogged with presets or freeze, use this procedure for a 'factory reset'.

1. Disconnect Electra from the USB power.
2. Press and hold the top left button.
3. While keeping the button pressed, connect the USB power.
4. Keep the button pressed until the splash screen animation is completed

This procedure will start the E1 without loading any presets. Manually remove any problematic ones.


To completely erase the E1 and format the internal SD do the following

1. Disconnect Electra from the USB power.
2. Press and hold the left middle button.
3. While keeping the button pressed, connect the USB power.
4. Keep the button pressed for some time.

After this you need to update the firmware. See the [section on dependencies](##dependencies) on how to do that.


## Setting up logging

To log all events (also those that happen on the E1 itself), set ```DEBUG=5``` and ```E1_LOGGING=True``` in ```config.py``` (setting ```E1_LOGGING=False``` will still give a lot of debugging information without any logging from the E1). On the MAC, this should create log messages in ```~/Library/Preferences/Ableton/Live <version>/Log.txt``` (where ```~``` is your home folder). 

To actually catch the log messages from the E1 in the same log file set ```E1_LOGGING_PORT=0```. This directs the log messages from the E1 to Port 1 connected to Live. 

Alternatively, leave the default ```E1_LOGGING_PORT=2``` as is which direct log messages from the E1 to its CTRL port, and catch the log messages from the E1 independently either using the (old) E1 Console app or using the debugger in the [web app](https://app.electra.one), see [the E1 documentation](https://docs.electra.one/editor.html#lua-debugger)
for more information.

If you want to help to debug the remote script, you can extract the tail of the messages in this log file that were logged right before the bug, and submit a bug report.

## Bug reports

If you encounter something you believe is a bug, please report it to me by email: [info@xot.nl](mailto:info@xot.nl). You can also create a [Github Issue](https://github.com/xot/ElectraOne/issues).

In the bug report please include:

- a concise description of the bug as subject,
- the firmware version your E1 runs,
- the version of Ableton Live you are running,
- the operating system (and version) Live runs on, and 
- a longer description of the bug, including what conditions seem to cause it and how exactly the bug manifests itself. Includes the (relevant contents) of the log-file (see above). If necessary, increase ```DEBUG```, restart Live, and trigger the bug again. See above for how to create a useful log.

Before submitting a bug report, please have a look at the [current issues](https://github.com/xot/ElectraOne/issues) to see whether your bug has already been reported on earlier. You can also monitor this page to keep track of how your bug is being resolved.
