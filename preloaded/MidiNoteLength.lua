release = controls.get(5)
decay = controls.get(2)
keyscale = controls.get(1)

function mode(valueObject, value)
    if value == 0 then
        release:setVisible(false)
        decay:setVisible(false)
        keyscale:setVisible(false)   
    else
        release:setVisible(true)
        decay:setVisible(true)
        keyscale:setVisible(true)        
    end
end

timelength = controls.get(8)
synclength = controls.get(7)

function sync(valueObject, value)
    if value == 0 then
        timelength:setVisible(true)
        synclength:setVisible(false)
    else
        timelength:setVisible(false)
        synclength:setVisible(true)
    end
end
