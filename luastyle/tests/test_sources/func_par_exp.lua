build(foo)
build(foo)
foo.build(foo)
foo:build(foo)
foo {}
bar ""
build(
  foo
)
a = function (foo) end

foo():next(
  -- resolved
  function(child_results)
    print(bar)
  end,
  -- rejected
  function()
    print(bar)
  end
)
