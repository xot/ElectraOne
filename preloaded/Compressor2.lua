ratio = controls.get(12)
xratio = controls.get(6)

function model(valueObject, value)
    if value == 0.0 then
        ratio:setVisible(true)
        xratio:setVisible(false)
    elseif value == 1.0 then
        ratio:setVisible(true)
        xratio:setVisible(false)
    else
        ratio:setVisible(false)
        xratio:setVisible(true)
    end
end

scison = false

sclisten = controls.get(20)
scgain = controls.get(19)
scmix = controls.get(21)

function setscvisibility()
    sclisten:setVisible(scison)
    scgain:setVisible(scison)
    scmix:setVisible(scison)
end

function scon(valueObject, value)
    scison = (value ~= 0)
    setscvisibility()
end

sceqison = false
eqisshelf = true

eqtp = controls.get(18)
eqfreq = controls.get(14)
eqgain = controls.get(15)
eqq = controls.get(17)

function seteqvisibility()
   eqtp:setVisible(sceqison)
   eqfreq:setVisible(sceqison)   
   eqgain:setVisible(sceqison and eqisshelf)
   eqq:setVisible(sceqison and (not eqisshelf))
end

function sceqon(valueObject, value)
    sceqison = (value ~= 0)
    seteqvisibility()
end

function eqtype(valueObject, value)
    eqisshelf = (value < 3)
    seteqvisibility()
end

release = controls.get(13)

function autorelease(valueObject, value)
    if (value == 0) then
       release:setVisible(true)
    else
       release:setVisible(false)
    end
end