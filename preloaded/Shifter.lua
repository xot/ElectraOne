mode = 0
delaysync = 0
lfosync = 0
spin = 0
wave = 0

pcoarse = controls.get(1)
fcoarse = controls.get(3)
rcoarse = controls.get(5)

pwindow = controls.get(27)

pfine = controls.get(2)
mfine = controls.get(4)

lfoamounthz = controls.get(22)
lfoamountst = controls.get(25)

lfofreq = controls.get(21)
lforate = controls.get(24)
lfooffset = controls.get(17)

lfophase = controls.get(14)
lfosetspin = controls.get(18)
lfospin = controls.get(19)

lfowidth = controls.get(16)
lfoduty = controls.get(15)

envamounthz = controls.get(12)
envamountst = controls.get(11)

dtime = controls.get(31)
dsync = controls.get(32)

function setvisibility()
    pcoarse:setVisible(mode == 0)
    fcoarse:setVisible(mode == 1)
    rcoarse:setVisible(mode == 2)
    pwindow:setVisible(mode == 0)
    pfine:setVisible(mode == 0)
    mfine:setVisible(mode ~= 0)
    lfoamounthz:setVisible(mode ~= 0)
    lfoamountst:setVisible(mode == 0)
    envamounthz:setVisible(mode ~= 0)
    envamountst:setVisible(mode == 0)
    dtime:setVisible(delaysync == 0)
    dsync:setVisible(delaysync ~= 0)
    lfofreq:setVisible(lfosync == 0)
    lforate:setVisible(lfosync ~= 0)
    lfooffset:setVisible(lfosync ~= 0)
    lfosetspin:setVisible((lfosync == 0) and (wave < 8))
    lfophase:setVisible((wave == 8) or ((wave < 8) and ((lfosync ~= 0) or (spin == 0))))
    lfospin:setVisible((wave < 8 ) and (lfosync == 0) and (spin ~= 0))
    lfowidth:setVisible(wave == 9)
    lfoduty:setVisible(wave < 8)
end

function setwave(valueObject, value)
    wave = value
    setvisibility()
end

function setmode(valueObject, value)
    mode = value
    setvisibility()
end

function setdelaysync(valueObject, value)
    delaysync = value
    setvisibility()
end

function setspin(valueObject, value)
    spin = value
    setvisibility()
end

function setlfosync(valueObject, value)
    lfosync = value
    setvisibility()
end
