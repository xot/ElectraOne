width = controls.get(14)
offset = controls.get(10)
shaping = controls.get(12)
feedback = controls.get(5)
feedbackinv = controls.get(4)


function mode(valueObject, value)
    print(value)
    if value < 2 then
        width:setVisible(true)
        offset:setVisible(false)
        shaping:setVisible(false)
        feedback:setVisible(true)
        feedbackinv:setVisible(true)
    else
        width:setVisible(false)
        offset:setVisible(true)
        shaping:setVisible(true)
        feedback:setVisible(false)
        feedbackinv:setVisible(false)  
    end
end
