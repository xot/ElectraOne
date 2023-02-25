# makedevices documentation

The makedevices script collects preloadable presets and stores them in Devices.py for use by the E1 remote script.

The input to the script are the following types of files stored in the folder  ```./preloaded```:


- ```<devicename>.epr```, the preset in JSON format, as [documented here](https://docs.electra.one/developers/presetformat.html#preset-json-format); it is minified by the script. This file must exist. (If not, all other corresponding files are ignored and a preloaded preset is not stored for this device.)
- ```<devicename>.cmap``` containing a textual representation of the CC-map Python data structure. This file must exist.
- ```<devicename>.lua```, containing additional LUA functions used within the preset. This file is optional.
- ```<devicename>.remap```, containing a dictionary of controls whose page assignment must be remapped, see below. This file is also optional.

## Contol page remapping

Certain Ableton devices show different controls depending on the value of other controls. For example, many devices have both 'rate' and 'frequency' controls, that are visible depending on the settings of the 'sync' control. To mimic this behaviour in a preloaded preset on the E1, one can create two separate controls (one for say the frequency and another for the rate), whose visibility as controlled using a LUA function triggered by the sync control. For example ```Shifter.lua``` contains the following code, where ```delaysync``` is the formatter function for the "DELAY SYNC" control:

```
dtime = controls.get(31)
dsync = controls.get(32)

function delaysync(valueObject, value)
    if value == 0 then
        dtime:setVisible(true)
        dsync:setVisible(false)
	    return("Delay Sync")
    else
        dtime:setVisible(false)
        dsync:setVisible(true)
	    return("Delay Sync")
    end
end
```

The idea is to display them on the exact same spot in the preset (and to control them with the same pot), but the preset editor only allows at most one control in a particular slot. The preset format however does allow more than one control to be present on the same slot on the same page. The trick is therefore to create presets in the preset editor with all the different controls (that need to be mapped on the same location on the same page) on a *different* page but at the same slot. 

The makedevices script changes the page assignment of these controls based on the information in the ```<devicename>.remap``` file. This file contains a dictionary mapping control identifiers (or preset control labels) to the page they need to be remapped on. Note: the script uses the (all caps) labels for the controls (as derived from the device parameter name).

For example the Shifter remap file contains the following dictionary:

```
{ "FSHIFT COARSE": 1,
  "RM COARSE": 1,
  "MOD FINE": 1,
  "ENV AMOUNT ST": 1,
  "DEALY S. TIME": 1,
  "LFO S. RATE": 1,
  "LFO AMOUNT ST": 1
}
```

The makedevices script also removes any pages with index larger than 6 whose name starts with ```Page ```. Remapped controls are therefore best placed on pages with index larger than 6. Giving a page a meaningful name prevents it from being deleted.
