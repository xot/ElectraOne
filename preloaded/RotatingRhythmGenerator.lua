div1odd = controls.get(7)
div1even = controls.get(6)
offset1 = controls.get(39)
offset1euclid = controls.get(40)

div1odd:setSlot(13,1)
offset1euclid:setSlot(14,1)

function odds1(valueObject, value)
    div1odd:setVisible(value~=0)   
    div1even:setVisible(value==0)
end

function euclid1(valueObject, value)
    offset1:setVisible(value==0)   
    offset1euclid:setVisible(value~=0)  
end

div2odd = controls.get(9)
div2even = controls.get(8)
offset2 = controls.get(41)
offset2euclid = controls.get(42)

div2odd:setSlot(16,1)
offset2euclid:setSlot(17,1)

function odds2(valueObject, value)
    div2odd:setVisible(value~=0)   
    div2even:setVisible(value==0)
end

function euclid2(valueObject, value)
    offset2:setVisible(value==0)   
    offset2euclid:setVisible(value~=0)  
end


div3odd = controls.get(11)
div3even = controls.get(10)
offset3 = controls.get(43)
offset3euclid = controls.get(44)

div3odd:setSlot(13,2)
offset3euclid:setSlot(14,2)

function odds3(valueObject, value)
    div3odd:setVisible(value~=0)   
    div3even:setVisible(value==0)
end

function euclid3(valueObject, value)
    offset3:setVisible(value==0)   
    offset3euclid:setVisible(value~=0)  
end

div4odd = controls.get(13)
div4even = controls.get(12)
offset4 = controls.get(45)
offset4euclid = controls.get(46)

div4odd:setSlot(16,2)
offset4euclid:setSlot(17,2)

function odds4(valueObject, value)
    div4odd:setVisible(value~=0)   
    div4even:setVisible(value==0)
end

function euclid4(valueObject, value)
    offset4:setVisible(value==0)   
    offset4euclid:setVisible(value~=0)  
end

