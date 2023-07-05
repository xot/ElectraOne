chrate = controls.get(3)
chamount = controls.get(1)

function chorus (valueObject, value)
    chrate:setVisible(value ~= 0)
    chamount:setVisible(value ~= 0)    
end

sprate = controls.get(15)
spamount = controls.get(13)

function spin (valueObject, value)
    sprate:setVisible(value ~= 0)
    spamount:setVisible(value ~= 0)   
end

hitype = controls.get(20)
hifreq = controls.get(18)
higain = controls.get(21)

function hifilter (valueObject, value)
    hitype:setVisible(value ~= 0)
    hifreq:setVisible(value ~= 0)
    higain:setVisible(value ~= 0)
end

lsfreq = controls.get(26)
lsgain = controls.get(27)

function lowshelf (valueObject, value)
    lsfreq:setVisible(value ~= 0)
    lsgain:setVisible(value ~= 0)    
end