rmodesel = controls.get(22)
xfadesel = controls.get(17)
sens = controls.get(24)
xfadeperct = controls.get(27)
intervaltime = controls.get(23)
intervalsync = controls.get(25)
intervalmode = controls.get(26)
fadein = controls.get(15)
fadeout = controls.get(16)

isretrigger = false
isrsync = false
isisync = false
isxfade = true

function setvisibility()
    rmodesel:setVisible(isretrigger)
    xfadesel:setVisible(isretrigger)    
    sens:setVisible(isretrigger and (not isrsync))
    xfadeperct:setVisible(isretrigger and isxfade and isrsync)
    intervaltime:setVisible(isretrigger and isrsync and (not isisync))
    intervalsync:setVisible(isretrigger and isrsync and isisync)
    intervalmode:setVisible(isretrigger and isrsync)
    fadein:setVisible(isretrigger and ((not isrsync) or (not isxfade)))
    fadeout:setVisible(isretrigger and (not isxfade))
end

function mrmode(valueObject, value)
    isretrigger = (value ~= 0)
    setvisibility()
end

function rmode(valueObject, value)
    isrsync = (value ~= 0)
    setvisibility()
end

function isync(valueObject, value)
    isisync = (value ~= 0)
    setvisibility()
end

function xfade(valueObject, value)
    isxfade = (value == 0)
    setvisibility()
end

time = controls.get(11)
div = controls.get(10)
s16th = controls.get(12)


function tmode(valueObject, value)
    if value == 0.0 then
        time:setVisible(true)
        div:setVisible(false)
        s16th:setVisible(false)
    elseif value == 1.0 then 
        time:setVisible(false)
        div:setVisible(true)
        s16th:setVisible(false)
    else
       time:setVisible(false)
        div:setVisible(false)
        s16th:setVisible(true)
    end
end
