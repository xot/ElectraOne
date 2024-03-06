release = controls.get(6)
decay = controls.get(2)
keyscale = controls.get(1)
timelength = controls.get(9)
synclength = controls.get(8)
gate = controls.get(4)

synclength:setSlot(9,1)

modestate = false
syncstate = false
latchstate = false

function mode(valueObject, value)
    modestate = (value ~= 0)
    setvisibility()
end

function sync(valueObject, value)
    syncstate = (value ~= 0)
    setvisibility()
end

function latch(valueObject, value)
    latchstate = (value ~= 0)
    setvisibility()
end

function setvisibility()
    release:setVisible(not latchstate and not modestate)
    decay:setVisible(not latchstate and not modestate)
    keyscale:setVisible(not latchstate and not modestate)  
    gate:setVisible(not latchstate)
    timelength:setVisible(not latchstate and not syncstate)  
    synclength:setVisible(not latchstate and syncstate)
end
