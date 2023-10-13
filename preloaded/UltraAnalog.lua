rate1 = controls.get(101)
freq1 = controls.get(102)

rate1:setSlot(3,5)

rate2 = controls.get(111)
freq2 = controls.get(112)

rate2:setSlot(15,5)

function sync1(valueObject, value)
    freq1:setVisible(value == 0)
    rate1:setVisible(value ~= 0)
end

function sync2(valueObject, value)
    freq2:setVisible(value == 0)
    rate2:setVisible(value ~= 0)
end
