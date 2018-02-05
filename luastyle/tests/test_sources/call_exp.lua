print('Lorem ipsum dolor sit amet, consectetur' ..
  tostring(foo) + '.') --hello

process(
  -- process
  data_1, -- arg 1
  data_2, -- arg 2
  true, 26) -- a usefull function

process(
  data_1,
  data_2,
  true, 26
)
-- end of file

setmetatable(lapp, {
    __call = function(tbl,str,args) return lapp.process_options_string(str,args) end,
})

setmetatable(lapp, {
    __call = function(tbl,str,args) return lapp.process_options_string(str,args) end,
  }, 13654,
  'foo'
)

process {
  processor {
    type = 'numeric',
    result = function(data) print(data) end
  },
  input = {1, 2, 3, 4}
}
