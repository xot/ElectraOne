lforate = controls.get(24)
lfotime = controls.get(28)
lforatio = controls.get(25)
lfosynced = controls.get(27)

function lfomode(valueObject, value)
    if value == 0 then
        lforate:setVisible(true)
        lfotime:setVisible(false)
        lforatio:setVisible(false)
        lfosynced:setVisible(false)
    elseif value == 1 then
        lforate:setVisible(false)
        lfotime:setVisible(true)
        lforatio:setVisible(false)
        lfosynced:setVisible(false)
    elseif value == 2 then
        lforate:setVisible(false)
        lfotime:setVisible(false)
        lforatio:setVisible(true)
        lfosynced:setVisible(false)
    else
        lforate:setVisible(false)
        lfotime:setVisible(false)
        lforatio:setVisible(false)
        lfosynced:setVisible(true)
    end
end

envrate = controls.get(2)
envtime = controls.get(6)
envratio = controls.get(3)
envsynced = controls.get(4)

function envmode(valueObject, value)
    if value == 0 then
        envrate:setVisible(true)
        envtime:setVisible(false)
        envratio:setVisible(false)
        envsynced:setVisible(false)
    elseif value == 1 then
        envrate:setVisible(false)
        envtime:setVisible(true)
        envratio:setVisible(false)
        envsynced:setVisible(false)
    elseif value == 2 then
        envrate:setVisible(false)
        envtime:setVisible(false)
        envratio:setVisible(true)
        envsynced:setVisible(false)
    else
        envrate:setVisible(false)
        envtime:setVisible(false)
        envratio:setVisible(false)
        envsynced:setVisible(true)
    end
end
