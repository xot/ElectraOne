ilter = controls.get(24)
ladder = controls.get(36)

ladder:setSlot(6,2)

function doladder(valueObject, value)
    filter:setVisible(value == 0)
    ladder:setVisible(value ~= 0)    
end

freq = controls.get(9)
note = controls.get(10)

freq:setSlot(3,2)

function carrmode(valueObject, value)
    freq:setVisible(value ~= 0)
    note:setVisible(value == 0)    
end

modfreq = controls.get(74)
modratio = controls.get(50)
modharm = controls.get(49)

modratio:setSlot(9,2)
modharm:setSlot(9,2)

function modmode(valueObject, value)
    modfreq:setVisible(value == 0)
    modratio:setVisible(value == 1)
    modharm:setVisible(value == 2)
end
