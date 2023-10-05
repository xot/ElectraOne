ftype = 0
ctype1 = 0
ctype2 = 0


circuit1 = controls.get(7)
circuit2 = controls.get(6)
morph = controls.get(21)
drive = controls.get(2)

circuit2:setSlot(3,1)
drive:setSlot(10,1)


function setfiltervisibility ()
   circuit1:setVisible(ftype < 2)
   circuit2:setVisible(ftype > 1)
   morph:setVisible(ftype == 4)
   drive:setVisible( ((ftype == 2 or ftype == 3) and (ctype2 ~=0)) or ((ftype < 2) and (ctype1 ~= 0)))
end

function setftype (valueObject, value)
    ftype = value
    setfiltervisibility()
end

function setctype1 (valueObject, value)
    ctype1 = value
    setfiltervisibility()
end

function setctype2 (valueObject, value)
    ctype2 = value
    setfiltervisibility()
end

quantize = controls.get(15)

function qon (valueObject, value)
    quantize:setVisible(value ~=0)
end

scgain = controls.get(23)
scmix = controls.get(24)

function scon(valueObject, value)
    scgain:setVisible(value ~= 0)
    scmix:setVisible(value ~= 0)
end

syncison = false

lfofreq = controls.get(11)
lforate = controls.get(19)
lfooffset = controls.get(12)
lfostereomode = controls.get(17)

spinison = false

lfospin = controls.get(16)
lfophase = controls.get(13)

lforate:setSlot(11,1)
lfospin:setSlot(17,1)
lfooffset:setSlot(18,1)

function setlfovisibility()
  lfofreq:setVisible(not syncison)
  lforate:setVisible(syncison)
  lfooffset:setVisible(syncison)
  lfostereomode:setVisible(not syncison)
  lfospin:setVisible(spinison)
  lfophase:setVisible(syncison or (not spinison))
end

function sync (valueObject, value)
    syncison = (value ~= 0)
    setlfovisibility()
end

function stereomode (valueObject, value)
    spinison = (value ~= 0)
    setlfovisibility()
end
