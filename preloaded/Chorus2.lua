hpffreq = controls.get(8)

function hpf(valueObject, value)
    hpffreq:setVisible(value ~= 0)
end

width = controls.get(14)
offset = controls.get(10)
shaping = controls.get(12)
feedback = controls.get(5)
feedbackinv = controls.get(4)
drywet = controls.get(3)

function mode(valueObject, value)
    width:setVisible(value < 2)
    offset:setVisible(value > 1)
    shaping:setVisible(value > 1)
    feedback:setVisible(value < 2)
    feedbackinv:setVisible(value < 2)
    drywet:setVisible(value < 2)
end
