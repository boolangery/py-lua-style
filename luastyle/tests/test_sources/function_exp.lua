print "foo"
print "bar"

function MetaTable.__call (func, foo, bar, foo, log)

  local process = {};

  process.onUpdate(function(name)
  end)

  function process:start()
    return process:init();
  end

  return process;
end

function BehaviorEngine:init(protocolDirectory, behaviorDatabase)

  -- listen to protocol change:
  self._protDirectory.protocolAdded:addListener(
    function(name)
      -- on new protocol, listen to newNode event:
      local index
      index = self._protDirectory:protocol(name).client.onNewNode:addListener(
        function(rawNode)
          self:_onNewNode(rawNode)
        end
      )
      self._regListeners.onNewNode[name] = index
      -- on new protocol, listen to newState event:
      index = self._protDirectory:protocol(name).client.onNewState:addListener(
        function(rawState)
          self:_onNewState(rawState)
        end
      )
      self._regListeners.onNewState[name] = index
    end
  )

  -- listen to reader change:
  self._database.onReload:addListener(
    function()
      -- TODO: reload data in memory...
    end
  )

end

local function add(a, b)
  return a + b
end
