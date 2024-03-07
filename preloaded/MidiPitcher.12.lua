pitch = controls.get(4)
stepwidth = controls.get(7)

pitchscaledeg = controls.get(5)
stepwidthscaledeg = controls.get(8)

pitchscaledeg:setSlot(1,1)
stepwidthscaledeg:setSlot(7,1)

function songscale(valueObject, value)
    pitch:setVisible(value == 0)
    stepwidth:setVisible(value == 0)
    pitchscaledeg:setVisible(value ~= 0)
    stepwidthscaledeg:setVisible(value ~= 0)
end
