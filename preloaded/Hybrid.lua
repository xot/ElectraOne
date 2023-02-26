delaytime = controls.get(36)
fbtime = controls.get(34)
delayrate = controls.get(32)
fbrate = controls.get(33)

function sync(valueObject, value)
    if value == 0 then
        delaytime:setVisible(true)
        fbtime:setVisible(true)
        delayrate:setVisible(false)
        fbrate:setVisible(false)
        return("Free")
    else
        delaytime:setVisible(false)
        fbtime:setVisible(false)
        delayrate:setVisible(true)
        fbrate:setVisible(true)
        return("Sync")
    end
end

modulation = controls.get(31) 
damping = controls.get(8) 
diffusion = controls.get(11)

dhbassx = controls.get(5)
dhbassmult = controls.get(6)
dhshape = controls.get(7) 

function dhvis(flag)
    modulation:setVisible(flag)
    damping:setVisible(flag)
    dhbassx:setVisible(flag)
    dhbassmult:setVisible(flag)    
    dhshape:setVisible(flag)
end

qzlow = controls.get(43)
qzdistance = controls.get(42)

function qzvis(flag)
    modulation:setVisible(flag)
    damping:setVisible(flag)
    diffusion:setVisible(flag)
    qzlow:setVisible(flag)    
    qzdistance:setVisible(flag)
end

shpitch = controls.get(46)
shshimmer = controls.get(47)

function shvis(flag)
    modulation:setVisible(flag)
    damping:setVisible(flag)
    diffusion:setVisible(flag)
    shpitch:setVisible(flag)    
    shshimmer:setVisible(flag)
end

tiwave = controls.get(52)
tiphase = controls.get(49)
titide = controls.get(51)
tirate = controls.get(50)

function tivis(flag)
    damping:setVisible(flag)
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

function prvis(flag)
    prsixth:setVisible(flag)    
    prseventh:setVisible(flag)
    prlow:setVisible(flag)    
    prhi:setVisible(flag)
    prx:setVisible(flag)    
end


function algotype(valueObject, value)
    if value == 0.0 then
	qzvis(false)
	shvis(false)
	tivis(false)
	prvis(false)
	dhvis(true)
    elseif value == 1.0 then
	dhvis(false)
	shvis(false)
	tivis(false)
	prvis(false)
	qzvis(true)
    elseif value == 2.0 then
	dhvis(false)
	qzvis(false)
	tivis(false)
	prvis(false)
	shvis(true)
    elseif value == 3.0 then
	dhvis(false)
	qzvis(false)
	shvis(false)
	prvis(false)
	tivis(true)
    else
	dhvis(false)
	qzvis(false)
	shvis(false)
	tivis(false)
	prvis(true)
    end
    if value == 0.0 then
        return("DarkHall")
    elseif value == 1.0 then
        return("Quartz")    
    elseif value == 2.0 then
        return("Shimmer")    
    elseif value == 3.0 then
        return("Tides")
    else
        return("Prism")
    end
end

