release = controls.get(6)
decay = controls.get(2)
keyscale = controls.get(1)

function mode(valueObject, value)
    release:setVisible(value ~= 0)
    decay:setVisible(value ~= 0)
    keyscale:setVisible(value ~= 0)   
end

timelength = controls.get(9)
synclength = controls.get(8)

synclength:setSlot(9,1)

function sync(valueObject, value)
    timelength:setVisible(value == 0)
    synclength:setVisible(value ~= 0)
end
