ltime = controls.get(14)
rtime = controls.get(21)
l16th = controls.get(11)
r16th = controls.get(18)

rs = controls.get(20)

loffset = controls.get(12)
roffset = controls.get(19)

rshowtime = false

function lsync(valueObject, value)
    if value == 0 then
        ltime:setVisible(true)
        l16th:setVisible(false)
        loffset:setVisible(false)
    else
        ltime:setVisible(false)
        l16th:setVisible(true)
        loffset:setVisible(true)
    end
end

function rsync(valueObject, value)
    if value == 0 then
        rtime:setVisible(true)
        rshowtime = true
        r16th:setVisible(false)
        roffset:setVisible(false)
    else
        rtime:setVisible(false)
        rshowtime = false
        r16th:setVisible(true)
        roffset:setVisible(true)
    end
end

function lrlink(valueObject, value)
    if value == 0 then
        rtime:setVisible(rshowtime)
        if rshowtime then
            r16th:setVisible(false)
            roffset:setVisible(false)
        else
            r16th:setVisible(true)
            roffset:setVisible(true)
        end
        rs:setVisible(true)
    else
        rtime:setVisible(false)
        r16th:setVisible(false)
        roffset:setVisible(false)
        rs:setVisible(false)
    end
end
