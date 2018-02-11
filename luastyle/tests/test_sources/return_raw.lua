function matching_tags()
  return a,
    b, c
end

function matching_tags()
  return function()
      print('toto')
    end,
    'foo'
end
