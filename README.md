# ElectraOne

Ableton Live MIDI Remote Script for the Electra One.

## How it works




## Warning

**This is *alpha* software.**

It was built using the [excellent resources](https://structure-void.com/ableton-live-midi-remote-scripts/) provided by Julien Bayle (StructureVoid), and Hanz Petrov's [introduction to remote scripts](http://remotescripts.blogspot.com/2010/03/introduction-to-framework-classes.html). Also the incredibly well maintained [documentation](https://docs.electra.one) for the Electra One itself was super useful.

However, official documentation from Ableton to program MIDI remote scripts is unfortunately missing. This means the code seems to work, but I don't really know *why* it works. Clearly, this is dangerous. 

**Use at your own risk!**

## Installation

Copy all Python files to your local Ableton MIDI Live Scripts folder (```~/Music/Ableton/User Library/Remote Scripts/``` on MacOS and
```~\Documents\Ableton\User Library\Remote Scripts``` on Windows) into a directory called ```ElectraOneDump````.

Add ElectraOne as a Control Surface in Live > Preferences > MIDI. Set the input port to ```Electr Controller (Electra Port 1)``` and the output port to ```Electr Controller (Electra CTRL)```. For both, tick the *Remote* boxes in the MIDI Ports table below. See:

[img]

A patch for any device selected (the 'Blue Hand') will automatically be constructed (or loaded), uploaded and then mapped to the Electra One

See ```~/Library/Preferences/Ableton/Live <version>/Log.txt``` for any error messages.

## Configuring

IF YOU WANT TO LOAD USER DEFINED

## Dependencies

This project depends on:

- Ableton Live 11, tested with version 11.1.1  (code relies on Python 3.6)
- Electra One firmware version XXX (to allow sending of both SysEx preset uploads and MIDI CC changes over *one* MIDI port). See [these instructions for uploading firmware](https://docs.electra.one/troubleshooting/hardrestart.html#recovering-from-a-system-freeze) that you can [download here](https://docs.electra.one/downloads/firmware.html).
- [ElectraOneDump](https://github.com/xot/ElectraOneDump), specifically the 
```ElectraOneDumper.py``` module.

## Recovering from errors

Should the Electra get bogged with presets or freeze, use this procedure ofr a 'factory reset'.

1. Disconnect Electra from the USB power.
2. Press and hold left middle button.
3. While keeping the button pressed, connect the USB power.
4. Keep the button pressed until the splash screen animation is completed

This procedure will remove all presets, Lua scripts, config files.

See [##Dependencies] on how to update the firmware.
