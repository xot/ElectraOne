time = controls.get(11)
beatswing = controls.get(2)
beatdelay = controls.get(1)

function sync(valueObject, value)
    time:setVisible(value == 0)
    beatswing:setVisible(value ~= 0)
    beatdelay:setVisible(value ~= 0)
end