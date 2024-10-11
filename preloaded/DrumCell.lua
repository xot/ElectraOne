fxstretch = controls.get(35)
fxgrain = controls.get(17)

fxloopoff = controls.get(21)
fxlooplen = controls.get(20)
fxloopoff:setSlot(9,1)
fxlooplen:setSlot(10,1)

fxpeamt = controls.get(28)
fxpedecay = controls.get(29)
fxpeamt:setSlot(9,1)
fxpedecay:setSlot(10,1)

fxpuamt = controls.get(30)
fxpurel = controls.get(31)
fxpuamt:setSlot(9,1)
fxpurel:setSlot(10,1)

fxbirate = controls.get(2)
fxbidecay = controls.get(1)
fxbirate:setSlot(9,1)
fxbidecay:setSlot(10,1)

fxfmamt = controls.get(8)
fxfmfreq = controls.get(9)
fxfmamt:setSlot(9,1)
fxfmfreq:setSlot(10,1)

fxrmamt = controls.get(32)
fxrmfreq = controls.get(33)
fxrmamt:setSlot(9,1)
fxrmfreq:setSlot(10,1)

fxsubamt = controls.get(36)
fxsubfreq = controls.get(37)
fxsubamt:setSlot(9,1)
fxsubfreq:setSlot(10,1)

fxnamt = controls.get(25)
fxncol = controls.get(26)
fxnamt:setSlot(9,1)
fxncol:setSlot(10,1)

function dofxtype(valueObject, value)
    fxstretch:setVisible(value == 0)
    fxgrain:setVisible(value == 0)
    fxloopoff:setVisible(value == 1)
    fxlooplen:setVisible(value == 1)
    fxpeamt:setVisible(value == 2)
    fxpedecay:setVisible(value == 2)
    fxpuamt:setVisible(value == 3)
    fxpurel:setVisible(value == 3)
    fxbirate:setVisible(value == 4)
    fxbidecay:setVisible(value == 4)
    fxfmamt:setVisible(value == 5)
    fxfmfreq:setVisible(value == 5)
    fxrmamt:setVisible(value == 6)
    fxrmfreq:setVisible(value == 6)
    fxsubamt:setVisible(value == 7)
    fxsubfreq:setVisible(value == 7)
    fxnamt:setVisible(value == 8)
    fxncol:setVisible(value == 8)
end

filtres = controls.get(15)
filtgain = controls.get(13)

filtres:setSlot(17,1)

function dofiltertype(valueObject, value)
    filtres:setVisible(value ~= 3)
    filtgain:setVisible(value == 3)    
end
