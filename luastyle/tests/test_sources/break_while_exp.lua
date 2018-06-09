-- print the first non-empty line
repeat
  line = os.read()
until line ~= ""
local i = 1
while a[i] do
  print(a[i])
  i = i + 1
end
for i = 1, 3 do print(i) end     -- count from 1 to 3
