acoarse = controls.get(1)
afine = controls.get(2)
afreq = controls.get(3)
amulti = controls.get(4)

afreq:setSlot(1,1)
amulti:setSlot(2,1)

function afixed(valueObject, value)
    acoarse:setVisible(value == 0)
    afine:setVisible(value == 0)
    afreq:setVisible(value ~= 0)
    amulti:setVisible(value ~= 0)
end

bcoarse = controls.get(19)
bfine = controls.get(20)
bfreq = controls.get(21)
bmulti = controls.get(22)

bfreq:setSlot(19,1)
bmulti:setSlot(20,1)

function bfixed(valueObject, value)
    bcoarse:setVisible(value == 0)
    bfine:setVisible(value == 0)
    bfreq:setVisible(value ~= 0)
    bmulti:setVisible(value ~=0)
end

ccoarse = controls.get(36)
cfine = controls.get(37)
cfreq = controls.get(38)
cmulti = controls.get(39)

cfreq:setSlot(1,2)
cmulti:setSlot(2,2)

function cfixed(valueObject, value)
    ccoarse:setVisible(value == 0)
    cfine:setVisible(value == 0)
    cfreq:setVisible(value ~= 0)
    cmulti:setVisible(value ~= 0)
end

dcoarse = controls.get(53)
dfine = controls.get(54)
dfreq = controls.get(55)
dmulti = controls.get(56)

dfreq:setSlot(19,2)
dmulti:setSlot(20,2)

function dfixed(valueObject, value)
    dcoarse:setVisible(value == 0)
    dfine:setVisible(value == 0)
    dfreq:setVisible(value ~= 0)
    dmulti:setVisible(value ~= 0)
end

-- retrig/loop visibility

aeretrig = controls.get(16)
aeloop = controls.get(11)

aeloop:setSlot(14,1)

function aemode(valueObject, value)
    aeretrig:setVisible((value == 2) or (value == 3))
    aeloop:setVisible(value == 1)
end

beretrig = controls.get(34)
beloop = controls.get(29)

beloop:setSlot(32,1)

function bemode(valueObject, value)
    beretrig:setVisible((value == 2) or (value == 3))
    beloop:setVisible(value == 1)
end

ceretrig = controls.get(51)
celoop = controls.get(46)

celoop:setSlot(14,2)

function cemode(valueObject, value)
    ceretrig:setVisible((value == 2) or (value == 3))
    celoop:setVisible(value == 1)
end

deretrig = controls.get(68)
deloop = controls.get(63)

deloop:setSlot(32,2)

function demode(valueObject, value)
    deretrig:setVisible((value == 2) or (value == 3))
    deloop:setVisible(value == 1)
end

-- phase/feedback visibility

aphase = controls.get(131)

function aretrig(valueObject, value)
    aphase:setVisible(value ~= 0)
end

bphase = controls.get(141)

function bretrig(valueObject, value)
    bphase:setVisible(value ~= 0)
end

cphase = controls.get(151)

function cretrig(valueObject, value)
    cphase:setVisible(value ~= 0)
end

dphase = controls.get(161)

function dretrig(valueObject, value)
    dphase:setVisible(value ~= 0)
end

-- lfo

lforate = controls.get(109)
lfosync = controls.get(111)

lfosync:setSlot(5,3)

function lforange(valueObject, value)
    lforate:setVisible(value ~= 2)
    lfosync:setVisible(value == 2)
end

lerepeat = controls.get(122)
leloop = controls.get(117)

leloop:setSlot(14,3)

function lemode(valueObject, value)
    lerepeat:setVisible((value == 2) or (value == 3))
    leloop:setVisible(value == 1)
end

-- filter 

ferepeat = controls.get(84)
feloop = controls.get(78)

feloop:setSlot(26,4)

function femode(valueObject, value)
    ferepeat:setVisible((value == 2) or (value == 3))
    feloop:setVisible(value == 1)
end

fdrive = controls.get(91)
fmorph = controls.get(93)

fmorph:setSlot(17,4)

fcrctbp = controls.get(89)
fcrctlp = controls.get(90)

fcrctlp:setSlot(8,4)

function ftype(valueObject, value)
    fcrctlp:setVisible(value < 2)
    fcrctbp:setVisible(value > 1)    
    fdrive:setVisible(value ~= 4)
    fmorph:setVisible(value == 4)
end

-- pitch

perepeat = controls.get(185)
peloop = controls.get(178)

peloop:setSlot(26,5)

function pemode(valueObject, value)
    perepeat:setVisible((value == 2) or (value == 3))
    peloop:setVisible(value == 1)
end
