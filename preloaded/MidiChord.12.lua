shift1 = controls.get(8)
shift2 = controls.get(10)
shift3 = controls.get(12)
shift4 = controls.get(14)
shift5 = controls.get(16)
shift6 = controls.get(18)

shiftsd1 = controls.get(9)
shiftsd2 = controls.get(11)
shiftsd3 = controls.get(13)
shiftsd4 = controls.get(15)
shiftsd5 = controls.get(17)
shiftsd6 = controls.get(19)

vel1 = controls.get(24)
vel2 = controls.get(25)
vel3 = controls.get(26)
vel4 = controls.get(27)
vel5 = controls.get(28)
vel6 = controls.get(29)

ch1 = controls.get(1)
ch2 = controls.get(2)
ch3 = controls.get(3)
ch4 = controls.get(4)
ch5 = controls.get(5)
ch6 = controls.get(6)

shiftsd1:setSlot(1,1)
shiftsd2:setSlot(2,1)
shiftsd3:setSlot(3,1)
shiftsd4:setSlot(4,1)
shiftsd5:setSlot(5,1)
shiftsd6:setSlot(6,1)

function songscale(valueObject, value)
    shift1:setVisible(value == 0)
    shift2:setVisible(value == 0)
    shift3:setVisible(value == 0)
    shift4:setVisible(value == 0)
    shift5:setVisible(value == 0)
    shift6:setVisible(value == 0)    
    shiftsd1:setVisible(value ~= 0)
    shiftsd2:setVisible(value ~= 0)
    shiftsd3:setVisible(value ~= 0)
    shiftsd4:setVisible(value ~= 0)
    shiftsd5:setVisible(value ~= 0)
    shiftsd6:setVisible(value ~= 0)        
end
