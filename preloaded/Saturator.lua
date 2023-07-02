drive = controls.get(14)
curve = controls.get(11)
depth = controls.get(13)
lin = controls.get(15)
damp = controls.get(12)
period = controls.get(16)

function curvetype(valueObject, value)
    if (value == 6) then
        drive:setVisible(true)
        curve:setVisible(true)
        depth:setVisible(true)
        lin:setVisible(true)
        damp:setVisible(true)
        period:setVisible(true)
    else
        drive:setVisible(false)
        curve:setVisible(false)
        depth:setVisible(false)
        lin:setVisible(false)
        damp:setVisible(false)
        period:setVisible(false)
    end
end
