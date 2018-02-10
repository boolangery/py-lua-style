print(a, 15, c, d, 'foo')

local v, err = pcall(toto, args, process(a), "eee", 42)

local a = function(a, b, c, ...)
  return a, b, c
end

function _G:print(a, b, c)
end

_G:print('foo', {}, {1, 2, 3})
