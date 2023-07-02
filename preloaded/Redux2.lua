pfdial = controls.get(6)

function postfilter(valueObject, value)
   if (value == 0) then
       pfdial:setVisible(false)
   else
       pfdial:setVisible(true)
   end
end
