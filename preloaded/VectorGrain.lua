filter = controls.get(22)
ladder = controls.get(36)

ladder:setSlot(6,2)

function doladder(valueObject, value)
    filter:setVisible(value == 0)
    ladder:setVisible(value ~= 0)    
end

free = controls.get(65)
sync = controls.get(66)

free:setSlot(8,2)

function dosync(valueObject, value)
    free:setVisible(value == 0)
    sync:setVisible(value ~= 0)    
end

