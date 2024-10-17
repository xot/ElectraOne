freq = controls.get(54)
sync = controls.get(56)

sync:setSlot(9,1)

function dosync(valueObject, value)
    freq:setVisible(value == 0)
    sync:setVisible(value ~= 0)    
end

filter = controls.get(20)
ladder = controls.get(29)

ladder:setSlot(6,1)

function doladder(valueObject, value)
    filter:setVisible(value == 0)
    ladder:setVisible(value ~= 0)    
end