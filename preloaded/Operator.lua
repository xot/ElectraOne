acoarse = controls.get(1)
afine = controls.get(2)
afreq = controls.get(3)
amulti = controls.get(4)

function afixed(valueObject, value)
    if value == 0 then
        acoarse:setVisible(true)
        afine:setVisible(true)
        afreq:setVisible(false)
        amulti:setVisible(false)
    else
        acoarse:setVisible(false)
        afine:setVisible(false)
        afreq:setVisible(true)
        amulti:setVisible(true)
    end
end

bcoarse = controls.get(19)
bfine = controls.get(20)
bfreq = controls.get(21)
bmulti = controls.get(22)

function bfixed(valueObject, value)
    if value == 0 then
        bcoarse:setVisible(true)
        bfine:setVisible(true)
        bfreq:setVisible(false)
        bmulti:setVisible(false)
    else
        bcoarse:setVisible(false)
        bfine:setVisible(false)
        bfreq:setVisible(true)
        bmulti:setVisible(true)
    end
end

ccoarse = controls.get(36)
cfine = controls.get(37)
cfreq = controls.get(38)
cmulti = controls.get(39)

function cfixed(valueObject, value)
    if value == 0 then
        ccoarse:setVisible(true)
        cfine:setVisible(true)
        cfreq:setVisible(false)
        cmulti:setVisible(false)
    else
        ccoarse:setVisible(false)
        cfine:setVisible(false)
        cfreq:setVisible(true)
        cmulti:setVisible(true)
    end
end

dcoarse = controls.get(53)
dfine = controls.get(54)
dfreq = controls.get(55)
dmulti = controls.get(56)

function dfixed(valueObject, value)
    if value == 0 then
        dcoarse:setVisible(true)
        dfine:setVisible(true)
        dfreq:setVisible(false)
        dmulti:setVisible(false)
    else
        dcoarse:setVisible(false)
        dfine:setVisible(false)
        dfreq:setVisible(true)
        dmulti:setVisible(true)
    end
end

-- retrig/loop visibility

aeretrig = controls.get(16)
aeloop = controls.get(11)

function aemode(valueObject, value)
    if value == 1 then
        aeretrig:setVisible(false)
        aeloop:setVisible(true)
    elseif (value == 2) or (value == 3) then
        aeretrig:setVisible(true)
        aeloop:setVisible(false)
    else
        aeretrig:setVisible(false)
        aeloop:setVisible(false)
    end
end

beretrig = controls.get(34)
beloop = controls.get(29)

function bemode(valueObject, value)
    if value == 1 then
        beretrig:setVisible(false)
        beloop:setVisible(true)
    elseif (value == 2) or (value == 3) then
        beretrig:setVisible(true)
        beloop:setVisible(false)
    else
        beretrig:setVisible(false)
        beloop:setVisible(false)
    end
end

ceretrig = controls.get(51)
celoop = controls.get(46)

function cemode(valueObject, value)
    if value == 1 then
        ceretrig:setVisible(false)
        celoop:setVisible(true)
    elseif (value == 2) or (value == 3) then
        ceretrig:setVisible(true)
        celoop:setVisible(false)
    else
        ceretrig:setVisible(false)
        celoop:setVisible(false)
    end
end

deretrig = controls.get(68)
deloop = controls.get(63)

function demode(valueObject, value)
    if value == 1 then
        deretrig:setVisible(false)
        deloop:setVisible(true)
    elseif (value == 2) or (value == 3) then
        deretrig:setVisible(true)
        deloop:setVisible(false)
    else
        deretrig:setVisible(false)
        deloop:setVisible(false)
    end
end

-- phase/feedback visibility

aphase = controls.get(131)
afeedback = controls.get(126)

function aretrig(valueObject, value)
    if value == 0 then
        aphase:setVisible(false)
	afeedback:setVisible(true)
    else
        aphase:setVisible(true)
	afeedback:setVisible(false)
    end
end

bphase = controls.get(141)
bfeedback = controls.get(136)

function bretrig(valueObject, value)
    if value == 0 then
        bphase:setVisible(false)
	bfeedback:setVisible(true)
    else
        bphase:setVisible(true)
	bfeedback:setVisible(false)
    end
end

cphase = controls.get(151)
cfeedback = controls.get(146)

function cretrig(valueObject, value)
    if value == 0 then
        cphase:setVisible(false)
	cfeedback:setVisible(true)
    else
        cphase:setVisible(true)
	cfeedback:setVisible(false)
    end
end

dphase = controls.get(161)
dfeedback = controls.get(156)

function dretrig(valueObject, value)
    if value == 0 then
        dphase:setVisible(false)
	dfeedback:setVisible(true)
    else
        dphase:setVisible(true)
	dfeedback:setVisible(false)
    end
end
