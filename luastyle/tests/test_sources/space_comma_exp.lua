print(a, 15, c, d, 'foo')

local v, err = pcall(toto, args, process(a), "eee", 42)

local a = function(a, b, c, ...)
end
