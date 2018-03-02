local table = {
nested = {
days = {
monday = 1,
tuesday = 2,
},
foo = 'bar',
},
non_nested = 42
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
