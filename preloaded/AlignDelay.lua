leftmeter = controls.get(8)
rightmeter = controls.get(13)

leftfeet= controls.get(7)
rightfeet = controls.get(12)

leftms = controls.get(9)
rightms = controls.get(14)

leftsmp = controls.get(2)
rightsmp = controls.get(3)

celcius = controls.get(1)
fahrenheit = controls.get(6)

leftfeet:setSlot(2,1)
rightfeet:setSlot(8,1)

leftms:setSlot(2,1)
rightms:setSlot(8,1)

leftsmp:setSlot(2,1)
rightsmp:setSlot(8,1)

distsel = controls.get(5)
tempsel = controls.get(15)

fahrenheit:setSlot(9,1)

mode = 0

function setmode(valueObject, value)
    mode = value
    setvisibility()
end

ismeter = true

function distunit(valueObject, value)
    ismeter = (value == 0)
    setvisibility()
end

iscelcius = true

function tempunit(valueObject, value)
    iscelcius = (value == 0)
    setvisibility()
end

notlinked =  true

function setlink(valueObject, value)
    notlinked = (value == 0)
    setvisibility()
end

function setvisibility()
    leftmeter:setVisible((mode == 2) and ismeter)
    rightmeter:setVisible((mode == 2) and ismeter and notlinked)
    leftfeet:setVisible((mode == 2) and not ismeter)
    rightfeet:setVisible((mode == 2) and not ismeter and notlinked)
    leftms:setVisible((mode == 0) and ismeter)
    rightms:setVisible((mode == 0) and ismeter and notlinked)
    leftsmp:setVisible((mode == 1))
    rightsmp:setVisible((mode == 1) and notlinked)
    celcius:setVisible((mode == 2) and iscelcius)
    fahrenheit:setVisible((mode == 2) and not iscelcius)
    tempsel:setVisible((mode == 2))
    distsel:setVisible((mode == 2))
end



