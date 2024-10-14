freq = controls.get(11)
sync = controls.get(12)

sync:setSlot(7,1)

function syncmode(valueObject, value)
    freq:setVisible(value==0)
    sync:setVisible(value~=0)
end

