function sync(valueObject, value)
    local control = valueObject:getControl()
    if value == 0 then
        control:setName("Time")
        control:setColor(0x1791E9)
    else
        control:setName("Sync")
        control:setColor(0xF15509)
    end
end
