veretrig = controls.get(66)
veloop = controls.get(60)

veretrig:setSlot(12,3)

function vemode(valueObject, value)
    veretrig:setVisible((value > 1) and (value < 4))
    veloop:setVisible(value == 1)
end

feretrig = controls.get(21)
feloop = controls.get(14)

feretrig:setSlot(24,2)

function femode(valueObject, value)
    feretrig:setVisible((value > 1) and (value < 4))
    feloop:setVisible(value == 1)
end


fetype = 0
circuita = 0
circuitb = 0

circuitasel = controls.get(26)
circuitbsel = controls.get(27)
circuitbsel:setSlot(3,2)

fedrive = controls.get(28)
femorph = controls.get(30)
femorph:setSlot(8,2)

function fesettype(valueObject, value)
    fetype = value
    setvisibility()
end

function setcircuita(valueObject, value)
    circuita = value
    setvisibility()
end

function setcircuitb(valueObject, value)
    circuitb = value
    setvisibility()
end

function setvisibility()
    circuitasel:setVisible(fetype >1)
    circuitbsel:setVisible(fetype <2)
    fedrive:setVisible( ((fetype < 2) and (circuitb > 0)) or ((fetype > 1) and (fetype < 4) and (circuita > 0)) )
    femorph:setVisible(fetype==4)
end
