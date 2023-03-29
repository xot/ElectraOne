eqgain = controls.get(10)
eqq = controls.get(12)

function eqtype(valueObject, value)
    if value < 3 then
        eqgain:setVisible(true)
        eqq:setVisible(false)
    else
        eqgain:setVisible(false)
        eqq:setVisible(true)
    end
end
