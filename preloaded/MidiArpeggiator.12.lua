freq = controls.get(2)
rate = controls.get(12)

rate:setSlot(4,1)

function sync(valueObject, value)
    freq:setVisible(value == 0)
    rate:setVisible(value ~= 0)
end
