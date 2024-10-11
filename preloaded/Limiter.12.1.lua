gain = controls.get(4)
output = controls.get(9)

output:setSlot(1,1)

ceiling = controls.get(2)
threshold = controls.get(10)

threshold:setSlot(3,1)

lrlink = controls.get(13)
mslink = controls.get(12)

mslink:setSlot(4,1)

function dorouting(valueObject, value)
    lrlink:setVisible(value == 0)
    mslink:setVisible(value ~= 0)    
end

function domaximize(valueObject, value)
    gain:setVisible(value == 0)
    output:setVisible(value ~= 0)
    ceiling:setVisible(value == 0)
    threshold:setVisible(value ~= 0)
end
