lforate = controls.get(24)
lfotime = controls.get(28)
lforatio = controls.get(25)
lfosynced = controls.get(27)

lfotime:setSlot(1,2)
lforatio:setSlot(1,2)
lfosynced:setSlot(1,2)

function lfomode(valueObject, value)
    lforate:setVisible(value == 0)
    lfotime:setVisible(value == 1)
    lforatio:setVisible(value == 2)
    lfosynced:setVisible(value == 3)
end

envrate = controls.get(2)
envtime = controls.get(6)
envratio = controls.get(3)
envsynced = controls.get(4)

envtime:setSlot(36,1)
envratio:setSlot(36,1)
envsynced:setSlot(36,1)


function envmode(valueObject, value)
    print(value)
    envrate:setVisible(value == 0.0)
    envtime:setVisible(value == 1.0)
    envratio:setVisible(value == 2.0)
    envsynced:setVisible(value == 3.0)
end
