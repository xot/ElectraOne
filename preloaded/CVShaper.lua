sync = controls.get(11)
freq = controls.get(10)

freq:setSlot(4,1)

function syncmode(valueObject, value)
    sync:setVisible(value ~= 0)
    freq:setVisible(value == 0)
end
