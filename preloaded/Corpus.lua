tune = controls.get(37)
fine = controls.get(7)
transpose = controls.get(36)
midimode  = controls.get(21)
pbrange  = controls.get(28)

function midifreq(valueObject, value)
    tune:setVisible(value == 0)
    fine:setVisible(value ~= 0)	
    transpose:setVisible(value ~= 0)
    midimode:setVisible(value ~= 0)
    pbrange:setVisible(value ~= 0)
end

material = controls.get(22)
radius = controls.get(30)
opening = controls.get(27)
inharmonics = controls.get(10)
bright = controls.get(2)
ratio = controls.get(31)
hit = controls.get(9)
posl = controls.get(18)
posr = controls.get(19)

function settype(valueObject, value)
    material:setVisible(value < 5)
    inharmonics:setVisible(value < 5)
    radius:setVisible(value > 4)
    opening:setVisible(value == 5)
    bright:setVisible(value < 5)
    ratio:setVisible((value == 3) or (value == 4))
    hit:setVisible(value < 5)
    posl:setVisible(value < 5)
    posr:setVisible(value < 5)
end

decay = controls.get(25)

function setoffdecay(valueObject, value)
    decay:setVisible(value ~= 0)
end


lfoamount = controls.get(11)
lfoshape = controls.get(14)
lfooffset = controls.get(26)

lfosync = controls.get(16)

lforate = controls.get(17)
lfofreq = controls.get(13)

lfomod = controls.get(15)

phase = controls.get(29)
spin = controls.get(34)

lfoison = false
lfoissync = false
lfoisspin = false

function setlfovisibility()
    lfoamount:setVisible(lfoison)
    lfoshape:setVisible(lfoison)
    lfosync:setVisible(lfoison)
    lfomod:setVisible(lfoison and (not lfoissync))
    lfooffset:setVisible(lfoison and lfoissync)
    phase:setVisible(lfoison and (lfoissync or (not lofisspin)))
    spin:setVisible(lfoison and (not lfoissync) and lfoisspin)
    lfofreq:setVisible(lfoison and (not lfoissync))
    lforate:setVisible(lfoison and lfoissync)
end

function setlfo(valueObject, value)
    lfoison = (value ~= 0)
    setlfovisibility()
end

function mod(valueObject, value)
    lfoisspin = (value ~= 0)
    setlfovisibility()
end

function sync(valueObject, value)
    lfoissync = (value ~= 0)
    setlfovisibility()
end


midfreq = controls.get(23)

function setfilter(valueObject, value)
    midfreq:setVisible(value ~= 0)
end
