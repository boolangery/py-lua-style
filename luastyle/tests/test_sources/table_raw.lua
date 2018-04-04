local table = {
nested = {
days = {
      -- days
      monday = 1, -- first
      tuesday = 2, -- second
      saturday = 3
      -- third
      , sunday = 4,
      -- last
},
foo = 'bar',
},
non_nested = 42
    ,12
}
local inline_table = {'1', '2', '3', '4'}
local strange_table = {model = 'car',
speed = 42.56, limit = 48,
average = 12}

   process {
  {
    {
     [true] = false,
            ['true'] = 'false',
  [process()] = 42,
    }
    }
  }

     local foo = {
     356,
    [true] = false,
    ['true'] = 'false',
    [process()] = 42,
   foo = 1,
  }
