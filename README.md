# ElectraOne

Ableton Live MIDI Remote Script for the Electra One.

## How it works

This Ableton Live MIDI Remote script allows you to control the parameters of the currently selected device in Ableton Live using the [Electra One](https://electra.one). 

It looks for a preloaded preset in ```Devices.py``` and uses that if it exists. If not, it creates a preset on the fly. The preset is uploaded to the Electra One to the currently selected preset slot (*overwriting any preset currently present in that slot*). All controls in the preset are mapped to the corresponding parameter in the device.

When constructing presets:
- on/off parameters are shown as toggles on the Electra One. 
- other 'quantised' parameters are shown as lists on the Electra One, using the possible values reported by Ableton. (In Electra One terms, these are turned into 'overlays' added to the preset.)
- non-quantised parameters are shown as faders on the Electra One. As many faders as possible are assigned to 14bit CCs. (These CCs actually occupy *two* slots in the CC map, see below.)
- Integer values, non-quantised, parameters are shown as integer-values faders on the Electra One. Other faders simply show a value within the minimum - maximum CC value range.

## Preset dumps

Constructed presets can be dumped, along with associated CC mapping information for fine tuning the preset as shown on the Electra One (e.g. parameter layout, assingment over pages, colours, groups). The  updated information can be added to ```Devices.py``` to turn it into a preloaded preset.

Such a dump constructs a file ```<devicename>.json``` with the JSON preset (which can be uploaded to the [Electra Editor](Https://app.electra.one)), and a file ```<devicename>.ccmap``` listing for each named parameter the following tuple

- the MIDI channel,
- whether it is a 14bit controler (1: yes, 0: no), and
- the CC parameter number (between 1 and 127) that controls it in the preset. ```None``` means the parameter is not/could not be mapped. 

Note that the actual CC parameter used for a 14bit control is cc_np *and* cc_no+32 (because by convention a 14bit CC value is sent using the base CC and its 'shadow' parameter 32 higher.

Dumps are written in the folder ```<LOCALDIR>/dumps``` (see documentation of ```LOCALDIR``` below).


## Preloaded presets

Preloaded presets are stored in ```Devices.py```. The Python script ```makedevices``` creates this file based on all presets stored in ```./preloaded``` (using the ```<devicename>.epr``` and ```<devicename>.cmap``` it finds there).

You can copy a dumped preset in ```./dumps``` to ```./preloaded``` (renaming the ```.json``` extension to ```.epr```). Better still, upload the ```json``` patch in ```./dumps``` to the Electra Editor, change the layout, and then download it again, saving it to ```./preloaded```. Do *not* change the assigned CC parameter numbers (these should be the same in both the patch (```.epr```) and the corresponding CC-map (```.ccmap```). 

The remote script is actually completely oblivious about the actual preset it uploads to the Electra One: it only uses the information in the CC-map to map CC's to Ableton Live parameters, to decide which MIDI channel to use, and to decide whether to use 7 or 14 bit control assignments. It is up to the patch to actually have the CCs listed in the map present, have it mapped to a device with that correct MIDI channel, and to ensure that the number of bits assigned is consistent. Also, the MIDI port in the preset must correspond to what the remote script expects; so leave that value alone.

Apart from that, anything  goes. This means you can freely change controller names, specify value ranges and assign special formatter functions. 

 
## Warning

**This is *alpha* software.**

It was built using the [excellent resources](https://structure-void.com/ableton-live-midi-remote-scripts/) provided by Julien Bayle (StructureVoid), and Hanz Petrov's [introduction to remote scripts](http://remotescripts.blogspot.com/2010/03/introduction-to-framework-classes.html). Also the incredibly well maintained [documentation](https://docs.electra.one) for the Electra One itself was super useful.

However, official documentation from Ableton to program MIDI remote scripts is unfortunately missing. This means the code seems to work, but I don't really know *why* it works. Clearly, this is dangerous. 

**Use at your own risk!**

## Installation

Copy all Python files to your local Ableton MIDI Live Scripts folder (```~/Music/Ableton/User Library/Remote Scripts/``` on MacOS and
```~\Documents\Ableton\User Library\Remote Scripts``` on Windows) into a directory called ```ElectraOne````.

Add ElectraOne as a Control Surface in Live > Preferences > MIDI. Set the input port to ```Electr Controller (Electra Port 1)``` and the output port to ```Electr Controller (Electra CTRL)```. For both, tick the *Remote* boxes in the MIDI Ports table below. See:

[img]

A patch for any device selected (the 'Blue Hand') will automatically be constructed (or loaded), uploaded and then mapped to the Electra One

See ```~/Library/Preferences/Ableton/Live <version>/Log.txt``` for any error messages (on MacOS).

## Configuring

The behaviour of the remote script can be changed by editing ```config.py ```:

- ```LOCALDIR```determines where external files are read and written. This is first tried as a directory relative to the user's home directory; if that doesn't exist, it is interpreted as an absolute path. If that also doesn't exist, then the user home directory is used instead (and ```./dumps``` or ```./user-presets``` are not appended).
- ```DEBUG``` controls whether debugging information is written to the log file. Set to ```False``` to speed up the script.
- ```DUMP ``` controls whether the preset and CC map information of the  currently selected device is dumped  (to ```LOCALDIR/dumps```).
- ```ORDER``` specifies whether presets that are constructed on the fly arrange parameters in the preset in alphabetical order, or simply in the order given by Ableton.

## Current limitations

- Value changes in Abelton (and current values when selecting a device) are not shown in the Electra One preset. (This is due to the fact that presets *need* to be sent to the Electra One over the CTRL port, which ignores incoming CC messages (that encode value changes).
- User-defined presets not defined yet. (You *can* add them to ```Devices.py```.)
- Value handling is quite rudimentary at the moment. Values do not follow the way values are shown in Ableton (and other remote controllers like Novation RemoteSL line), like showing the actual float value, percentages, semitones etc.
- The 'Blue Hand' is not showing. However, the currently selected device *is* mapped.
- Uploading large patches is *slow*.

## Dependencies

This project depends on:

- Ableton Live 11, tested with version 11.1.1 (code relies Abelton Live supporting Python 3.6).
- Electra One firmware version 2.1.8a (to allow sending of both SysEx preset uploads and MIDI CC changes over *one* MIDI port). See [these instructions for uploading firmware](https://docs.electra.one/troubleshooting/hardrestart.html#recovering-from-a-system-freeze) that you can [download here](https://docs.electra.one/downloads/firmware.html).

## Recovering from errors

Should the Electra get bogged with presets or freeze, use this procedure for a 'factory reset'.

1. Disconnect Electra from the USB power.
2. Press and hold left middle button.
3. While keeping the button pressed, connect the USB power.
4. Keep the button pressed until the splash screen animation is completed

This procedure will remove all presets, Lua scripts, config files.

See [##Dependencies] on how to update the firmware.
