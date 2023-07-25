info.setText("by www.xot.nl")

function defaultFormatter(valueObject, value)
    return("")
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

function aaa()
  window.stop()
end

function zzz()
  window.resume()
end

-- handling patch requests to switch between mixer/effect 

function patch.onRequest (device)
  print ("Patch Request pressed");
  if device.id == 1
    then midi.sendSysex(PORT_1, {0x00, 0x21, 0x45, 0x7E, 0x7E})
  end
end

-- handling forwarding mixer updates to second E1 (if attached)

function forward(f)
  cmdt = {0x00, 0x21, 0x45, 0x08, 0x0D}
  cmds = f .. "()"
  for i=1, string.len(cmds) do
    cmdt[i+5]= string.byte(cmds,i,i)
  end
  midi.sendSysex(PORT_1,cmdt)
end

function forward2(f,p1,p2)
  cmdt = {0x00, 0x21, 0x45, 0x08, 0x0D}
  cmds = f .. "(" .. p1 .. "," .. p2 .. ")"
  for i=1, string.len(cmds) do
    cmdt[i+5]= string.byte(cmds,i,i)
  end
  midi.sendSysex(PORT_1,cmdt)
end

function aa()
  forward('aa')
end

function zz()
  forward('zz')
end

function utl(idx,label)
  forward2('utl', tostring(idx), '"'..label..'"')
end

function ursl(idx,label)
  forward2('ursl', tostring(idx), '"'..label..'"')
end

function seqv(idx,flag)
  if flag then
    forward2('seqv',tostring(idx),'true')
  else
    forward2('seqv',tostring(idx),'false')
  end
end

function smv(tc,rc)
  forward2('smv', tostring(tc), tostring(rc))
end

