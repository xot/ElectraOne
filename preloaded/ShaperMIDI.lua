freq  = controls.get(10)
sync  = controls.get(11)

sync:setSlot(10,1)

function mode(valueObject, value)
    freq:setVisible(value==0)
    sync:setVisible(value~=0)
end
