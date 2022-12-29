pcoarse = controls.get(1)
fcoarse = controls.get(3)
rcoarse = controls.get(5)

pwindow = controls.get(27)

pfine = controls.get(2)
mfine = controls.get(4)

lfoamounthz = controls.get(22)
lfoamountst = controls.get(25)

envamounthz = controls.get(12)
envamountst = controls.get(11)

function mode(valueObject, value)
    if value == 0.0 then
        pcoarse:setVisible(true)
        fcoarse:setVisible(false)
        rcoarse:setVisible(false)
        pwindow:setVisible(true)
        pfine:setVisible(true)
        mfine:setVisible(false)
        lfoamounthz:setVisible(false)
        lfoamountst:setVisible(true)
        envamounthz:setVisible(false)
        envamountst:setVisible(true)
        return("Pitch")
    elseif value == 1.0 then
        pcoarse:setVisible(false)
        fcoarse:setVisible(true)
        rcoarse:setVisible(false)
        pwindow:setVisible(false)
        pfine:setVisible(false)
        mfine:setVisible(true)
        lfoamounthz:setVisible(true)
        lfoamountst:setVisible(false)
        envamounthz:setVisible(true)
        envamountst:setVisible(false)
        return("Freq")
    else
        pcoarse:setVisible(false)
        fcoarse:setVisible(false)
        rcoarse:setVisible(true)
        pwindow:setVisible(false)
        pfine:setVisible(false)
        mfine:setVisible(true)
        lfoamounthz:setVisible(true)
        lfoamountst:setVisible(false)
        envamounthz:setVisible(true)
        envamountst:setVisible(false)
        return("Ring")
    end
end

dtime = controls.get(31)
dsync = controls.get(32)

function delaysync(valueObject, value)
    if value == 0 then
        dtime:setVisible(true)
        dsync:setVisible(false)
	    return("Delay Sync")
    else
        dtime:setVisible(false)
        dsync:setVisible(true)
	    return("Delay Sync")
    end
end

lfofreq = controls.get(21)
lforate = controls.get(24)
lfooffset = controls.get(17)

function lfosync(valueObject, value)
    if value == 0 then
        lfofreq:setVisible(true)
        lforate:setVisible(false)
        lfooffset:setVisible(false)
	    return("LFO Sync")
    else
        lfofreq:setVisible(false)
        lforate:setVisible(true)
        lfooffset:setVisible(true)
	    return("LFO Sync")
    end
end
