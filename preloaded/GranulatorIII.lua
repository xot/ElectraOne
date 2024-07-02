lfofreq = controls.get(55)
lforatio = controls.get(58)
lfobeat = controls.get(54)

lforatio:setSlot(13,3)
lfobeat:setSlot(13,3)

function lfosync(valueObject, value)
    lfofreq:setVisible(value == 0)
    lforatio:setVisible(value == 2)
    lfobeat:setVisible(value == 1)
end
