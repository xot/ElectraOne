ltime = controls.get(25)
rtime = controls.get(44)
l16th = controls.get(20)
r16th = controls.get(39)
ldiv = controls.get(21)
rdiv = controls.get(40)

rs = controls.get(42)
lm =  controls.get(24)
rm = controls.get(43)

islsync = true
isl16th = false
isrsync = true
isr16th = false
islinked = false

function setvisibility()
    ltime:setVisible(not islsync)
    l16th:setVisible(islsync and isl16th)
    ldiv:setVisible(islsync and not isl16th)
    rtime:setVisible(not islinked and not isrsync)
    r16th:setVisible(not islinked and (isrsync and isr16th))
    rdiv:setVisible(not islinked and (isrsync and not isr16th))
    rs:setVisible(not islinked)
    rm:setVisible((not islinked) and isrsync)
    lm:setVisible(islsync)    
end

function lsync(valueObject, value)
    islsync = (value ~= 0)
    setvisibility()
end

function rsync(valueObject, value)
    isrsync = (value ~= 0)
    setvisibility()
end

function lmode(valueObject, value)
    isl16th = (value == 3.0)    
    setvisibility()
end

function rmode(valueObject, value)
    isr16th = (value == 3.0)    
    setvisibility()
end

function lrlink(valueObject, value)
    islinked = (value ~= 0)
    setvisibility()
end

modrate = controls.get(32)
modfreq = controls.get(30)

function modsync(valueObject, value)
    modfreq:setVisible(value == 0)
    modrate:setVisible(value ~= 0)
end

