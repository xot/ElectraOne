filter1morph = controls.get(24)
filter1peak = controls.get(26)

filter2morph = controls.get(31)
filter2peak = controls.get(33)

filter3morph = controls.get(38)
filter3peak = controls.get(40)

filter1morph:setSlot(12,2)
filter2morph:setSlot(24,2)
filter3morph:setSlot(36,2)

function filter1type(valueObject, value)
    filter1morph:setVisible(value == 5)
    filter1peak:setVisible(value == 4)    
end

function filter2type(valueObject, value)
    filter2morph:setVisible(value == 5)
    filter2peak:setVisible(value == 4)    
end

function filter3type(valueObject, value)
    filter3morph:setVisible(value == 5)
    filter3peak:setVisible(value == 4)    
end

lfo116th = controls.get(45)
lfo1rate = controls.get(47)
lfo1synced = controls.get(50)

lfo216th = controls.get(52)
lfo2rate = controls.get(54)
lfo2synced = controls.get(57)

lfo1rate:setSlot(3,3)
lfo1synced:setSlot(3,3)
lfo2rate:setSlot(9,3)
lfo2synced:setSlot(9,3)

function lfo1mode(valueObject, value)
    lfo116th:setVisible(value == 4)
    lfo1rate:setVisible(value == 0)
    lfo1synced:setVisible((value > 0) and (value < 4))
end

function lfo2mode(valueObject, value)
    lfo216th:setVisible(value == 4)
    lfo2rate:setVisible(value == 0)
    lfo2synced:setVisible((value > 0) and (value < 4))
end

noise16th = controls.get(61)
noiserate = controls.get(62)
noisesynced = controls.get(65)

noiserate:setSlot(21,3)
noisesynced:setSlot(21,3)

function noisemode(valueObject, value)
    noise16th:setVisible(value == 4)
    noiserate:setVisible(value == 0)
    noisesynced:setVisible((value > 0) and (value < 4))
end

fbsynced = controls.get(19)
fbtime = controls.get(20)
fbnote = controls.get(18)

fbnote:setSlot(11,4)
fbsynced:setSlot(11,4)

function fbmode(valueObject, value)
    fbtime:setVisible(value == 0)
    fbnote:setVisible(value == 4)
    fbsynced:setVisible((value > 0) and (value < 4))
end