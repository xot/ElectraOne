mfreq = controls.get(16)
mrate = controls.get(19)

function modsync(valueObject, value)
    if value == 0 then
        mfreq:setVisible(true)
        mrate:setVisible(false)
	    return("Mod Sync")
    else
        mfreq:setVisible(false)
        mrate:setVisible(true)
	    return("Mod Sync")
    end
end

spin = controls.get(28)
phase = controls.get(18)

function spinsync(valueObject, value)
    if value == 0 then
        phase:setVisible(true)
        spin:setVisible(false)
	    return("Phase/Spin")
    else
        phase:setVisible(false)
        spin:setVisible(true)
	    return("Phase/Spin")
    end
end

mfreq2 = controls.get(17)
mrate2 = controls.get(20)

function modsync2(valueObject, value)
    if value == 0 then
        mfreq2:setVisible(true)
        mrate2:setVisible(false)
	    return("Mod Sync")
    else
        mfreq2:setVisible(false)
        mrate2:setVisible(true)
	    return("Mod Sync")
    end
end
