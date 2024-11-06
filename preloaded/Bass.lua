freq = controls.get(19)
sync = controls.get(32)

sync:setSlot(14,2)

function dosync(valueObject, value)
    freq:setVisible(value == 0)
    sync:setVisible(value ~= 0)
end