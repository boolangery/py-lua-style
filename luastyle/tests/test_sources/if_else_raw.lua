if op == "+" then
r = a + b
elseif op == "-" then
r = a - b
elseif op == "*" then
r = a*b
elseif op == "/" then
r = a/b
else
error("invalid operation")
end

if true then foo = 'bar' else foo = nil end

if true then
print('hello')
end

if true then
print('hello') end

if nested then
if nested then
if nested then print('ok Im nested') end
elseif foo then
local a = 42
end
end

      if foo then
   print(foo)
   if bar then
    print(bar)
          else
    print('error')
  end
        else
  print('error')
end

  if not parm then
    -- extra unnamed parameters are indexed starting at 1
  parm = iextra
   ps = { type = 'string' }
     parms[parm] = ps
  iextra = iextra + 1
  else
   ps = parms[parm]
 end
