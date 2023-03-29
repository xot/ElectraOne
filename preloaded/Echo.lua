ltime = controls.get(25)
rtime = controls.get(44)
l16th = controls.get(20)
r16th = controls.get(39)
ldiv = controls.get(21)
rdiv = controls.get(40)
modrate = controls.get(32)
modfreq = controls.get(30)

lshow16th = false
rshow16th = false
lshowtime = false
rshowtime = false

function lsync(valueObject, value)
    if value == 0 then
        ltime:setVisible(true)
	lshowtime = true
        l16th:setVisible(false)
        ldiv:setVisible(false)
    else
        ltime:setVisible(false)
	lshowtime = false
        l16th:setVisible(lshow16th)
        ldiv:setVisible(not lshow16th)
    end
end

function rsync(valueObject, value)
    if value == 0 then
        rtime:setVisible(true)
	rshowtime = true
	r16th:setVisible(false)
        rdiv:setVisible(false)
    else
        rtime:setVisible(false)
	rshowtime = false
        r16th:setVisible(rshow16th)
        rdiv:setVisible(not rshow16th)
    end
end

function modsync(valueObject, value)
if value == 0 then
        modfreq:setVisible(true)
        modrate:setVisible(false)
    else
        modfreq:setVisible(false)
        modrate:setVisible(true)
    end
end

function lmode(valueObject, value)
    if value == 3.0 then
        lshow16th = true
    else
        lshow16th = false
    end
    if not lshowtime then
        l16th:setVisible(lshow16th)
        ldiv:setVisible(not lshow16th)
    end
end

function rmode(valueObject, value)
    if value == 3.0 then
        rshow16th = true
    else
        rshow16th = false
    end
    if not rshowtime then
        r16th:setVisible(rshow16th)
        rdiv:setVisible(not rshow16th)
    end
end
