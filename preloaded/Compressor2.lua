ratio = controls.get(12)
xratio = controls.get(6)

function model(valueObject, value)
    if value == 0.0 then
        ratio:setVisible(true)
        xratio:setVisible(false)
    elseif value == 1.0 then
        ratio:setVisible(true)
        xratio:setVisible(false)
    else
        ratio:setVisible(false)
        xratio:setVisible(true)
    end
end

eqgain = controls.get(15)
eqq = controls.get(17)

function eqtype(valueObject, value)
    if value < 3 then
        eqgain:setVisible(true)
        eqq:setVisible(false)
    else
        eqgain:setVisible(false)
        eqq:setVisible(true)
    end
end
