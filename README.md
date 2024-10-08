# ElectraOne

Ableton Live MIDI Remote Script for the Electra One.

## What it does

This Ableton Live MIDI Remote script allows you to control [the session mixer](#the-mixer) and the parameters of the [currently selected device](#controlling-the-currently-appointed-device) in Ableton Live using the [Electra One](https://electra.one), E1 for short. 

It can also be used to dump E1 presets for Ableton Live devices with sensible default control assignments, which can be used to craft your own preset designs to control these devices.

The remote script comes with a default Ableton Live template (`Live template.als`) that has several Channel EQs configured on the tracks, together with an [E1 mixer preset](#the-mixer) (`Mixer.eproj`) to control it.

The remote script also comes with specially crafted predefined presets for most of the Ableton Live effects and instruments.


(*Note: this is a beta release, but it should be relatively stable and usable by now. The current version works best with E1 firmware version 3.5 or higher*)

## The mixer

The mixer preset controls five consecutive session tracks parameters: pan, volume, mute, solo and arm. The 'prev tracks' and 'next tracks' buttons on the main page switch control to the previous five or next five tracks (never shifting left of the first or right of the last visible track). Inserted or removed tracks are automatically handled. The 'Main' mixer page also contains controls for the master pan, volume, cue volume, and solo switch. And it contains the following transport controls: play/stop, record, and dials to change the playing position and the tempo.

![Main](./images/main.png "Main")


For each track, the level of at most six sends can be controlled (see the 'Sends' page). Note that the sends on the return tracks (that are disabled by default in Live) are not included and cannot be controlled by the mixer.

![Sends](./images/sends.png "Sends")

The return track corresponding to each send can be managed using the controls on the 'Returns' page: pan, volume, and mute.

![Returns](./images/returns.png "Returns")

Finally a separate 'Channel EQs' page contains controls the parameters of an equaliser device (by default the Channel EQ device), when present on an audio/midi track or the master track. (When more than one ChannelEq device is present on a track, the last, rightmost ChannelEq device will be controlled.)

![Channel EQs](./images/channeleqs.png "Channel EQs")

All controls on all pages are synced with the values of the parameters in Live they control as soon as a selection changes, or when parameters in Live are changed through the UI or using a different controller.

When fewer than 5 tracks and fewer than 6 return tracks are present in the Live set, the controls on track strips on the E1 for tracks that are not present in Live are hidden.


The mixer preset is included in the distribution (`Mixer.eproj`), and is also [available in the online E1 preset library](https://app.electra.one/preset/CK3qbv7Vt43PN4LkBTy7). 


*Note: after installing the remote script (see below) you must also upload the mixer preset to bank 6, slot 1 (see [the E1 documentation](https://docs.electra.one/account.html#preset-slots); search for `Ableton Mixer` in the the preset list on the right side of the page ). The remote script does not do that automatically for you! Moreover, please make sure to upload the latest version of the mixer preset each time you upgrade the script.* 

## Controlling the currently appointed device

The remote script also allows the E1 to control the currently selected device on the currently selected track in Live. This specific selected device is called the *appointed* device (and is indicated by Live using the 'Blue Hand').

The remote script comes with predefined presets for many of Ableton Live's effects and instruments. (The layout and control information for these predefined devices is stored in `Devices.py`.) The figure shows the preset for `Delay`.

Starting with firmware 3.4 on a modern E1 (the mkII, i.e hardware revision 3.0 or larger), these predefined devices can also be preloaded to the E1 for fast recall. See for [instructions below](https://github.com/xot/ElectraOne#installation).

If no preloaded or predefined preset for a device is found, the remote script will [construct one on the fly](https://github.com/xot/ElectraOne#creating-presets-on-the-fly). This is useful, for example, to control the macros in rack. 

So when you select a new device in Live, the following happens.

- First, the remote script tries to activate a preset for the device that is already preloaded on the E1. (For older, mkI, E1 this step is skipped.) 
- If that fails, it looks for a predefined preset for the device in the directory  `preloaded` and uploads and activates it.
- And if no such preset is found, the remote script constructs one on the fly and uploads that preset to the E1 instead, and activates it.

![Delay predefined preset](./images/delay.png "Delay predefined preset")

The preset is (up)loaded to the E1 to the second preset slot in bank 6 by default (*overwriting any preset currently present in that slot*). All controls in the preset are mapped to the corresponding parameter in the device. 

You can edit or add your own favourite preset layouts [as described in this separate document](https://github.com/xot/ElectraOne/blob/main/README-ADDING-PRESETS.md#adding-preloaded-device-presets).

### Known limitations

The remote script relies on the information about a device it receives from Ableton. This information is quite often wrong or incomplete. Notable examples are

- Sampler: omits a lot of important parameters (e.g. LFO settings) that therefore cannot be mapped.
- Wavetable: omits the Midi and Modulation matrix entries.
- SpectralResonator: omits the resonator type and many MIDI input controls.

### Controlling device appointment when selecting tracks

By default, if you select a different track in Live, the appointed device changes to the currently selected device on the new track (and its preset is displayed to control it). If no device is selected, the empty device is appointed instead.

If the selected track contains a device whose name starts with `!`, then this device (i.e. the first one on the track with such a special name) becomes appointed instead of the selected device.

If you set `APPOINT_ON_TRACK_CHANGE` to `False`, changing tracks does not change the appointed device.

### Creating presets on the fly

If no preloaded or predefined preset exists, the remote script creates a preset on the fly. (The image shows the preset created on the fly for the Saturator effect, in 'sorted' order, see below.)

![Preset created on the fly](./images/saturator.png "Preset created on the fly")

When constructing presets:

- On/off parameters are shown as toggles on the E1.
- Other 'quantised' parameters are shown as lists on the E1, using the possible values reported by Ableton. (In E1 terms, these are turned into 'overlays' added to the preset.)
- Non-quantised parameters are shown as faders on the E1. As many faders as possible are assigned to 14bit CCs. 
- Integer valued, non-quantised, parameters are shown as integer-valued faders on the E1. 
- Float valued parameters are shown as float-valued faders on the E1. 
- For certain types of parameters (e.g. percentage, phase shift), the remote script tries to guess the type and adjust the display accordingly.

Note that large devices with many parameters may create a preset with several pages. The generation of presets on the fly can be customised, see the [configuration section](https://github.com/xot/ElectraOne#configuring).

### Racks

When selecting a rack (audio, instrument, drum or MIDI rack), the E1 automatically creates a preset containing all macros in the rack, and uploads that to the E1 so they can be controlled.

*Note: when using a drum rack on a visible track, by default it shows the last played drum instrument in the chain. Whenever an incoming note plays a drum instrument, this drum instrument becomes selected **and therefore gets (up)loaded to the E1**. This is of course undesirable as the E1 would get swamped with preset (up)loads. To avoid this, hide the devices on a drum track!*


### VST or AU plugins

VST or AU plugin parameters can also be managed, but this needs to be done in a slightly roundabout way in order to ensure the mappings are properly saved with the Live set.

Depending on the plugin, *first* create an audio or instrument rack. Then add the plugin to the rack. To manage the parameters within the plugin, click on the expand (triangle down) button in the title bar of the plugin to expose the 'Configure' button. Click on it and follow the instructions to add plugin parameters to the configuration panel. To save this configuration, *save the enclosing rack configuration*: saving the plugin state itself *does not save the configuration of parameters*! You don't need to bother about the macros, although it might be useful to assign them such that the most important parameters of the plugin are mapped on a single preset page.

You can also create your own custom presets for VST or AU plugins. The general process to create custom presets is [described here](https://github.com/xot/ElectraOne/blob/main/README-ADDING-PRESETS.md). For VST or AU plugins you need to be aware of a [some naming conventions](https://github.com/xot/ElectraOne/blob/main/README-ADDING-PRESETS.md#naming).

#### Configuring Ableton to map AU and VST plugin parameters

To more easily control the parameters of AU and VST plugins in Ableton, you can tell Ableton to automatically configure and reveal the plugin parameters. This is done by adding the following line to Ableton Live's `Options.txt` file (see this [Ableton help document](https://help.ableton.com/hc/en-us/articles/6003224107292-Options-txt-file) on where to find it and how to edit it).

`-_PluginAutoPopulateThreshold=128`

Note the hyphen followed by the underscore! Also this is not guaranteed to work for all plugins; I've seen it work for AU plugins but not for VSTs on MacOS.

#### Limitations

Certain plugins poorly report their parameters internally, making it hard for the remote script to create a proper preset on the fly. For example, the AU version of the Arturia Mini V3 plugin reports its parameters internally as integers between 0 and 1, creating a totally unusable preset :-( 
The VST version does report its parameters correctly, but for that variant the 
option to automatically configure and reveal the plugin parameters (see above) does not work.

You can add the name of such a device to the `BORKED_DEVICES` configuration option to tell the algorithm that creates presets on the fly to ignore the parameter information provided by such a device and generate floating point faders for the parameters by default.
  
## Switching between device and mixer view

You can use the normal way of switching between presets on the E1 via the MENU button. 

There is a faster way however (when `CONTROL_MODE=CONTROL_EITHER`).
Pressing the PRESET REQUEST button on the E1 (right column, top button) will
alternate between the mixer and the appointed device preset.

## Installation

Make sure that the version of Ableton Live and the firmware of the E1 are supported (see below).


1. For *MacOS*: download the [ElectraOne.MacOS.zip](https://github.com/xot/ElectraOne/blob/main/install/ElectraOne.MacOS.zip?raw=true) zip file from the repository. (When using Safari, [make sure that the zip file is not automatically unpacked](https://www.howtogeek.com/789559/how-to-stop-safari-from-automatically-unzipping-downloaded-files-on-mac/).) Save it *in your home directory*. Double click it to extracts all files. This should create `~/Music/Ableton/User Library/Remote Scripts/ElectraOne` with all the necessary files. (`~` is a shorthand for your home directory here.)

   For *Windows*: download the [ElectraOne.Windows.zip](https://github.com/xot/ElectraOne/blob/main/install/ElectraOne.Windows.zip?raw=true) zip file from the repository. (Right click and select "Extract All..." from the drop down menu. Select your *home directory* as the destination (using "Browse...") and click "Extract". This should create `~\Documents\Ableton\User Library\Remote Scripts\ElectraOne` with all the necessary files. (`~` is a shorthand for your home directory here.)

2. Connect the E1 to your computer with a USB cable ([see E1 documentation](https://docs.electra.one/#_2-connect-your-new-electra-one-controller-to-a-computer)).

![Ableton Preferences](./images/ableton.png "Ableton Preferences")

3. For *MacOS*: Add E1 as a Control Surface in Live > Preferences > MIDI. Set the both the input port and the output port to `Electra Controller (Electra Port 1)`. For both, tick the *Remote* boxes in the MIDI Ports table below, untick the *Track* boxes. 

   For *Windows*: Add E1 as a Control Surface in Options > Preferences > MIDI. Set the both the input port and the output port to `Electra Controller`. For both, tick the *Remote* boxes in the MIDI Ports table below, untick the *Track* boxes.

4. Upload the `Mixer.eproj` preset (included in the distribution) to the E1 to bank 6, slot 1.  See [above](https://github.com/xot/ElectraOne/blob/main/README.md#the-mixer).

5. If you run firmware version 3.4 or higher (*which is highly recommended because of the speed increase*) *and* own a E1 mkII, unpack the archive `upload-to-E1.zip` in the folder `ctrlv2` on the E1. (To do so, on an E1 mkII you need to [enable USB Disk mode](https://docs.electra.one/downloads/updatemkII.html#_4-enable-the-usb-disk-option).) This should create a file `ctrlv2/lua/xot/default.lua` and a  folder `ctrlv2/presets/xot/ableton` containing all preloaded presets and their associated LUA scripts. The `.ccmap` do not need to be uploaded and are therefore not included in `upload-to-E1.zip`.

7. Start Ableton.

If all goes well, a patch for the appointed device (indicated by the 'Blue Hand') will automatically be created and/or (up)loaded and then mapped to the E1.

Enjoy!


You can edit or add your own favourite preset layouts [as described in this separate document](https://github.com/xot/ElectraOne/blob/main/README-ADDING-PRESETS.md) Be sure to read the separate [Tips & Tricks](https://github.com/xot/ElectraOne/blob/TIPS_AND_TRICKS.md) too!


### Log files

See 

- `~/Library/Preferences/Ableton/Live <version>/Log.txt` (on MacOS), or
- `~\AppData\Roaming\Ableton\Live <version>\Preferences\Log.txt` (on Windows)

for any error messages (again note that `~` stands for your home directory).

The log files in

- `~/Library/Application\ Support/Ableton/Live\ Reports/Usage` (MacOS), or
- `~\AppData\Roaming\Ableton\Live Reports\Usage\` (Windows)

are also useful.

### Installing SendMidi (MacOS only)

Although not strictly necessary, the remote script becomes much more responsive (and usable) under MacOS if you install [SendMidi](https://github.com/gbevin/SendMIDI). (*It seems that sending larger MIDI messages natively through Live under Windows is faster than MacOS; SendMidi isn't necessary in that case, and is harder to install under Windows because it requires shared access to the MIDI port with which to communicate with the E1, which the default Windows MIDI driver does not support.*)

Here are the instructions for installing sendmidi 1.2.0 under MacOS.

Download the right binary [here](https://github.com/gbevin/SendMIDI/releases). Install the package by double clicking on it and following the steps in the installation program. Use the default settings (ie do not change the install location). This will create the sendmidi executable in `/usr/local/bin/`. 

Set the following constants in the `config.py` (this is one of the files you just copied into the new `ElectraOne` folder that you created in your local Ableton MIDI Live Scripts folder):

- `SENDMIDI_CMD = /usr/local/bin/sendmidi`
- `E1_PORT_NAME = 'Electra Controller Electra Port 1'` (or whatever the exact name of MIDI Port 1 of the ElectraOne happens to be on your system; the value shown here is the default. Running the command `sendmidi list` returns the list of ports SendMidi knows about.).


### Dependencies

This project depends on:

- Ableton Live 12 (tested with 12.0) or Ableton Live 11, tested with version 11.1.1 upto 11.3.12; code relies on Abelton Live supporting Python 3.6 or later.
- E1 firmware version 3.5 or later. See [these instructions for uploading firmware](https://docs.electra.one/troubleshooting/hardrestart.html#recovering-from-a-system-freeze) that you can [download here](https://docs.electra.one/downloads/firmware.html).
- Optional: [SendMidi](https://github.com/gbevin/SendMIDI), for faster preset uploading. 

### Current limitations

- Uploading large patches is *slow*, unless you enable fast loading. (Best to stick to preloaded patches or setting `ORDER = ORDER_DEVICEDICT`, which is the default.)

### Warning

**This is *beta* software.**

It was built using the [excellent resources](https://structure-void.com/ableton-live-midi-remote-scripts/) provided by Julien Bayle (StructureVoid), and Hanz Petrov's [introduction to remote scripts](http://remotescripts.blogspot.com/2010/03/introduction-to-framework-classes.html). Also the incredibly well maintained [documentation](https://docs.electra.one) for the E1 itself was super useful.

However, official documentation from Ableton to program MIDI remote scripts is unfortunately missing. This means the code seems to work, but I don't really know *why* it works. Clearly, this is dangerous. 

**Use at your own risk!**

## Configuring

The behaviour of the remote script can be changed by editing `config.py`. Below the most basic configuration options are documented. More advanced configuration options are discussed [here](xx)

- `DEBUG` the amount of debugging information that is written to the log file. Larger values mean more logging. Set to `-1` to create no log entries and to speed up the script.
- `DETECT_E1` controls whether to detect the E1 at startup, or not. Default is `True`.
- `CONTROL_MODE` whether the remote script controls both mixer and effect (`CONTROL_EITHER`), the mixer (`CONTROL_MIXER_ONLY`) or the effect only (`CONTROL_EFFECT_ONLY`).
- `USE_ABLETON_VALUES`. Whether to use the exact value strings Ableton generates for faders whose value cannot be easily computed by the E1 itself (like non-linear frequency and volume sliders). Default is `True`.
- `SENDMIDI_CMD` full path to the `sendmidi`command. If `None`(the default), fast uploading of presets is not supported.
- `USE_PRELOAD_FEATURE`. Whether to use the preloaded presets feature (if supported). If false, the predefined presets in `Devices.py` are always used, overriding any (older) preloaded presets on the E1. Default is `True`.
- `POSITION_FINE`. Whether to update the position with every sub_division  change, or only every beat. Default is `True`.
- `TIMEOUT_STRETCH` Factor to stretch the timout when uploading presets or LUA scritps to compensate for slow working conditions. Default is 1.
- `EFFECT_REFRESH_PERIOD` Length of time (in 100ms increments) between successive refreshes of controls on the E1 whose string values need to be provided by Abelton. Default: 2.
- `MIXER_CLIPS_REFRESH_PERIOD` Length of time (in 100ms increments) between successive refreshes of session clips on the E1 mixer (E1_DAW only). Defualt: 20.
- `MIXER_TRACKS_REFRESH_PERIOD` Length of time (in 100ms increments) between successive refreshes of the visible tracks on the E1 mixer. Default: 20.


If the sendmidi command cannot be found or fails, the remote script falls back to normal (slow) sending of presets through Live itself.

The following constants configure when a device is *appointed* (becomes the device to manage by the remote controller(s)) and how to respond to that.

- `APPOINT_ON_TRACK_CHANGE` Whether to appoint the currently selected device on a selected track (only guaranteed to work if this is the only remote script handling device appointment), or only do this when device is explicitly selected. Default is `True`.
- `SWITCH_TO_EFFECT_IMMEDIATELY`  Whether to switch immediately from the mixer preset to the effect preset whenever a new device is appointed in Ableton, or only switch when explicitly requested by the user by pressing the upper right preset request button on the E1. Default is `True`.

The following constants *only* influence the construction of presets 'on the fly' and do not affect predefined or preloaded presets:

- `PRESET_COLOR` Default color to use for controls in a generated preset, as a hex-string (default is white, i.e.  `FFFFFF`).
- `ORDER` specifies whether presets that are constructed on the fly arrange parameters in the preset in alphabetical order (`ORDER_SORTED`),  simply in the order given by Ableton (`ORDER_ORIGINAL`) or in the order defined in the Ableton Live remote script framework (`ORDER_DEVICEDICT`, the default). This is the same order as used by most other remote controllers, as this limits the shown controllers to only the most significant devices. Indeed, when selecting the latter option, any parameters not in the 'DEVICE_DICT' are not included in the JSON preset. (They *are* included in the CC map for reference, with a mapping of `None`, but *not* in the dumped preset; you may therefore want to use `ORDER_SORTED` when dumping presets.)
- `BORKED_DEVICES` is a list of device names with unreliable paramater information for which the preset constructed on the fly should assume all parameters are floats (default `["MiniV3"]`, a known offender).
- `PARAMETERS_TO_IGNORE` a dictionary, keyed by device name, containing for each device a list of names of parameters to ignore when constructing presets on the fly. The list with key "ALL" contains the names of parameters to ignore for all presets constructed on the fly. Can e.g. be used to exclude the "Device On" button normally included (setting `{"ALL": ["Device On"]}`). Default `{}`.
- `PERSONAL_DEVICE_DICT` Personal DEVICE_DICT: for named devices, contains a tuple of tuples containing the names of the parameters to include if `ORDER=DEVICE_DICT` e.g. `PERSONAL_DEVICE_DICT = { 'Emit': ( ('Attack', 'Decay' ), ) }`  Do not forget a trailing comma (,) if you only add one tuple! Takes precedence over any entry for the same device in the global `DEVICE_DICT`. Default `{}`.

### Setting up logging

To log all events (also those that happen on the E1 itself), set `DEBUG=5` and `E1_LOGGING=True` in `config.py` (setting `E1_LOGGING=False` will still give a lot of debugging information without any logging from the E1). On the MAC, this should create log messages in `~/Library/Preferences/Ableton/Live <version>/Log.txt` (where `~` is your home folder). 

To actually catch the log messages from the E1 in the same log file set `E1_LOGGING_PORT=0`. This directs the log messages from the E1 to Port 1 connected to Live. 

Alternatively, leave the default `E1_LOGGING_PORT=2` as is which direct log messages from the E1 to its CTRL port, and catch the log messages from the E1 independently either using the (old) E1 Console app or using the debugger in the [web app](https://app.electra.one), see [the E1 documentation](https://docs.electra.one/editor.html#lua-debugger)
for more information.

If you want to help to debug the remote script, you can extract the tail of the messages in this log file that were logged right before the bug, and submit a bug report.


## Recovering from errors

### Slow preset selection/upload

Sometimes preloaded preset selection or preset upload is slow. Powering off the E1 and reconnecting it may help.


### Resetting the E1 

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

### Resetting the remote script

Occasionally, the remote script or the E1 may get in a bad state.

You can unplug and then replug the E1 to restart it and continue to use it with the remote script to see if that solves the problem. (See below for [how to completely reset](#recovering-from-errors) and remove all existing presets from it.)

If the remote script appears to have stopped working (typically noticeable if selecting a new device does not upload or change anything on the E1) you can reset the remote script by selecting the 'reset slot' on the E1 (by default this is the last, lower right slot in the sixth bank).

## Bug reports

If you encounter something you believe is a bug, please report it to me by email: [info@xot.nl](mailto:info@xot.nl). You can also create a [Github Issue](https://github.com/xot/ElectraOne/issues).

In the bug report please include:

- a concise description of the bug as subject,
- the firmware version your E1 runs,
- the version of Ableton Live you are running,
- the operating system (and version) Live runs on, and 
- a longer description of the bug, including what conditions seem to cause it and how exactly the bug manifests itself. Includes the (relevant contents) of the log-file (see [above](#log-files)). If necessary, increase `DEBUG`, restart Live, and trigger the bug again. See above for how to create a useful log.

Before submitting a bug report, please have a look at the [current issues](https://github.com/xot/ElectraOne/issues) to see whether your bug has already been reported on earlier. You can also monitor this page to keep track of how your bug is being resolved.
