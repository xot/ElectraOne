time  = controls.get(1)
sync  = controls.get(3)

time:setSlot(5,1)

function mode(valueObject, value)
    time:setVisible(value==0)
    sync:setVisible(value~=0)
end
