# ElectrOne - Device definitions
#
# Ableton Live MIDI Remote Script for the Electra One
#
# Author: Jaap-henk Hoepman (info@xot.nl)
#
# Distributed under the MIT License, see LICENSE
#

# Dictionary with preset and MIDI cc mapping data for known devices
# (indexed by device.original_name)
# - The preset is a JSON string in Electra One format.
#   (The current implementation assumes that all quantized parameters
#   are 7-bit absolute CC values while all non quantized parameters are
#   14-bit absolute values)
# - The MIDI cc mapping data is a dictionary of Ableton Live original parameter
#   names with their corresponding MIDI CC values in the preset.
#

from .ElectraOneDumper import PatchInfo

DEVICES = {
    'Looper' :
        PatchInfo( '{"version":2,"name":"Looper","projectId":"rPoZxhbryg2gniEI7viF","pages":[{"id":1,"name":"Page 1"}],"groups":[],"devices":[{"id":1,"name":"Generic MIDI","port":1,"channel":11}],"overlays":[{"id":1,"items":[{"label":"Stop","index":0,"value":0},{"label":"Record","index":1,"value":42},{"label":"Play","index":2,"value":85},{"label":"Overdub","index":3,"value":127}]},{"id":2,"items":[{"label":"None","index":0,"value":0},{"label":"Start Song","index":1,"value":64},{"label":"Start & Stop Song","index":2,"value":127}]},{"id":3,"items":[{"label":"Global","index":0,"value":0},{"label":"None","index":1,"value":9},{"label":"8 Bars","index":2,"value":18},{"label":"4 Bars","index":3,"value":27},{"label":"2 Bars","index":4,"value":36},{"label":"1 Bar","index":5,"value":45},{"label":"1/2","index":6,"value":54},{"label":"1/2T","index":7,"value":64},{"label":"1/4","index":8,"value":73},{"label":"1/4T","index":9,"value":82},{"label":"1/8","index":10,"value":91},{"label":"1/8T","index":11,"value":100},{"label":"1/16","index":12,"value":109},{"label":"1/16T","index":13,"value":118},{"label":"1/32","index":14,"value":127}]},{"id":4,"items":[{"label":"None","index":0,"value":0},{"label":"Follow song tempo","index":1,"value":64},{"label":"Set & Follow song tempo","index":2,"value":127}]},{"id":5,"items":[{"label":"Always","index":0,"value":0},{"label":"Never","index":1,"value":42},{"label":"Rec/OVR","index":2,"value":85},{"label":"Rec/OVR/Stop","index":3,"value":127}]}],"controls":[{"id":1,"type":"list","visible":true,"name":" STATE ","color":"FFFFFF","bounds":[0,40,146,56],"pageId":1,"controlSetId":1,"inputs":[{"potId":1,"valueId":"value"}],"values":[{"id":"value","message":{"type":"cc7","deviceId":1,"parameterNumber":2},"overlayId":1}]},{"id":2,"type":"list","visible":true,"name":" SONG CONTROL ","color":"529DEC","bounds":[170,40,146,56],"pageId":1,"controlSetId":1,"inputs":[{"potId":2,"valueId":"value"}],"values":[{"id":"value","message":{"type":"cc7","deviceId":1,"parameterNumber":8},"overlayId":2}]},{"id":3,"type":"fader","visible":true,"name":" SPEED ","color":"C44795","bounds":[340,40,146,56],"pageId":1,"controlSetId":1,"inputs":[{"potId":3,"valueId":"value"}],"values":[{"id":"value","message":{"type":"cc14","deviceId":1,"lsbFirst":false,"parameterNumber":6,"min":0,"max":16383}}]},{"id":4,"type":"fader","visible":true,"name":" FEEDBACK ","color":"03A598","bounds":[510,40,146,56],"pageId":1,"controlSetId":1,"inputs":[{"potId":4,"valueId":"value"}],"values":[{"id":"value","message":{"type":"cc14","deviceId":1,"lsbFirst":false,"parameterNumber":3,"min":0,"max":16383}}]},{"id":7,"type":"list","visible":true,"name":" QUANTIZATION ","color":"FFFFFF","bounds":[0,128,146,56],"pageId":1,"controlSetId":1,"inputs":[{"potId":7,"valueId":"value"}],"values":[{"id":"value","message":{"type":"cc7","deviceId":1,"parameterNumber":7},"overlayId":3}]},{"id":8,"type":"list","visible":true,"name":" TEMPO CONTROL ","color":"529DEC","bounds":[170,128,146,56],"pageId":1,"controlSetId":1,"inputs":[{"potId":8,"valueId":"value"}],"values":[{"id":"value","message":{"type":"cc7","deviceId":1,"parameterNumber":9},"overlayId":4}]},{"id":9,"type":"pad","mode":"toggle","visible":true,"name":" REVERSE ","color":"C44795","bounds":[340,128,146,56],"pageId":1,"controlSetId":1,"inputs":[{"potId":9,"valueId":"value"}],"values":[{"id":"value","message":{"type":"cc7","deviceId":1,"parameterNumber":4,"onValue":127,"offValue":0},"defaultValue":"off"}]},{"id":10,"type":"list","visible":true,"name":" MONITOR ","color":"03A598","bounds":[510,128,146,56],"pageId":1,"controlSetId":1,"inputs":[{"potId":10,"valueId":"value"}],"values":[{"id":"value","message":{"type":"cc7","deviceId":1,"parameterNumber":5},"overlayId":5}]},{"id":13,"type":"pad","mode":"toggle","visible":true,"name":" DEVICE ON ","color":"FFFFFF","bounds":[0,216,146,56],"pageId":1,"controlSetId":2,"inputs":[{"potId":1,"valueId":"value"}],"values":[{"id":"value","message":{"type":"cc7","deviceId":1,"parameterNumber":1,"onValue":127,"offValue":0},"defaultValue":"off"}]}]}'
                  ,  {'Device On': 1,'State': 2,'Feedback': 3,'Reverse': 4,'Monitor': 5,'Speed': 6,'Quantization': 7,'Song Control': 8,'Tempo Control': 9}
                  )
    ,
    'Echo' :
       PatchInfo( ''
                , {'Device On': 1
,'L Sync': 2
,'L Time': 3
,'L Division': 3
,'L 16th': 3
,'L Sync Mode': 6
,'L Offset': 7
,'R Time': 8
,'R Sync': 9
,'R Division': 8
,'R 16th': 8
,'R Sync Mode': 12
,'R Offset': 13
,'Link': 14
,'Repitch': 15
,'Feedback': 16
,'Feedback Inv': 17
,'Channel Mode': 18
,'Input Gain': 19
,'Output Gain': 20
,'Clip Dry': 21
,'Gate On': 22
,'Gate Thr': 23
,'Gate Release': 24
,'Duck On': 25
,'Duck Thr': 26
,'Duck Release': 27
,'Filter On': 28
,'HP Freq': 29
,'HP Res': 30
,'LP Freq': 31
,'LP Res': 32
,'Mod Wave': 33
,'Mod Freq': 34
,'Mod Sync': 35
,'Mod Rate': 34
,'Mod Phase': 37
,'Env Mix': 38
,'Dly < Mod': 39
,'Flt < Mod': 40
,'Mod 4x': 41
,'Reverb Level': 42
,'Reverb Decay': 43
,'Reverb Loc': 44
,'Noise On': 45
,'Noise Amt': 46
,'Noise Mrph': 47
,'Wobble On': 48
,'Wobble Amt': 49
,'Wobble Mrph': 50
,'Stereo Width': 51
,'Dry Wet': 52
}
)}

# Return the predefined patch information for a device, None if it doesn't exist
def get_predefined_patch_info(device_original_name):
    # FIXME: try to read from file
    if device_original_name in DEVICES:
        return DEVICES[device_original_name]
    else:
        return None

        
