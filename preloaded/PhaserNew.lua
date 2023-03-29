mfreq = controls.get(16)
mrate = controls.get(19)

function modsync(valueObject, value)
    if value == 0 then
        mfreq:setVisible(true)
        mrate:setVisible(false)
    else
        mfreq:setVisible(false)
        mrate:setVisible(true)
    end
end

spin = controls.get(28)
phase = controls.get(18)

function spinsync(valueObject, value)
    if value == 0 then
        phase:setVisible(true)
        spin:setVisible(false)
    else
        phase:setVisible(false)
        spin:setVisible(true)
    end
end

mfreq2 = controls.get(17)
mrate2 = controls.get(20)

function modsync2(valueObject, value)
    if value == 0 then
        mfreq2:setVisible(true)
        mrate2:setVisible(false)
    else
        mfreq2:setVisible(false)
        mrate2:setVisible(true)
    end
end

flangetime = controls.get(13)
doublertime = controls.get(4)

notches = controls.get(24)
center = controls.get(2)
spread = controls.get(30)
blend = controls.get(15)

function phvis(flag)
    notches:setVisible(flag)
    center:setVisible(flag)
    spread:setVisible(flag)
    blend:setVisible(flag)
end

function phasermode(valueObject, value)
    if value == 0 then
        phvis(true)
        flangetime:setVisible(false)
        doublertime:setVisible(false)
    elseif value == 1 then
        phvis(false)
        flangetime:setVisible(true)
        doublertime:setVisible(false)
    else
        phvis(false)
        flangetime:setVisible(false)
        doublertime:setVisible(true)
    end
end
