rate1 = controls.get(55)
freq1 = controls.get(54)

freq1:setSlot(2,2)

function dosync1(valueObject, value)
    rate1:setVisible(value~=0)
    freq1:setVisible(value==0)
end

rate2 = controls.get(61)
freq2 = controls.get(60)

freq2:setSlot(14,2)

function dosync2(valueObject, value)
    rate2:setVisible(value~=0)
    freq2:setVisible(value==0)
end
