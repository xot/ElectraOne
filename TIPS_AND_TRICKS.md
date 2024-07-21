# Tips and Tricks

## Controlling a complete Live set

It is possible to control the most significant parameters of a complete Live set using the remote script, from within a single preset (i.e. without switching back and forth). To do so, prepare your Live set as follows

- Put an audio effect rack on an audio track all by itself.
- Put as many Map8 max-for-live devices within that rack as you need (Map8 is part of the [Max for Live Essentials](https://www.ableton.com/en/packs/max-live-essentials/) pack). Each Map8 device can map 8 parameters anywhere in the live set (something you cannot do with the macro controls in a rack, which is why we need to apply this convoluted trick.)
- Map the parameters you want to control using Map8.
- Then map the Map8 controls to the macro controls on the audio rack, in the order you want them to appear in the preset. Rename macro names as appropriate. And add macro controls where needed (up to a maximum of 16.)
- Select the audio effect rack, and the mapped parameters show up on the effect control of the E1.

There is a downside though: parameter values as shown in the device preset all have value range 0-100%. This is a limitation of Map8 and I suspect (after some digging) a limitation of parameter mapping in Max itself: I cannot get the underlying parameter values/types of a parameter in Max.

## Using a second E1 to control the mixer

If you happen to own *two* E1s, then you can use the second one to control the mixer exclusively, while the first controls the currently selected device. 

Proceed as follows.

1. Connect both E1s to your computer, and make sure that both devices have separate names, e.g. `Electra Controller A`  and `Electra Controller B` (on the Mac, use ```Audio MIDI Setup``` for this).
2. Create a separate folder `ElectraOneMixer` in your local Ableton MIDI Live Scripts folder (see [installation instructions](#Installation) above), and copy all `.py` files in the `ElectraOne` folder to this new folder.
3. In Ableton, set up the remote script twice. Once using `ElectraOne` with input port and the output port ```Electra Controller A```, and using `ElectraOneMixer` with input port and the output port ```Electra Controller  B``` (if you used the names suggested in step 1). For all ports, tick the *Remote* boxes in the MIDI Ports table below, and untick the *Track* boxes.
3. For `ElectraOne` set `CONTROL_MODE = CONTROL_EFFECT_ONLY` in `config.py`. If you use SendMIDI (see above), make sure that your correctly set `E1_PORT_NAME` e.g. `E1_PORT_NAME = 'Electra Controller A Electra Port 1'`.
4. For `ElectraOneMixer` set `CONTROL_MODE = CONTROL_MIXER_ONLY` and `SENDMIDI_CMD = None` in `config.py`.
5. Restart Ableton.


