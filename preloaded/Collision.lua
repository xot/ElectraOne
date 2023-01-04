rate1 = controls.get(19)
freq1 = controls.get(14)

rate2 = controls.get(33)
freq2 = controls.get(28)

function sync1(valueObject, value)
    if value == 0 then
        freq1:setVisible(true)
        rate1:setVisible(false)
        return("Free")
    else
        freq1:setVisible(false)
        rate1:setVisible(true)
        return("Sync")
    end
end

function sync2(valueObject, value)
    if value == 0 then
        freq2:setVisible(true)
        rate2:setVisible(false)
        return("Free")
    else
        freq2:setVisible(false)
        rate2:setVisible(true)
        return("Sync")
    end
end

material1 = controls.get(82)
inharmonics1 = controls.get(78)
radius1 = controls.get(93)
opening1 =  controls.get(87)


function type1(valueObject, value)
    if value < 5 then
        material1:setVisible(true)
        inharmonics1:setVisible(true)
        radius1:setVisible(false)
        opening1:setVisible(false)
    else
        material1:setVisible(false)
        inharmonics1:setVisible(false)
        radius1:setVisible(true)
        opening1:setVisible(true)
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

material2 = controls.get(113)
inharmonics2 = controls.get(109)
radius2 = controls.get(124)
opening2 =  controls.get(118)

function type2(valueObject, value)
    if value < 5 then
        material2:setVisible(true)
        inharmonics2:setVisible(true)
        radius2:setVisible(false)
        opening2:setVisible(false)
    else
        material2:setVisible(false)
        inharmonics2:setVisible(false)
        radius2:setVisible(true)
        opening2:setVisible(true)
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
