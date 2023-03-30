width = controls.get(13)
spin = controls.get(9)
phase = controls.get(7)
freq = controls.get(3)
rate = controls.get(11)
offset = controls.get(6)
modebutton = controls.get(10)

israndom = false
isphase = true
issync = false

function setvisibility()
    width:setVisible(israndom)
    spin:setVisible((not israndom) and (not isphase) and (not issync))
    phase:setVisible((not israndom) and (isphase or issync))
    freq:setVisible(not issync)
    rate:setVisible(issync)
    offset:setVisible(issync)
    modebutton:setVisible((not issync) and (not israndom))
end

function mode(valueObject, value)
    isphase = (value == 0)
    setvisibility()
end

function wave(valueObject, value)
   israndom = (value == 3.0)  
   setvisibility()
end

function lfotype(valueObject, value)
    issync = (value ~= 0)
    setvisibility()
end


