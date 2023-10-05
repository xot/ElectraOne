time = controls.get(11)
beatswing = controls.get(2)
beatdelay = controls.get(1)

time:setSlot(1,1)

function sync(valueObject, value)
    if value == 0 then
        time:setVisible(true)
        beatswing:setVisible(false)
        beatdelay:setVisible(false)
    else
        time:setVisible(false)
        beatswing:setVisible(true)
        beatdelay:setVisible(true)
    end
end
