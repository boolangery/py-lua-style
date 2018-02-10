local sorted_query = [[
  return function (t)
    local i = 0
    local v
    local ls = {}
    for i,v in ipairs(t) do
      if CONDITION then
        ls[#ls+1] = v
      end
    end
    table.sort(ls,function(v1,v2)
      return SORT_EXPR
    end)
    local n = #ls
    return function()
      i = i + 1
      v = ls[i]
      if i > n then return end
      return FIELDLIST
    end
  end
]]

--[[
  @api {get} /user/:id Request User information
  @apiName GetUser
  @apiGroup User

  @apiParam {Number} id Users unique ID.

  @apiSuccess {String} firstname Firstname of the User.
  @apiSuccess {String} lastname  Lastname of the User.
--]]
  function getUser(id)
    return _storage.users.findById(id)
end
