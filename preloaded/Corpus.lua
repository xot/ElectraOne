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
