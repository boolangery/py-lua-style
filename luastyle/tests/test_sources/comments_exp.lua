--- convert this UTC date to local.
function Date:toLocal ()
  -- convert this UTC date to local.
  local ndate = Date(self) -- convert this UTC date to local.
  -- convert this UTC date to local.
  if self.utc then
    -- convert this UTC date to local.
    ndate.utc = false
    -- convert this UTC date to local.
    ndate:set(ndate.time)
    --~         ndate:add { sec = Date.tzone(self) }
  end
  -- convert this UTC date to local.
  return ndate
  -- convert this UTC date to local.
end
-- convert this UTC date to local.
