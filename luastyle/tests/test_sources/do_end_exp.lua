--- do program
--- @param test
do
  local a -- a local var
  -- comment
end
do local a end
do do do local b end end end
do
  -- local var
  local a
  do
    local b-- local var
    do
      local c = a + b
    end
  end
  -- end
end
