tune = controls.get(37)
transpose = controls.get(36)

function midifreq(valueObject, value)
    if value == 0 then
        tune:setVisible(true)
        transpose:setVisible(false)
	    return("MIDI Freq on")
    else
        tune:setVisible(false)
        transpose:setVisible(true)
	    return("MIDI Freq off")
    end
end

lforate = controls.get(17)
lfofreq = controls.get(13)

function sync(valueObject, value)
    if value == 0 then
        lfofreq:setVisible(true)
        lforate:setVisible(false)
	return("Time")
    else
        lfofreq:setVisible(false)
        lforate:setVisible(true)
	return("Sync")
    end
end

phase = controls.get(29)
spin = controls.get(34)

function mod(valueObject, value)
    if value == 0 then
        phase:setVisible(true)
        spin:setVisible(false)
	return("Phase")
    else
        phase:setVisible(false)
        spin:setVisible(true)
	return("Spin")
    end
end

material = controls.get(22)
inharmonics = controls.get(10)
radius = controls.get(30)
opening =  controls.get(27)


function type(valueObject, value)
    if value < 5 then
        material:setVisible(true)
        inharmonics:setVisible(true)
        radius:setVisible(false)
        opening:setVisible(false)
    else
        material:setVisible(false)
        inharmonics:setVisible(false)
        radius:setVisible(true)
        opening:setVisible(true)
    end
    if value == 0 then
      return("Beam")
    elseif value == 1 then
      return("Marimba")
    elseif value == 2 then
      return("String")
    elseif value == 3 then
      return("Membrane")
    elseif value == 4 then
      return("Plate")
    elseif value == 5 then
      return("Pipe")
    else 
      return("Tube")
    end
end
