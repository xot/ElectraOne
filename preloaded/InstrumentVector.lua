rate = controls.get(55)
sync = controls.get(57)

sync:setSlot(7,4)

function dosync(valueObject, value)
    rate:setVisible(value == 0)
    sync:setVisible(value ~= 0)
end

rate2 = controls.get(64)
sync2 = controls.get(66)

sync2:setSlot(19,4)

function dosync2(valueObject, value)
    rate2:setVisible(value == 0)
    sync2:setVisible(value ~= 0)    
end

bpcirc = controls.get(32)
lpcirc = controls.get(35)
drive = controls.get(33)
morphe = controls.get(36)

lpcirc:setSlot(4,2)
morphe:setSlot(9,2)

function dotype(valueObject, value)
    bpcirc:setVisible(value > 1)
    lpcirc:setVisible(value <= 1)
    drive:setVisible(value ~= 4)
    morphe:setVisible(value == 4)
end

bpcirc2 = controls.get(41)
lpcirc2 = controls.get(44)
drive2 = controls.get(42)
morphe2 = controls.get(45)

lpcirc2:setSlot(16,2)
morphe2:setSlot(21,2)
function dotype2(valueObject, value)
    bpcirc2:setVisible(value > 1)
    lpcirc2:setVisible(value <= 1)
    drive2:setVisible(value ~= 4)
    morphe2:setVisible(value == 4)   
end
