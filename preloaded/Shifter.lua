mode = 0
delaysync = 0
lfosync = 0
spin = 0
wave = 0
delayison = false
envison = false

pcoarse = controls.get(1)
fcoarse = controls.get(3)
rcoarse = controls.get(5)

fcoarse:setSlot(1,1)
rcoarse:setSlot(1,1)

pwindow = controls.get(27)

pfine = controls.get(2)
mfine = controls.get(4)

mfine:setSlot(2,1)

lfoamounthz = controls.get(22)
lfoamountst = controls.get(25)

lfoamountst:setSlot(22,1)

lfofreq = controls.get(21)
lforate = controls.get(24)
lfooffset = controls.get(17)

lforate:setSlot(21,1)

lfophase = controls.get(14)
lfosetspin = controls.get(18)
lfospin = controls.get(19)

lfospin:setSlot(15,1)

lfowidth = controls.get(16)
lfoduty = controls.get(15)

lfowidth:setSlot(4,1)

envamounthz = controls.get(12)
envamountst = controls.get(11)
envattack = controls.get(8)
envrelease = controls.get(9)

envamountst:setSlot(28,1)

dtime = controls.get(31)
dsync = controls.get(32)
dfeedback = controls.get(37)
dsetsync = controls.get(36)

dsync:setSlot(32,1)

function setvisibility()
    pcoarse:setVisible(mode == 0)
    fcoarse:setVisible(mode == 1)
    rcoarse:setVisible(mode == 2)
    pwindow:setVisible(mode == 0)
    pfine:setVisible(mode == 0)
    mfine:setVisible(mode ~= 0)
    lfoamounthz:setVisible(mode ~= 0)
    lfoamountst:setVisible(mode == 0)
    envamounthz:setVisible(envison and (mode ~= 0))
    envamountst:setVisible(envison and (mode == 0))
    envattack:setVisible(envison)
    envrelease:setVisible(envison)
    dtime:setVisible(delayison and (delaysync == 0))
    dsync:setVisible(delayison and (delaysync ~= 0))
    dfeedback:setVisible(delayison)
    dsetsync:setVisible(delayison)    
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

function delayon(valueObject, value)
    delayison = (value ~= 0 )
    setvisibility()
end

function envon(valueObject, value)
    envison = (value ~= 0)
    setvisibility()
end
