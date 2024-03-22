freq = controls.get(7)
sync = controls.get(8)
x10 = controls.get(15)

sync:setSlot(7,1)


function mode(valueObject, value)
    freq:setVisible(value==0)
    x10:setVisible(value==0)
    sync:setVisible(value~=0)
end

