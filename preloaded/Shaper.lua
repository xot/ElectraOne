sync = controls.get(9)
freq = controls.get(8)
manual = controls.get(5)
trigger = controls.get(14)

sync:setSlot(11,1)
manual:setSlot(11,1)

tmode = 0
smode = false

function syncmode(valueObject, value)
    smode = (value == 0)
    setvisibility()
end

function triggermode(valueObject, value)
    tmode = value
    setvisibility()
end

function setvisibility()
    sync:setVisible(smode and (tmode ~= 2))
    freq:setVisible(not smode and (tmode ~= 2))
    manual:setVisible((tmode == 2))
    trigger:setVisible((tmode == 1))
end