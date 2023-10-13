fdrive = controls.get(17)
fmorph = controls.get(19)

fmorph:setSlot(17,1)

fcrctbp = controls.get(15)
fcrctlp = controls.get(16)

fcrctlp:setSlot(20,1)

function ftype(valueObject, value)
    fcrctlp:setVisible(value < 2)
    fcrctbp:setVisible(value > 1)    
    fdrive:setVisible(value ~= 4)
    fmorph:setVisible(value == 4)
end

-- lfo

lforate = controls.get(32)
lfofreq = controls.get(29)

lforate:setSlot(34,2)

function lfosync(valueObject, value)
    lfofreq:setVisible(value == 0)
    lforate:setVisible(value ~= 0)    
end