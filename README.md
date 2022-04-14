# ElectraOne

Ableton Live MIDI Remote Script for the Electra One


## Installation

Copy all Python files to your local Ableton MIDI Live Scripts folder (```~/Music/Ableton/User Library/Remote Scripts/``` on MacOS and
```~\Documents\Ableton\User Library\Remote Scripts``` on Windows) into a directory called ```ElectraOneDump````.

Add ElectraOne as a Control Surface in Live > Preferences > MIDI.

A patch for any device selected (the 'Blue Hand') will automatically be constructed (or loaded), uploaded and then mapped to the Electra One

See ```~/Library/Preferences/Ableton/Live <version>/Log.txt``` for any error messages.

## Dependencies

This project depends on [ElectraOneDump](https://github.com/xot/ElectraOneDump), specifically the 
```ElectraOneDumper.py``` module.
