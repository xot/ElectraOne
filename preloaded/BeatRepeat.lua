function formatPitch (valueObject, value)
  if value == 0 then
    return ("0 st")
  else
    return (string.format("-%i st",value))
  end
end

