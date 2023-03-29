freq = controls.get(2)
rate = controls.get(12)

function sync(valueObject, value)
    if value == 0 then
        freq:setVisible(true)
        rate:setVisible(false)
    else
        freq:setVisible(false)
        rate:setVisible(true)
    end
end
