hpffreq = controls.get(8)

function hpf(valueObject, value)
    if value == 0 then
       hpffreq:setVisible(false)
    else
       hpffreq:setVisible(true)
    end
end



width = controls.get(14)
offset = controls.get(10)
shaping = controls.get(12)
feedback = controls.get(5)
feedbackinv = controls.get(4)
drywet = controls.get(3)

function mode(valueObject, value)
    if value < 2 then
        width:setVisible(true)
        offset:setVisible(false)
        shaping:setVisible(false)
        feedback:setVisible(true)
        feedbackinv:setVisible(true)
	drywet:setVisible(true)
    else
        width:setVisible(false)
        offset:setVisible(true)
        shaping:setVisible(true)
        feedback:setVisible(false)
        feedbackinv:setVisible(false)  
	drywet:setVisible(false)
    end
end
