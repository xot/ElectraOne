freq1 = controls.get(99)
sync1 = controls.get(100)

freq1:setSlot(2,3)

function dosync1(valueObject, value)
    freq1:setVisible(value == 0)
    sync1:setVisible(value ~= 0)
end

freq2 = controls.get(105)
sync2 = controls.get(106)

freq2:setSlot(8,3)

function dosync2(valueObject, value)
    freq2:setVisible(value == 0)
    sync2:setVisible(value ~= 0)
end

aamount1 = controls.get(17)
aamount2 = controls.get(18)
aamount3 = controls.get(14)
aamount4 = controls.get(15)
aamount5 = controls.get(21)
aamount6 = controls.get(16)
aamount7 = controls.get(13)
aamount8 = controls.get(20)
aamount9 = controls.get(19)

function doadest1(valueObject, value)
    aamount1:setVisible(value ~= 0)
end

function doadest2(valueObject, value)
    aamount2:setVisible(value ~= 0)
end

function doadest3(valueObject, value)
    aamount3:setVisible(value ~= 0)
end

function doadest4(valueObject, value)
    aamount4:setVisible(value ~= 0)
end

function doadest5(valueObject, value)
    aamount5:setVisible(value ~= 0)
end

function doadest6(valueObject, value)
    aamount6:setVisible(value ~= 0)
end

function doadest7(valueObject, value)
    aamount7:setVisible(value ~= 0)
end

function doadest8(valueObject, value)
    aamount8:setVisible(value ~= 0)
end

function doadest9(valueObject, value)
    aamount9:setVisible(value ~= 0)
end

bamount1 = controls.get(35)
bamount2 = controls.get(36)
bamount3 = controls.get(32)
bamount4 = controls.get(33)
bamount5 = controls.get(39)
bamount6 = controls.get(34)
bamount7 = controls.get(31)
bamount8 = controls.get(38)
bamount9 = controls.get(37)

function dobdest1(valueObject, value)
    bamount1:setVisible(value ~= 0)
end

function dobdest2(valueObject, value)
    bamount2:setVisible(value ~= 0)
end

function dobdest3(valueObject, value)
    bamount3:setVisible(value ~= 0)
end

function dobdest4(valueObject, value)
    bamount4:setVisible(value ~= 0)
end

function dobdest5(valueObject, value)
    bamount5:setVisible(value ~= 0)
end

function dobdest6(valueObject, value)
    bamount6:setVisible(value ~= 0)
end

function dobdest7(valueObject, value)
    bamount7:setVisible(value ~= 0)
end

function dobdest8(valueObject, value)
    bamount8:setVisible(value ~= 0)
end

function dobdest9(valueObject, value)
    bamount9:setVisible(value ~= 0)
end
