mfreq = controls.get(16)
mrate = controls.get(19)

mrate:setSlot(3,1)

function modsync(valueObject, value)
    mfreq:setVisible(value == 0)
    mrate:setVisible(value ~= 0)
end

spin = controls.get(28)
phase = controls.get(18)

spin:setSlot(22,1)

function spinsync(valueObject, value)
    phase:setVisible(value == 0)
    spin:setVisible(value ~= 0)
end

mfreq2 = controls.get(17)
mrate2 = controls.get(20)

mfreq2:setSlot(11,1)

function modsync2(valueObject, value)
    mfreq2:setVisible(value == 0)
    mrate2:setVisible(value ~= 0)
end

notches = controls.get(24)
center = controls.get(2)
spread = controls.get(30)
blend = controls.get(15)
flangetime = controls.get(13)
doublertime = controls.get(4)

flangetime:setSlot(1,1)
doublertime:setSlot(2,1)

function phasermode(valueObject, value)
    notches:setVisible(value == 0)
    center:setVisible(value == 0)
    spread:setVisible(value == 0)
    blend:setVisible(value == 0)
    flangetime:setVisible(value == 1)
    doublertime:setVisible(value == 2)
end

