time = controls.get(11)
div = controls.get(10)
s16th = controls.get(12)


function mode(valueObject, value)
    if value == 0.0 then
        time:setVisible(true)
        div:setVisible(false)
        s16th:setVisible(false)
    elseif value == 1.0 then 
        time:setVisible(false)
        div:setVisible(true)
        s16th:setVisible(false)
    else
       time:setVisible(false)
        div:setVisible(false)
        s16th:setVisible(true)
    end
end
