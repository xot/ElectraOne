div = controls.get(5)
div2 = controls.get(6)
ppqn = controls.get(8)

div2:setSlot(1,1)
ppqn:setSlot(1,1)

function dotype(valueObject, value)
    div:setVisible(value==0)
    div2:setVisible(value==1)
    ppqn:setVisible(value==2)
end
