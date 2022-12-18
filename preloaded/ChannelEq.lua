function formatMidFreq (valueObject, value)
   local table = {120, 155, 201, 261, 337, 437, 566, 733, 949, 1230, 1590, 2060, 2670, 3450, 4470, 5790, 7500}
   if value==16383
     then return("7.5 kHz")
   end
   local idx = math.floor(value / 1024)+1
   local alpha = (value % 1024) / 1024.0
   local beta = -0.1
   local show = table[idx] + (-beta * (alpha - 0.5) * (alpha - 0.5) + alpha + 0.25 * beta) * (table[idx+1] - table[idx]) 
   if show < 1000
       then return(string.format("%i Hz", math.floor(show) ))
       else return(string.format("%.2f kHz", show/1000 ))
    end
end
