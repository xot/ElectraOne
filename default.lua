info.setText("by www.xot.nl")

function defaultFormatter(valueObject, value)
    return("")
end

function formatSmallFloat (valueObject, value)
  return (string.format("%.3f",value/1000))
end

function formatFloat (valueObject, value)
  return (string.format("%.2f",value/100))
end

function formatLargeFloat (valueObject, value)
  return (string.format("%.1f",value/10))
end

function formatdB (valueObject, value)
  return (string.format("%.1f dB",value/10))
end

function formatFreq (valueObject, value)
  return (string.format("%.1f Hz",value/10))
end

function formatPan (valueObject, value)
  if value < 0 then
    return (string.format("%iL", -value))
  elseif value == 0 then
    return "C"
  else
    return (string.format("%iR", value))
  end
end

function formatPercent (valueObject, value)
  return (string.format("%.1f %%",value/10))
end

function fmtSemiIntPercent (valueObject, value)
  if (-100 < value) and (value < 100) then
    return (string.format("%.1f %%",value/10))  
  else
    return (string.format("%.0f %%",value/10))
  end
end

function formatIntPercent (valueObject, value)
  return (string.format("%.0f %%",value/10))
end

function formatDegree (valueObject, value)
  return (string.format("%i *",value))
end

function formatSemitone (valueObject, value)
  return (string.format("%i st",value))
end

function formatFineSemitone (valueObject, value)
  return (string.format("%.2f st",value/100))
end

function formatDetune (valueObject, value)
  return (string.format("%i ct",value))
end

-- start/stop display drawing

function aa()
  window.stop()
end

function zz()
  window.resume()
end

-- handling patch requests to switch between mixer/effect 

function patch.onRequest (device)
  print ("Patch Request pressed",device.id);
  if device.id == 1
    then print ("Sending patch request MIDI");
    	 midi.sendSysex(PORT_1, {0x00, 0x21, 0x45, 0x7E, 0x7E}) ;
	 print ("Sent patch request MIDI");	 
  end
end

