rate = controls.get(14)
echo = controls.get(7)
feedback = controls.get(8)

echo:setSlot(12,1)


function loopmode(valueObject, value)
    rate:setVisible(value==1)
    echo:setVisible(value==3)
    feedback:setVisible(value==3)    
end
