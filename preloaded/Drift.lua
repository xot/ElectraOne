lforate = controls.get(24)
lfotime = controls.get(28)
lforatio = controls.get(25)
lfosynced = controls.get(27)

lfotime:setSlot(1,2)
lforatio:setSlot(1,2)
lfosynced:setSlot(1,2)

function lfomode(valueObject, value)
    lforate:setVisible(value == 0)
    lfotime:setVisible(value == 1) 
    lforatio:setVisible(value == 2)
    lfosynced:setVisible(value == 3)
end

env2rate = controls.get(2)
env2time = controls.get(6)
env2ratio = controls.get(3)
env2synced = controls.get(4)

env2time:setSlot(36,1)
env2ratio:setSlot(36,1)
env2synced:setSlot(36,1)

env2 = controls.get(78)
env2cycmode = controls.get(7)
env2tilt = controls.get(5)
env2hold = controls.get(1)

env2cycle = false
env2mode = 0

function env2setvisibility()
    env2rate:setVisible(env2mode == 0.0 and env2cyc)
    env2time:setVisible(env2mode == 1.0 and env2cyc)
    env2ratio:setVisible(env2mode == 2.0 and env2cyc)
    env2synced:setVisible(env2mode == 3.0 and env2cyc)
    env2:setVisible(not env2cyc)
    env2cycmode:setVisible(env2cyc)
    env2tilt:setVisible(env2cyc)
    env2hold:setVisible(env2cyc)
end

function setenv2mode(valueObject, value)
    env2mode = value
    env2setvisibility()
end

function setenv2cycle(valueObject, value)
    env2cyc = (value ~= 0.0)
    env2setvisibility()
end
