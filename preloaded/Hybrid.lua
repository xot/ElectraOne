delaytime = controls.get(36)
fbtime = controls.get(34)
delayrate = controls.get(32)
fbrate = controls.get(33)

delayrate:setSlot(19,1)
fbrate:setSlot(21,1)

function sync(valueObject, value)
    delaytime:setVisible(value == 0)
    fbtime:setVisible(value == 0)
    delayrate:setVisible(value ~= 0)
    fbrate:setVisible(value ~= 0)
end

modulation = controls.get(31) 
damping = controls.get(8) 
diffusion = controls.get(11)

diffusion:setSlot(6,1)

dhbassx = controls.get(5)
dhbassmult = controls.get(6)
dhshape = controls.get(7)

dhbassx:setSlot(6,1)
dhbassmult:setSlot(12,1)
dhshape:setSlot(11,1)

function dhvis(flag)
    dhbassx:setVisible(flag)
    dhbassmult:setVisible(flag)    
    dhshape:setVisible(flag)
end

qzlow = controls.get(43)
qzdistance = controls.get(42)

qzlow:setSlot(11,1)
qzdistance:setSlot(12,1)

function qzvis(flag)
    qzlow:setVisible(flag)    
    qzdistance:setVisible(flag)
end

shpitch = controls.get(46)
shshimmer = controls.get(47)

shpitch:setSlot(11,1)
shshimmer:setSlot(12,1)

function shvis(flag)
    shpitch:setVisible(flag)    
    shshimmer:setVisible(flag)
end

tiwave = controls.get(52)
tiphase = controls.get(49)
titide = controls.get(51)
tirate = controls.get(50)

tiwave:setSlot(5,1)
tiphase:setSlot(6,1)
titide:setSlot(11,1)
tirate:setSlot(12,1)

function tivis(flag)
    tiwave:setVisible(flag)    
    tiphase:setVisible(flag)
    titide:setVisible(flag)    
    tirate:setVisible(flag)
end

prsixth = controls.get(40)
prseventh = controls.get(39)
prlow = controls.get(38)
prhi = controls.get(37)
prx = controls.get(41)

prsixth:setSlot(5,1)
prseventh:setSlot(6,1)
prlow:setSlot(10,1)
prhi:setSlot(11,1)
prx:setSlot(12,1)

function prvis(flag)
    prsixth:setVisible(flag)    
    prseventh:setVisible(flag)
    prlow:setVisible(flag)    
    prhi:setVisible(flag)
    prx:setVisible(flag)    
end

function algotype(valueObject, value)
    modulation:setVisible(value < 3)
    damping:setVisible(value < 4)
    diffusion:setVisible((value == 1) or (value == 2))
    dhvis(value == 0)
    qzvis(value == 1)
    shvis(value == 2)
    tivis(value == 3)
    prvis(value == 4)
end

