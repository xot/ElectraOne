time = controls.get(2)
sync = controls.get(4)

sync:setSlot(4,1)

function dosync(valueObject, value)
    time:setVisible(value == 0)
    sync:setVisible(value ~= 0)    
end

