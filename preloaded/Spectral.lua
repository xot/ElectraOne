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
    if value == 0.0 then
        return("Time")
    elseif value == 1.0 then
        return("Notes")
    elseif value == 2.0 then
            return("16th")
    elseif value == 3.0 then
            return("16th Triplet")        
    else
        return("16th Dotted")
    end
end
