pfdial = controls.get(6)

function postfilter(valueObject, value)
    pfdial:setVisible(value ~= 0)
end
