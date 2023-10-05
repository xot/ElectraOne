ltime = controls.get(10)
lbeat = controls.get(1)
lswing = controls.get(2)

lrtime = controls.get(21)
lrbeat = controls.get(12)
lrswing = controls.get(13)

rtime = controls.get(32)
rbeat = controls.get(23)
rswing = controls.get(24)

ltime:setSlot(3,1)
lrtime:setSlot(15,1)
rtime:setSlot(27,1)

islsync = false
islrsync = false
isrsync = false

function setvisibility()
   ltime:setVisible(not islsync)
   lbeat:setVisible(islsync)
   lswing:setVisible(islsync)
   lrtime:setVisible(not islrsync)
   lrbeat:setVisible(islrsync)
   lrswing:setVisible(islrsync)
   rtime:setVisible(not isrsync)
   rbeat:setVisible(isrsync)
   rswing:setVisible(isrsync)
end

function lsync(valueObject, value)
    islsync = (value ~= 0)
    setvisibility()
end

function lrsync(valueObject, value)
    islrsync = (value ~= 0)
    setvisibility()
end

function rsync(valueObject, value)
    isrsync = (value ~= 0)
    setvisibility()
end
