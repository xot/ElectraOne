# makedevices documentation

The makedevices script collects preloadable presets and stores them in Devices.py for use by the E1 remote script.

The input to the script are the following types of files stored in the folder  ```./preloaded```:


- ```<devicename>.epr```, the preset in JSON format, as [documented here](https://docs.electra.one/developers/presetformat.html#preset-json-format); it is minified by the script. This file must exist. (If not, all other corresponding files are ignored and a preloaded preset is not stored for this device.)
- ```<devicename>.cmap``` containing a textual representation of the CC-map Python data structure. This file must exist.
- ```<devicename>.lua```, containing additional LUA functions used within the preset. This file is optional.

