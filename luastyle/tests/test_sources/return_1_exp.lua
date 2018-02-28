local nesting = function()
  return setmetatable({}, {
      __call = function(self, process)
        init(process)

        return setmetatable(self, {
            __index = function(self, key)
              return process.api[key]
            end,

            __newindex = function(self, key, value)
              error('Attempt to modify process')
            end
        })
      end
  })
end

return setmetatable({}, {
    __call = function(self, process)
      init(process)

      return setmetatable(self, {
          __index = function(self, key)
            return process.api[key]
          end,

          __newindex = function(self, key, value)
            error('Attempt to modify process')
          end
      })
    end
})
