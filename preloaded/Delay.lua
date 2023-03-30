ltime = controls.get(14)
rtime = controls.get(21)
l16th = controls.get(11)
r16th = controls.get(18)

rs = controls.get(20)

loffset = controls.get(12)
roffset = controls.get(19)

islsync = false
isrsync = false
islinked = false

function setvisibility()
    ltime:setVisible(not islsync)
    l16th:setVisible(islsync)
    loffset:setVisible(islsync)
    rtime:setVisible(not islinked and not isrsync)
    r16th:setVisible(not islinked and isrsync)
    roffset:setVisible(not islinked and isrsync)
    rs:setVisible(not islinked)
end

function lsync(valueObject, value)
    islsync = (value ~= 0)
    setvisibility()
end

function rsync(valueObject, value)
    isrsync = (value ~= 0)
    setvisibility()
end

function lrlink(valueObject, value)
    islinked = (value ~= 0)
    setvisibility()
end
