

# Basic architecture

When the selected device changes

1. A patch for the newly selected device is uploaded to the Electra One.
   - If a user-defined patch exists, that one is used 
   - If not, the parameters for the newly selected device are retrieved and automatically converted to a Electra One patch (see ElectraOneDump) in the order in which they are retrieved from the device (using ```device.parameters```)
   
3. All the parameters in the newly selected device are mapped to MIDI CC (using ```Live.MidiMap.map_midi_cc```). For a user-defined patch, a accompanying CC map must also be defined. This dictionary defines for each device parameter name the corresponding MIDI CC parameter. If a parameter is missing from the dictionary it is not mapped.

   For an automatically converted patch MIDI CC numbers are assigned to parameters in the order in which they are retrieved from the device.
   
3. After this mapping all is set: Ableton will forward incoming MIDI CC changes to the mapped parameter, and will also *send* MIDI CC messages whenever the parameter is changed through the Ableton GUI or another control surface.

Note: for user-defined patches it is possible to assign *several different device parameters* to the same MIDI CC; this is e.g. useful in devices like Echo that have one visible dial in the UI for the left (and right) delay time, but that actually corresponds to three different device parameters (depending on the Sync and Sync Mode settings); this allows one to save on controls in the Electra One patch *and* makes the UI there more intuitive (as it corresponds to what you see in Ableton itself). 

However, changing the parameter value in the Ableton UI does not necessarily update the displayed value in that case... (but this may be due to the fact that a parameter is then wrongly mapped to 14bit (or 7bit)

Note: The current implementation maps all quantized parameters to 7-bit absolute CC values while all non quantized parameters (ie faders and dials) to 14-bit absolute values. User defined patches are responsible for making sure that this convention is followed.
